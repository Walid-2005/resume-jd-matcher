"""
Resume section parser and evidence classifier.

Splits raw resume text into labelled sections (Experience, Skills, Education,
Projects, etc.) so downstream scoring can distinguish high-evidence skills
(shown in Experience/Projects — actually used) from low-evidence ones
(listed only in the Skills section — claimed, unverified).
"""
import re
from typing import Dict, List, Optional, Tuple


# ── Section-header patterns ─────────────────────────────────────────────────
# Keyed by canonical section label.  Values are regex alternatives matched
# against each line (case-insensitive, anchored to start-of-line).  Each line
# that matches a pattern becomes the boundary between two sections.
SECTION_PATTERNS: Dict[str, List[str]] = {
    'summary': [
        r'summary', r'professional\s+summary', r'career\s+summary',
        r'objective', r'career\s+objective', r'profile',
        r'about\s+me', r'about', r'personal\s+statement',
    ],
    'experience': [
        r'(?:work|professional|employment|career|relevant)\s+experience',
        r'experience', r'work\s+history', r'employment\s+history',
        r'professional\s+background', r'career\s+history',
    ],
    'projects': [
        r'projects?', r'(?:personal|key|select|notable|featured)\s+projects?',
        r'portfolio', r'side\s+projects?',
    ],
    'skills': [
        r'skills?', r'technical\s+skills?', r'core\s+(?:skills|competencies)',
        r'key\s+skills?', r'competencies',
        r'(?:tech|technology)\s+stack', r'technologies',
        r'tools?(?:\s+(?:and|&)\s+technologies)?',
        r'areas\s+of\s+expertise',
    ],
    'education': [
        r'education', r'academic', r'academics',
        r'qualifications?', r'academic\s+background',
        r'educational\s+(?:background|qualifications)',
    ],
    'certifications': [
        r'certifications?', r'licenses?',
        r'certifications?\s+(?:and|&)\s+(?:licenses?|courses?)',
        r'(?:professional\s+)?licenses?',
        r'courses?', r'online\s+courses?', r'training',
    ],
    'awards': [
        r'awards?', r'honors?', r'honours?',
        r'awards?\s+(?:and|&)\s+(?:honors|honours|recognitions?)',
        r'achievements?', r'accomplishments?',
    ],
    'publications': [
        r'publications?', r'papers?', r'research',
    ],
    'languages': [
        r'languages?(?:\s+spoken)?',
    ],
    'hobbies': [
        r'hobbies', r'interests?', r'activities',
        r'personal\s+interests', r'extracurriculars?',
    ],
    'contact': [
        r'contact(?:\s+(?:info|information|details))?',
        r'personal\s+(?:info|information|details)',
    ],
    'references': [
        r'references', r'referees',
    ],
    'volunteer': [
        r'volunteer(?:ing)?(?:\s+experience)?',
        r'community\s+(?:service|involvement)',
    ],
}


# Pre-compile a flat list of (canonical_section, pattern) so we only compile
# once at import time.  Header patterns are anchored and allow optional
# trailing colon / punctuation / decoration.
_COMPILED_HEADERS: List[Tuple[str, re.Pattern]] = []
for _section, _patterns in SECTION_PATTERNS.items():
    for _pat in _patterns:
        _COMPILED_HEADERS.append((
            _section,
            re.compile(
                # Optional leading bullet / decoration, the header keyword,
                # optional trailing decoration, then end-of-line.  We match
                # short standalone lines only (<= 6 words) to avoid matching
                # sentences like "my experience with Python has grown".
                r'^\s*(?:[•\-\*–·=\s]*)?' + _pat + r'\s*[:\-–—]?\s*$',
                re.IGNORECASE,
            ),
        ))


# Evidence-strength multiplier per section.  Higher = stronger evidence that
# the candidate actually has (vs merely claims) the skill.
SECTION_CONFIDENCE: Dict[str, float] = {
    'experience':     1.00,   # actually used on the job — strongest signal
    'projects':       0.95,   # built something with it
    'certifications': 0.85,   # formally validated
    'publications':   0.80,   # wrote about it at depth
    'volunteer':      0.80,   # applied in a real setting
    'awards':         0.75,
    'skills':         0.70,   # explicit claim, unverified
    'summary':        0.60,   # general claim
    'education':      0.50,   # coursework / theory only
    'languages':      0.50,
    'hobbies':        0.40,
    'references':     0.00,
    'contact':        0.00,
    'unclassified':   0.55,
}

# Sections that count as "evidence of use" (vs merely claimed)
EVIDENCE_SECTIONS = {'experience', 'projects', 'certifications',
                     'publications', 'volunteer', 'awards'}


def parse_resume_sections(text: str) -> Dict[str, str]:
    """Split a resume into labelled sections.

    The first run of lines before any recognised header is kept under
    ``'unclassified'`` (typically the name / contact block at the top).

    Args:
        text: Raw resume text.

    Returns:
        Dict mapping canonical section name → that section's body text.
        Only sections that actually appear in the resume are present.
    """
    if not text:
        return {}

    sections: Dict[str, List[str]] = {}
    current = 'unclassified'
    # A short header on its own line should NOT gobble content that follows
    # it if the following lines are clearly unrelated.  We simply accumulate
    # into the current section until the next header is found.

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            # Preserve paragraph breaks inside the current section
            sections.setdefault(current, []).append('')
            continue

        # Short lines only — avoid matching "experience with Python" inside
        # a prose paragraph.  Hard cap at 6 words to be safe.
        if len(stripped.split()) <= 6:
            matched_section: Optional[str] = None
            for section_name, pattern in _COMPILED_HEADERS:
                if pattern.match(stripped):
                    matched_section = section_name
                    break
            if matched_section is not None:
                current = matched_section
                continue

        sections.setdefault(current, []).append(stripped)

    # Join lines back into strings; drop empty sections
    return {
        name: '\n'.join(lines).strip()
        for name, lines in sections.items()
        if any(ln.strip() for ln in lines)
    }


