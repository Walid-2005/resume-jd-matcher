"""
Feature extraction for the score calibrator.

Centralised so the **training** path (building X from synthetic pairs and
stored feedback) and the **inference** path (building x from a live
analysis) produce identical feature vectors.  If the two drift, the
calibrator's predictions become meaningless — this module is the single
source of truth.

Design principles:
  * Features are numeric only (sklearn wants floats).
  * Every feature is always present — None / missing keys fall back to a
    sensible default (0 for counts, False→0 for flags).
  * Adding a feature here requires retraining, but never silently breaks
    inference: unseen features at load time default to 0.
"""
from __future__ import annotations
from typing import Any, Dict, List


# Column order is part of the model's contract.  Do not reorder.  Append
# only.  If you change this list, bump FEATURE_VERSION and retrain.
FEATURE_NAMES: List[str] = [
    # Score components (the model sees the raw pieces, not just the total)
    'raw_score',
    'skill_match_score',
    'semantic_score',
    'experience_score',

    # Skill-match shape
    'n_job_skills',
    'n_matched',
    'n_missing',
    'n_partial',
    'match_ratio',          # n_matched / max(1, n_job_skills)

    # Tier breakdown (profile-only; 0 when no profile)
    'n_core_missing',
    'n_expected_missing',
    'n_advanced_missing',
    'n_preferred_missing',

    # Role / scoring context
    'has_role_profile',     # 0/1
    'role_level_num',       # junior=0, mid=1, senior=2
    'weights_tier_num',     # low=0, baseline=1, high=2

    # Evidence quality (from resume_sections)
    'evidence_coverage',
    'n_well_evidenced',
    'n_claimed_only',
    'avg_evidence_confidence',

    # Semantic recovery (cross-encoder rerank of missing skills)
    # How many JD skills were NOT caught by keyword/synonym match but WERE
    # recovered as paraphrase matches from resume prose.  Signals that the
    # rule-based matcher is under-counting — the calibrator can learn when
    # this indicates a strong candidate vs. a noisy false-positive.
    'n_semantic_recovered',
]

# Bump when FEATURE_NAMES changes.  Training writes this into the model
# metadata; predict() refuses to run if versions don't match.
FEATURE_VERSION = 2


_ROLE_LEVEL_MAP = {'junior': 0, 'entry': 0, 'mid': 1, 'senior': 2, 'lead': 2, 'staff': 2}
_WEIGHTS_TIER_MAP = {'low': 0, 'baseline': 1, 'high': 2}


def build_features(ctx: Dict[str, Any]) -> Dict[str, float]:
    """Build a fixed-shape feature dict from an analysis context.

    Args:
        ctx: Dict assembled at analysis time (see matcher.py) with keys:
             - match_results    (dict returned by MLMatcher)
             - evidence_summary (dict returned by compute_evidence_summary)
             - raw_score        (int, pre-calibration rule-based score)

        All keys are optional — missing pieces fall back to neutral defaults
        so inference never crashes on a partial context.

    Returns:
        Dict keyed by FEATURE_NAMES, values are floats.  Always the same
        shape and order as FEATURE_NAMES.
    """
    mr = ctx.get('match_results') or {}
    ev = ctx.get('evidence_summary') or {}

    # Score components
    raw_score        = float(ctx.get('raw_score', mr.get('total_score', 0.0)))
    skill_match      = float(mr.get('skill_match_score', 0.0))
    semantic_score   = float(mr.get('semantic_score', 0.0))
    experience_score = float(mr.get('experience_score', 0.0))

    # Skill shape
    job_skills    = mr.get('job_skills') or []
    matched       = mr.get('matched_skills') or []
    missing       = mr.get('missing_skills') or []
    partial       = mr.get('partial_skills') or []
    n_job_skills  = len(job_skills)
    n_matched     = len(matched)
    n_missing     = len(missing)
    n_partial     = len(partial)
    match_ratio   = n_matched / max(1, n_job_skills)

    # Tier breakdown
    n_core_missing     = len(mr.get('core_missing') or [])
    n_expected_missing = len(mr.get('expected_missing') or [])
    n_advanced_missing = len(mr.get('advanced_missing') or [])
    n_preferred_missing = len(mr.get('preferred_missing') or [])

    # Context
    has_profile      = 1.0 if mr.get('has_role_profile') else 0.0
    role_level_num   = float(_ROLE_LEVEL_MAP.get(
        str(mr.get('role_level', 'mid')).lower(), 1
    ))
    weights_tier_num = float(_WEIGHTS_TIER_MAP.get(
        str(mr.get('weights_tier', 'baseline')).lower(), 1
    ))

    # Evidence
    evidence_coverage       = float(ev.get('coverage', 0.0))
    n_well_evidenced        = float(len(ev.get('well_evidenced') or []))
    n_claimed_only          = float(len(ev.get('claimed_only') or []))
    avg_evidence_confidence = float(ev.get('avg_confidence', 0.0))

    # Semantic recovery (populated by matcher.py when the cross-encoder
    # finds paraphrase matches).  Safe default = 0 for legacy contexts.
    n_semantic_recovered = float(ctx.get('n_semantic_recovered', 0))

    return {
        'raw_score':               raw_score,
        'skill_match_score':       skill_match,
        'semantic_score':          semantic_score,
        'experience_score':        experience_score,
        'n_job_skills':            float(n_job_skills),
        'n_matched':               float(n_matched),
        'n_missing':               float(n_missing),
        'n_partial':               float(n_partial),
        'match_ratio':             match_ratio,
        'n_core_missing':          float(n_core_missing),
        'n_expected_missing':      float(n_expected_missing),
        'n_advanced_missing':      float(n_advanced_missing),
        'n_preferred_missing':     float(n_preferred_missing),
        'has_role_profile':        has_profile,
        'role_level_num':          role_level_num,
        'weights_tier_num':        weights_tier_num,
        'evidence_coverage':       evidence_coverage,
        'n_well_evidenced':        n_well_evidenced,
        'n_claimed_only':          n_claimed_only,
        'avg_evidence_confidence': avg_evidence_confidence,
        'n_semantic_recovered':    n_semantic_recovered,
    }


def features_to_vector(features: Dict[str, float]) -> List[float]:
    """Flatten a feature dict into a FEATURE_NAMES-ordered list.

    Missing keys default to 0.0 so older feedback rows (captured before a
    new feature was added) still produce valid training inputs.
    """
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]
