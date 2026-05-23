"""
Role profile inheritance.

Only ~50 roles have hand-curated tiered (core/expected/advanced) profiles in
``ROLE_SKILL_PROFILES``.  Another ~160 roles have a flat skill template in
``ROLE_SKILL_TEMPLATES`` but no tiered profile, which means scoring for those
roles falls back to treating every skill as equal-weight — a step down from
the tier-weighted scoring we do for profiled roles.

This module closes that gap via *inheritance*: each unprofiled role is
nominated a parent (the nearest profiled role), and the parent's
core / expected / advanced tiers are merged with the child's flat template
to produce a synthesised profile for the child.

The intent is breadth-of-coverage, not perfect accuracy — an inherited
profile is always a better scoring signal than no profile at all, as long
as the parent is well-chosen.  Roles with no reasonable parent (healthcare,
skilled trades, physical engineering disciplines) are deliberately NOT
mapped here — they keep the old flat-scoring behaviour.
"""
from __future__ import annotations
from typing import Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Parent-role nomination table.
#
#  Each entry maps an unprofiled role (key in ROLE_SKILL_TEMPLATES) to a
#  profiled parent role (key in ROLE_SKILL_PROFILES).  Parents are picked on
#  transferable-skill overlap, not surface-level title similarity.
#
#  If a role isn't in this table, get_inherited_profile() returns None and the
#  caller falls through to flat scoring, the same as pre-inheritance behaviour.
# ─────────────────────────────────────────────────────────────────────────────
ROLE_PARENT_MAP: Dict[str, str] = {

    # ── Software engineering (language-specific → software engineer) ────────
    'software developer':              'software engineer',
    'python developer':                'software engineer',
    'java developer':                  'software engineer',
    'c# developer':                    'software engineer',
    'dotnet developer':                'software engineer',
    'php developer':                   'software engineer',
    'oracle developer':                'software engineer',
    'sap developer':                   'software engineer',
    'mulesoft developer':              'software engineer',
    'microsoft dynamics developer':    'software engineer',
    'mainframe developer':             'software engineer',
    'programmer analyst':              'software engineer',
    'application engineer':            'software engineer',
    'embedded software engineer':      'software engineer',
    'software development manager':    'software engineer',
    'systems integration manager':     'software engineer',

    # ── Web stack specialisations ───────────────────────────────────────────
    'back end developer':              'backend developer',
    'api developer':                   'backend developer',
    'front end developer':             'frontend developer',
    'web developer':                   'full stack developer',

    # ── Emerging tech → ML engineer ─────────────────────────────────────────
    'ai developer':                    'machine learning engineer',
    'ai engineer':                     'machine learning engineer',
    'ai researcher':                   'machine learning engineer',
    'nlp engineer':                    'machine learning engineer',
    'computer vision engineer':        'machine learning engineer',
    'research scientist':              'machine learning engineer',
    'medical researcher':              'machine learning engineer',

    # ── Data ────────────────────────────────────────────────────────────────
    'big data engineer':               'data engineer',
    'etl developer':                   'data engineer',
    'data architect':                  'data engineer',
    'database administrator':          'data engineer',
    'analytics engineer':              'data engineer',
    'business intelligence analyst':   'data analyst',
    'sports analyst':                  'data analyst',
    'geographic information systems analyst': 'data analyst',

    # ── Niche devs that still share core dev skills ─────────────────────────
    'blockchain developer':            'backend developer',
    'internet of things developer':    'backend developer',
    'game developer':                  'software engineer',
    'game designer':                   'ui/ux designer',

    # ── Cloud / infra / security ────────────────────────────────────────────
    'cloud architect':                 'cloud engineer',
    'network security engineer':       'cybersecurity analyst',
    'it auditor':                      'cybersecurity analyst',

    # ── QA family ───────────────────────────────────────────────────────────
    'test automation engineer':        'qa engineer',
    'test developer':                  'qa engineer',
    'firmware test engineer':          'qa engineer',
    'software quality assurance analyst': 'qa engineer',
    'quality assurance manager':       'qa engineer',

    # ── IT / support ────────────────────────────────────────────────────────
    'it support':                      'it support specialist',
    'it engineer':                     'it support specialist',
    'it consultant':                   'it support specialist',
    'technical support engineer':      'it support specialist',
    'technical operations officer':    'it support specialist',
    'jira administrator':              'it support specialist',
    'system administrator':            'network engineer',

    # ── Architecture-of-systems ─────────────────────────────────────────────
    'information architect':           'software architect',
    'multimedia architect':            'software architect',

    # ── Executive / leadership → consultant profile ─────────────────────────
    'chief executive officer':         'management consultant',
    'chief operating officer':         'management consultant',
    'chief of staff':                  'management consultant',
    'vice president':                  'management consultant',
    'chief technology officer':        'software architect',
    'chief information officer':       'it manager',
    'chief financial officer':         'financial analyst',
    'chief marketing officer':         'marketing manager',

    # ── Finance ─────────────────────────────────────────────────────────────
    'tax accountant':                  'accountant',
    'auditor':                         'accountant',
    'treasury analyst':                'financial analyst',
    'credit analyst':                  'risk analyst',
    'equity research analyst':         'financial analyst',
    'financial planner':               'financial analyst',
    'insurance underwriter':           'risk analyst',
    'compliance officer':              'risk analyst',

    # ── Banking / relationship ──────────────────────────────────────────────
    'bank teller':                     'customer success manager',
    'banking center supervisor':       'operations manager',
    'business banking relationship manager': 'account manager',

    # ── Sales ───────────────────────────────────────────────────────────────
    'sales manager':                   'sales executive',
    'sales representative':            'sales executive',
    'account executive':               'sales executive',
    'sales engineer':                  'sales executive',
    'real estate agent':               'sales executive',
    'realtor':                         'sales executive',
    'property manager':                'account manager',

    # ── Customer-facing ─────────────────────────────────────────────────────
    'customer service representative': 'customer success manager',
    'call center manager':             'customer success manager',
    'receptionist':                    'customer success manager',
    'hotel front desk agent':          'customer success manager',
    'flight attendant':                'customer success manager',
    'travel agent':                    'customer success manager',
    'tour guide':                      'customer success manager',

    # ── Operations / supply chain ───────────────────────────────────────────
    'supply chain manager':            'supply chain analyst',
    'logistics coordinator':           'supply chain analyst',
    'procurement specialist':          'supply chain analyst',
    'inventory analyst':               'supply chain analyst',
    'inventory coordinator':           'supply chain analyst',
    'fleet manager':                   'supply chain analyst',
    'warehouse manager':               'operations manager',
    'restaurant manager':              'operations manager',
    'retail manager':                  'operations manager',
    'construction manager':            'operations manager',

    # ── HR / people ─────────────────────────────────────────────────────────
    'hr coordinator':                  'hr generalist',
    'career coach':                    'hr generalist',

    # ── Admin / office ──────────────────────────────────────────────────────
    'administrative assistant':        'customer success manager',
    'event planner':                   'marketing manager',

    # ── Marketing / content / creative ──────────────────────────────────────
    'content creator':                 'content writer',
    'content strategist':              'content writer',
    'editor':                          'content writer',
    'journalist':                      'content writer',
    'grant writer':                    'content writer',
    'translator':                      'content writer',
    'public relations specialist':     'marketing manager',
    'ecommerce manager':               'marketing manager',

    # ── Visual & media production ───────────────────────────────────────────
    'photographer':                    'video editor',
    'video producer':                  'video editor',
    'podcast producer':                'video editor',
    'music producer':                  'video editor',
    'animator':                        'video editor',
    'interior designer':               'ui/ux designer',
    'creative professional':           'graphic designer',

    # ── Legal ───────────────────────────────────────────────────────────────
    # No legal profile exists, but paralegals/attorneys share analytical +
    # documentation + stakeholder skills with business analysts.
    'corporate counsel':               'business analyst',
    'paralegal':                       'business analyst',
    'lawyer':                          'business analyst',
    'real estate attorney':            'business analyst',

    # ── Strategy / advisory ─────────────────────────────────────────────────
    'policy analyst':                  'management consultant',
    'sustainability consultant':       'management consultant',

    # ── Education / training ────────────────────────────────────────────────
    'teacher':                         'training manager',
    'university professor':            'training manager',
    'instructional designer':          'training manager',
    'clinical educator':               'training manager',
    'tutor':                           'training manager',
    'librarian':                       'training manager',
    'fitness coach':                   'training manager',

    # ── Healthcare / Clinical (→ registered nurse as canonical parent) ──────
    # All clinical roles share the same core: patient care, medical
    # terminology, compliance, attention to detail.  The child's flat
    # template overlays specialty skills (pharmacy, radiology, etc.) on top.
    'doctor':                          'registered nurse',
    'veterinarian':                    'registered nurse',
    'dental hygienist':                'registered nurse',
    'pharmacist':                      'registered nurse',
    'optometrist':                     'registered nurse',
    'radiologist':                     'registered nurse',
    'physiotherapist':                 'registered nurse',
    'physical therapist':              'registered nurse',
    'occupational therapist':          'registered nurse',
    'speech therapist':                'registered nurse',
    'dietitian':                       'registered nurse',
    'case manager':                    'registered nurse',
    'healthcare administrator':        'registered nurse',

    # ── Lab Science (→ chemist as canonical parent) ─────────────────────────
    'lab technician':                  'chemist',
    'environmental scientist':         'chemist',

    # ── Physical Engineering (→ mechanical engineer as canonical parent) ────
    # CAD, project delivery, quality control, and problem-solving are shared.
    # Child templates layer on discipline-specific skills (PLC, drafting,
    # MATLAB, GIS, etc.).
    'biomedical engineer':             'mechanical engineer',
    'electrical engineer':             'mechanical engineer',
    'civil engineer':                  'mechanical engineer',
    'agricultural engineer':           'mechanical engineer',
    'automotive engineer':             'mechanical engineer',
    'computer hardware engineer':      'mechanical engineer',
    'architect':                       'mechanical engineer',
    'urban planner':                   'mechanical engineer',

    # ── Skilled Trades (→ electrician as canonical parent) ──────────────────
    # Shared core: hands-on problem solving, safety, customer work.
    'plumber':                         'electrician',
    'welder':                          'electrician',
    'hvac technician':                 'electrician',

    # ── Hospitality / Service (operations + customer-facing) ────────────────
    'chef':                            'operations manager',
    'barista':                         'customer success manager',
    'security guard':                  'operations manager',

    # ── Wellness / Social Services ──────────────────────────────────────────
    # Social work shares documentation, case handling, and stakeholder skills
    # with HR.  Fitness/wellness roles share instructional and program-design
    # skills with training managers.
    'social worker':                   'hr generalist',
    'health and fitness professional': 'training manager',
}