def classify_skill_evidence(
    resume_text: str,
    skills: List[str],
    sections: Optional[Dict[str, str]] = None,
) -> Dict[str, Dict]:
    """For each skill, find the strongest section it appears in.

    A skill mentioned in Experience AND Skills is scored by the stronger
    section (Experience).  Case-insensitive word-boundary matching.

    Args:
        resume_text: Raw resume text (used as fallback when sections is None).
        skills:      Skills to classify (list of canonical skill strings).
        sections:    Pre-parsed sections dict.  If omitted, parsed from text.

    Returns:
        Dict keyed by lowercased skill, values:
            {
              'section':    canonical section name of strongest evidence,
              'confidence': float 0.0-1.0 (from SECTION_CONFIDENCE),
              'all_sections': list of every section it appears in,
              'has_evidence':  True if found in an EVIDENCE_SECTIONS section,
            }
        Skills not found anywhere in the resume are omitted.
    """
    if sections is None:
        sections = parse_resume_sections(resume_text or '')

    out: Dict[str, Dict] = {}
    for skill in skills:
        key = skill.lower().strip()
        if not key:
            continue
        pattern = re.compile(r'\b' + re.escape(key) + r'\b', re.IGNORECASE)
        matched_sections: List[Tuple[str, float]] = []
        for section_name, body in sections.items():
            if not body:
                continue
            if pattern.search(body):
                conf = SECTION_CONFIDENCE.get(section_name,
                                               SECTION_CONFIDENCE['unclassified'])
                matched_sections.append((section_name, conf))

        if not matched_sections:
            continue

        # Strongest-evidence section wins
        best = max(matched_sections, key=lambda x: x[1])
        out[key] = {
            'section':       best[0],
            'confidence':    best[1],
            'all_sections':  [s for s, _ in matched_sections],
            'has_evidence':  any(s in EVIDENCE_SECTIONS for s, _ in matched_sections),
        }
    return out


def compute_evidence_summary(evidence_map: Dict[str, Dict]) -> Dict:
    """Aggregate statistics over a per-skill evidence map.

    Used to drive a small score adjustment and strength/weakness messages.

    Returns:
        {
          'n_total':        count of skills with any evidence,
          'n_with_evidence':count whose strongest section is in EVIDENCE_SECTIONS,
          'coverage':       ratio of n_with_evidence / n_total  (0-1),
          'avg_confidence': mean confidence across all tracked skills,
          'claimed_only':   skills only in skills/summary (no Experience/Project),
          'well_evidenced': skills with strong (>= experience-tier) evidence,
        }
    """
    if not evidence_map:
        return {
            'n_total': 0, 'n_with_evidence': 0,
            'coverage': 0.0, 'avg_confidence': 0.0,
            'claimed_only': [], 'well_evidenced': [],
        }

    claimed_only: List[str] = []
    well_evidenced: List[str] = []
    conf_sum = 0.0
    n_evid = 0
    for skill, info in evidence_map.items():
        conf_sum += info['confidence']
        if info['has_evidence']:
            n_evid += 1
            if info['confidence'] >= SECTION_CONFIDENCE['projects']:
                well_evidenced.append(skill)
        else:
            claimed_only.append(skill)

    n_total = len(evidence_map)
    return {
        'n_total':        n_total,
        'n_with_evidence': n_evid,
        'coverage':       round(n_evid / n_total, 3) if n_total else 0.0,
        'avg_confidence': round(conf_sum / n_total, 3) if n_total else 0.0,
        'claimed_only':   claimed_only,
        'well_evidenced': well_evidenced,
    }


def evidence_score_delta(summary: Dict) -> float:
    """Convert an evidence summary into a small score adjustment in pp (-3..+3).

    Rationale — we want the delta to be *informative* without swamping the
    structural skill match.  Empirically good ranges:

      * coverage >= 0.70 and n_total >= 3  →  +2 pp  (well-evidenced resume)
      * coverage >= 0.50 and n_total >= 3  →  +1 pp
      * coverage >= 0.30 or n_total < 3    →   0 pp  (neutral)
      * coverage <  0.30 and n_total >= 5  →  -2 pp  (lots of skills, little evidence)
      * no skills traced to evidence       →  -1 pp  (all claims, no receipts)

    Capped by design so the overall rubric still trusts skill_match + semantic.
    """
    n = summary['n_total']
    cov = summary['coverage']
    if n == 0:
        return 0.0
    if n >= 3 and cov >= 0.70:
        return 2.0
    if n >= 3 and cov >= 0.50:
        return 1.0
    if n >= 5 and cov < 0.30:
        return -2.0
    if summary['n_with_evidence'] == 0 and n >= 3:
        return -1.0
    return 0.0
