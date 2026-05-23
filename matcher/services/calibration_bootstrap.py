"""
Synthetic training-data generator for the score calibrator.

Cold-start problem: the calibrator needs training rows, but there's no
user feedback on day one.  Waiting for real feedback would leave the
model permanently untrained for a student-project deployment.

Solution: for each of the ~180 profiled roles, construct three resume
variants with KNOWN ground-truth target scores, pair each against a
role-matched JD, and label the pair.  Feed them through the live scoring
pipeline to collect feature vectors, then train the calibrator to close
the gap between rule-based scores and the synthetic ground truth.

Variants (and the target score each is assigned):

  STRONG (target=85)
    - All core skills + most expected skills present
    - Experience bullets explicitly demonstrate them (evidence = high)
    - Role level matches the JD (e.g., "Senior Python Engineer" resume
      for a senior-level JD)

  PARTIAL (target=55)
    - Roughly half the core skills present
    - No experience bullets (Skills section only → evidence = low)
    - Missing advanced tier entirely

  MISMATCH (target=20)
    - Resume is from a DIFFERENT role family altogether
    - No core-skill overlap by design

These targets reflect what a recruiter would reasonably grade each pair
at a glance.  They're coarse (integers to the nearest 5) — the calibrator
learns a correction signal, not a precise regression to these exact
numbers.
"""
from __future__ import annotations
import random
from typing import Dict, List, Tuple


# Ground-truth target scores by variant.  These are the labels the
# calibrator is trained to close toward.
VARIANT_TARGET_SCORE: Dict[str, int] = {
    'strong':   85,
    'partial':  55,
    'mismatch': 20,
}

# A pool of "mismatch donor" roles — when building a mismatch resume for
# role X, we pick a random role from this list whose skills have minimal
# overlap with X.  Chosen to span unrelated domains so no matter what
# role we're pairing against, one of these is going to be a clean
# mismatch.
_MISMATCH_DONORS: List[str] = [
    'accountant', 'chef', 'registered nurse', 'graphic designer',
    'marketing manager', 'hr generalist', 'sales executive',
    'mechanical engineer', 'lawyer', 'translator',
]


def _profile_or_template(role: str, profiles: dict, templates: dict) -> Dict[str, list]:
    """Return a unified {core, expected, advanced} dict for any role.

    Profiled roles return their tiered profile.  Template-only roles (not
    in ROLE_SKILL_PROFILES) use their flat template: the first 5 skills
    become core, the rest become expected, advanced stays empty.  This
    keeps the bootstrap generator working across the full ~208 roles.
    """
    if role in profiles:
        return profiles[role]
    tpl = templates.get(role, [])
    return {
        'core':     list(tpl[:5]),
        'expected': list(tpl[5:]),
        'advanced': [],
    }


def _build_strong_resume(role: str, profile: Dict[str, list]) -> str:
    """Compose a resume that should score high against the role's JD."""
    core     = profile.get('core', [])
    expected = profile.get('expected', [])

    # Experience bullets that explicitly mention the skills (so the
    # section parser classifies them as 'evidence' → confidence = 1.0).
    bullets: list[str] = []
    for skill in core[:4]:
        bullets.append(f"- Used {skill} daily to deliver production features")
    for skill in expected[:3]:
        bullets.append(f"- Applied {skill} across multiple team projects")

    all_skills = list(dict.fromkeys(core + expected[:5]))

    return (
        f"Alex Candidate\n\n"
        f"PROFESSIONAL SUMMARY\n"
        f"Experienced {role} with 4+ years delivering impact.\n\n"
        f"EXPERIENCE\n"
        f"Senior {role.title()} — Acme Corp (2021-Present)\n"
        + "\n".join(bullets) + "\n\n"
        f"PROJECTS\n"
        f"- Built an end-to-end system using {', '.join(core[:3])}\n\n"
        f"SKILLS\n{', '.join(all_skills)}\n\n"
        f"EDUCATION\n"
        f"BSc Computer Science — State University\n"
    )