# How many of the child's flat-template skills should be promoted to core.
# The top of a Kaggle-derived template tends to be the most role-identifying
# skills, so a small head-slice makes a good "core" candidate set.
_CHILD_CORE_PROMOTION_COUNT = 5


def build_inherited_profile(
    child_role: str,
    parent_profile: Dict[str, list],
    child_template: list,
) -> Dict[str, list]:
    """Synthesise a tiered profile for ``child_role`` from its parent + template.

    Algorithm:
      1. Start with a deep copy of the parent's core / expected / advanced.
      2. Take the first ``_CHILD_CORE_PROMOTION_COUNT`` skills from the child's
         flat template.  Any of these that aren't already in *any* parent tier
         are inserted into ``core`` — they are the role-defining skills.
      3. Remaining child-template skills that aren't in any tier are merged
         into ``expected`` (we don't have enough signal to call them advanced).
      4. Deduplicate while preserving order within each tier.

    This keeps the parent's tiering discipline (so scoring still knows which
    skills are must-haves vs bonus) while letting the child's specifics drive
    differentiation.
    """
    core     = list(parent_profile.get('core', []))
    expected = list(parent_profile.get('expected', []))
    advanced = list(parent_profile.get('advanced', []))

    existing_lower = {s.lower() for s in core + expected + advanced}

    # 1. Promote top-of-template skills into core.
    for skill in child_template[:_CHILD_CORE_PROMOTION_COUNT]:
        if skill.lower() not in existing_lower:
            core.append(skill)
            existing_lower.add(skill.lower())

    # 2. Remaining child-template skills → expected.
    for skill in child_template[_CHILD_CORE_PROMOTION_COUNT:]:
        if skill.lower() not in existing_lower:
            expected.append(skill)
            existing_lower.add(skill.lower())

    return {
        'core':     core,
        'expected': expected,
        'advanced': advanced,
    }


def get_inherited_profile(
    role_key: str,
    role_skill_templates: Dict[str, list],
    role_skill_profiles: Dict[str, Dict[str, list]],
) -> Optional[Dict[str, list]]:
    """Return a synthesised profile for ``role_key``, or None if no parent.

    Args:
        role_key:            The detected role (lowercase key into
                             ``role_skill_templates``).
        role_skill_templates: Flat per-role skill lists.
        role_skill_profiles:  Hand-curated tiered profiles (parents).

    Returns:
        A ``{'core', 'expected', 'advanced'}`` dict, or None when:
          * the role has no entry in ``ROLE_PARENT_MAP`` (no confident parent),
          * the role is already in ``role_skill_profiles`` (parent itself),
          * the nominated parent is missing (data integrity issue).
    """
    if not role_key:
        return None
    if role_key in role_skill_profiles:
        return None   # caller should prefer the real profile

    parent_key = ROLE_PARENT_MAP.get(role_key)
    if parent_key is None:
        return None
    parent_profile = role_skill_profiles.get(parent_key)
    if parent_profile is None:
        return None

    child_template = role_skill_templates.get(role_key, [])
    return build_inherited_profile(role_key, parent_profile, child_template)


def inheritance_stats(
    role_skill_templates: Dict[str, list],
    role_skill_profiles: Dict[str, Dict[str, list]],
) -> Dict[str, int]:
    """Diagnostic counts for the inheritance table.

    Useful for smoke tests and for tracking coverage gains over time.
    """
    templated   = set(role_skill_templates.keys())
    profiled    = set(role_skill_profiles.keys())
    unprofiled  = templated - profiled
    inheritable = {r for r in unprofiled if r in ROLE_PARENT_MAP}
    orphan      = unprofiled - inheritable
    return {
        'templated':       len(templated),
        'profiled':        len(profiled),
        'unprofiled':      len(unprofiled),
        'inheritable':     len(inheritable),
        'orphan':          len(orphan),
        'coverage_before': round(len(profiled) / len(templated), 3) if templated else 0.0,
        'coverage_after':  round((len(profiled) + len(inheritable)) / len(templated), 3) if templated else 0.0,
    }