def _build_partial_resume(role: str, profile: Dict[str, list]) -> str:
    """Resume with roughly half the core skills and no experience evidence."""
    core = profile.get('core', [])
    kept = core[:max(1, len(core) // 2)]   # keep half the core, round up

    return (
        f"Sam Applicant\n\n"
        f"SUMMARY\n"
        f"Looking for {role} opportunity.\n\n"
        f"SKILLS\n{', '.join(kept)}\n\n"
        f"EDUCATION\n"
        f"BSc — Local College\n\n"
        f"EXPERIENCE\n"
        f"Retail Associate — Local Store (2020-2022)\n"
        f"- Customer service and daily operations\n"
    )


def _build_mismatch_resume(donor_role: str, donor_profile: Dict[str, list]) -> str:
    """Resume from a totally unrelated role — should score very low."""
    core     = donor_profile.get('core', [])
    expected = donor_profile.get('expected', [])
    all_skills = list(dict.fromkeys(core + expected[:3]))

    return (
        f"Jordan Unrelated\n\n"
        f"EXPERIENCE\n"
        f"{donor_role.title()} — Some Company (2020-Present)\n"
        f"- Performed core {donor_role} duties using {', '.join(core[:3])}\n\n"
        f"SKILLS\n{', '.join(all_skills)}\n\n"
        f"EDUCATION\n"
        f"Relevant degree for {donor_role}\n"
    )


def _build_jd(role: str, profile: Dict[str, list]) -> str:
    """Template a JD for the target role using its profile tiers."""
    core     = profile.get('core', [])
    expected = profile.get('expected', [])
    advanced = profile.get('advanced', [])

    required_bullets  = "\n".join(f"- {s}" for s in core + expected[:4])
    preferred_bullets = "\n".join(f"- {s}" for s in advanced[:5] or expected[4:7])

    return (
        f"We are hiring a {role.title()}.\n\n"
        f"Required:\n{required_bullets}\n\n"
        + (f"Preferred:\n{preferred_bullets}\n" if preferred_bullets else "")
    )


def _pick_mismatch_donor(target_role: str, profiles: dict, templates: dict) -> Tuple[str, Dict[str, list]]:
    """Pick a donor role whose core skills don't overlap with target's."""
    target_core = set(
        s.lower() for s in
        _profile_or_template(target_role, profiles, templates).get('core', [])
    )
    # Try donors in order, return the first with zero core overlap.
    for donor in _MISMATCH_DONORS:
        donor_prof = _profile_or_template(donor, profiles, templates)
        donor_core = set(s.lower() for s in donor_prof.get('core', []))
        if not (target_core & donor_core):
            return donor, donor_prof
    # Fallback: use the first donor anyway.
    return _MISMATCH_DONORS[0], _profile_or_template(_MISMATCH_DONORS[0], profiles, templates)


def generate_bootstrap_pairs(
    role_limit: int | None = None,
    seed: int = 42,
) -> List[Dict]:
    """Generate synthetic (resume, jd, target_score, variant, role) pairs.

    Args:
        role_limit: If set, only generate pairs for the first N roles
                    (useful for quick dev iteration).
        seed:       RNG seed for reproducibility.

    Returns:
        List of dicts with keys:
          - role          (str)
          - variant       ('strong' | 'partial' | 'mismatch')
          - target_score  (int)
          - resume_text   (str)
          - jd_text       (str)
    """
    from .ml_matcher import ROLE_SKILL_TEMPLATES
    from .trained_skills import ROLE_SKILL_PROFILES

    rng = random.Random(seed)
    del rng  # reserved for future jitter; kept for reproducibility hook

    roles = sorted(set(ROLE_SKILL_PROFILES.keys()) | set(ROLE_SKILL_TEMPLATES.keys()))
    if role_limit is not None:
        roles = roles[:role_limit]

    pairs: List[Dict] = []
    for role in roles:
        profile = _profile_or_template(role, ROLE_SKILL_PROFILES, ROLE_SKILL_TEMPLATES)
        core = profile.get('core', [])
        if not core:
            continue   # skip roles with no usable skill list

        jd = _build_jd(role, profile)

        # 1. STRONG match
        pairs.append({
            'role':         role,
            'variant':      'strong',
            'target_score': VARIANT_TARGET_SCORE['strong'],
            'resume_text':  _build_strong_resume(role, profile),
            'jd_text':      jd,
        })

        # 2. PARTIAL match
        pairs.append({
            'role':         role,
            'variant':      'partial',
            'target_score': VARIANT_TARGET_SCORE['partial'],
            'resume_text':  _build_partial_resume(role, profile),
            'jd_text':      jd,
        })

        # 3. MISMATCH (donor from a different domain)
        donor, donor_prof = _pick_mismatch_donor(
            role, ROLE_SKILL_PROFILES, ROLE_SKILL_TEMPLATES,
        )
        pairs.append({
            'role':         role,
            'variant':      'mismatch',
            'target_score': VARIANT_TARGET_SCORE['mismatch'],
            'resume_text':  _build_mismatch_resume(donor, donor_prof),
            'jd_text':      jd,
        })

    return pairs
