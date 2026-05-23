"""
Score calibrator — learned correction on top of the rule-based score.

Architecture
------------
The rule-based scoring pipeline (skill-match + semantic + experience +
tier calibration + evidence delta) produces a strong prior score.  The
calibrator is a thin regression layer that learns a CORRECTION DELTA in
percentage points, trained on:

  1. Synthetic bootstrap pairs (weight 1) — generated from role profiles
     with known ground-truth target scores.  Covers cold start.
  2. Real user feedback (weight 3) — AnalysisFeedback rows where the
     user rated the score as too_high / accurate / too_low.  Gradually
     corrects systematic biases the synthetic data can't see.

At inference the calibrator's output is CAPPED at ±MAX_CORRECTION_PP so
a noisy or poorly-trained model can never swamp the rule-based score.

Fail-soft everywhere: missing model file → 0 correction.  Broken pickle
→ 0 correction.  Mismatched feature version → 0 correction.  Analysis
continues regardless.
"""
from __future__ import annotations

import logging
import os
import pickle
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .calibration_features import (
    FEATURE_NAMES, FEATURE_VERSION, build_features, features_to_vector,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────────────────────────────────────

# Where the trained model lives.  Committed to git so the deployed app
# starts with a trained calibrator out-of-the-box.
MODEL_DIR = Path(__file__).parent.parent / 'trained_data'
MODEL_PATH = MODEL_DIR / 'score_calibrator.pkl'

# Minimum combined (synthetic + real) rows required before we'll train.
# Smaller than this and the model is just noise.
MIN_TRAIN_SIZE = 30

# Hard cap on how much the calibrator can move a score, in percentage
# points.  Protects against bad training runs swamping the rule-based
# logic that we trust a lot more.
MAX_CORRECTION_PP = 5.0

# Sample weighting: real feedback carries more signal than synthetic,
# since real users are the ground truth we actually care about.
_SAMPLE_WEIGHT_SYNTHETIC = 1.0
_SAMPLE_WEIGHT_REAL      = 3.0

# Feedback → target-correction mapping.  A user who says the score is
# "too high" wants it pulled down by this many points; "too low" pushed
# up; "accurate" means the rule-based score is already right.
_FEEDBACK_TARGET_CORRECTION = {
    'too_high': -10.0,
    'accurate':   0.0,
    'too_low':  +10.0,
}


# ─────────────────────────────────────────────────────────────────────────────
#  Metadata — shipped inside the pickle so we can reason about the model
#  at load time (feature version, training stats, freshness).
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CalibratorMeta:
    feature_version: int
    feature_names:   List[str]
    trained_at:      str
    n_train:         int
    n_synthetic:     int
    n_real:          int
    mae_train:       float
    mae_holdout:     float
    r2_holdout:      float
    model_type:      str
    notes:           Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
#  Calibrator
# ─────────────────────────────────────────────────────────────────────────────

class ScoreCalibrator:
    """Singleton-ish wrapper around a sklearn regressor + its metadata."""

    _instance: Optional['ScoreCalibrator'] = None

    def __init__(self):
        self._model = None
        self._meta: Optional[CalibratorMeta] = None
        self._loaded_from: Optional[float] = None   # file mtime at load time
        self._load_if_available()

    @classmethod
    def instance(cls) -> 'ScoreCalibrator':
        """Process-wide singleton.  Reloads transparently when the file
        on disk is newer than what we have in memory."""
        if cls._instance is None:
            cls._instance = cls()
        else:
            cls._instance._reload_if_stale()
        return cls._instance

    # ── Persistence ─────────────────────────────────────────────────────
    def _load_if_available(self) -> None:
        if not MODEL_PATH.exists():
            return
        try:
            with open(MODEL_PATH, 'rb') as f:
                payload = pickle.load(f)
            meta = CalibratorMeta(**payload['meta'])
            if meta.feature_version != FEATURE_VERSION:
                logger.warning(
                    "score_calibrator: feature version mismatch "
                    "(model=%d, code=%d) — ignoring trained model",
                    meta.feature_version, FEATURE_VERSION,
                )
                return
            self._model = payload['model']
            self._meta = meta
            self._loaded_from = MODEL_PATH.stat().st_mtime
            logger.info(
                "score_calibrator: loaded model (n_train=%d, mae_holdout=%.2f)",
                meta.n_train, meta.mae_holdout,
            )
        except Exception as e:
            logger.warning("score_calibrator: failed to load model: %s", e)
            self._model = None
            self._meta = None

    def _reload_if_stale(self) -> None:
        if not MODEL_PATH.exists():
            return
        mtime = MODEL_PATH.stat().st_mtime
        if self._loaded_from is None or mtime > self._loaded_from:
            self._load_if_available()

    def _save(self, model, meta: CalibratorMeta) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump({'model': model, 'meta': asdict(meta)}, f)

    # ── Inference ───────────────────────────────────────────────────────
    def predict(self, ctx: Dict[str, Any]) -> float:
        """Return the correction delta in percentage points.

        Returns 0.0 when:
          - No trained model is available
          - The feature vector can't be built
          - Anything at all goes wrong (fail-soft)

        Output is always clipped to [-MAX_CORRECTION_PP, +MAX_CORRECTION_PP].
        """
        if self._model is None:
            return 0.0
        try:
            x = features_to_vector(build_features(ctx))
            delta = float(self._model.predict([x])[0])
            if delta > MAX_CORRECTION_PP:
                delta = MAX_CORRECTION_PP
            elif delta < -MAX_CORRECTION_PP:
                delta = -MAX_CORRECTION_PP
            return delta
        except Exception as e:
            logger.warning("score_calibrator: predict failed: %s", e)
            return 0.0

    # ── Training ────────────────────────────────────────────────────────
    def train(
        self,
        synthetic_rows: List[Dict[str, Any]],
        real_rows: List[Dict[str, Any]],
    ) -> CalibratorMeta:
        """Fit a fresh model from labeled rows and persist it.

        Row format (both kinds):
          {
            'features':   Dict[str, float],   # output of build_features()
            'target':     float,              # correction delta in pp
            'source':     'synthetic' | 'real',
          }

        Real rows additionally should already have ``target`` derived from
        the user's score_rating via ``_FEEDBACK_TARGET_CORRECTION``.

        Returns:
            CalibratorMeta with training statistics.

        Raises:
            ValueError if fewer than MIN_TRAIN_SIZE combined rows.
        """
        n_synth = len(synthetic_rows)
        n_real  = len(real_rows)
        n_total = n_synth + n_real
        if n_total < MIN_TRAIN_SIZE:
            raise ValueError(
                f"Not enough training rows: {n_total} < {MIN_TRAIN_SIZE}. "
                f"Generate more bootstrap pairs or collect more feedback."
            )

        # Heavy imports local to training so inference never pays for them.
        import numpy as np
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.metrics import mean_absolute_error, r2_score
        from sklearn.model_selection import train_test_split

        all_rows = synthetic_rows + real_rows
        X = np.array([features_to_vector(r['features']) for r in all_rows])
        y = np.array([float(r['target']) for r in all_rows])
        w = np.array([
            _SAMPLE_WEIGHT_REAL if r.get('source') == 'real'
            else _SAMPLE_WEIGHT_SYNTHETIC
            for r in all_rows
        ])

        # 80/20 holdout — stratification by source so both splits see
        # synthetic and real if both exist.
        stratify = (
            [r.get('source', 'synthetic') for r in all_rows]
            if n_real > 0 else None
        )
        X_tr, X_ho, y_tr, y_ho, w_tr, _w_ho = train_test_split(
            X, y, w, test_size=0.2, random_state=42, stratify=stratify,
        )

        model = GradientBoostingRegressor(
            n_estimators=150,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )
        model.fit(X_tr, y_tr, sample_weight=w_tr)

        # Clip predictions at the same cap used at inference, so training
        # metrics reflect what the user will actually see.
        def _clip(v):
            return np.clip(v, -MAX_CORRECTION_PP, MAX_CORRECTION_PP)

        pred_tr = _clip(model.predict(X_tr))
        pred_ho = _clip(model.predict(X_ho))
        mae_tr = float(mean_absolute_error(y_tr, pred_tr))
        mae_ho = float(mean_absolute_error(y_ho, pred_ho))
        r2_ho  = float(r2_score(y_ho, pred_ho)) if len(set(y_ho)) > 1 else 0.0

        meta = CalibratorMeta(
            feature_version=FEATURE_VERSION,
            feature_names=list(FEATURE_NAMES),
            trained_at=datetime.utcnow().isoformat(timespec='seconds') + 'Z',
            n_train=n_total,
            n_synthetic=n_synth,
            n_real=n_real,
            mae_train=mae_tr,
            mae_holdout=mae_ho,
            r2_holdout=r2_ho,
            model_type='GradientBoostingRegressor',
            notes={
                'max_correction_pp':  MAX_CORRECTION_PP,
                'weight_synthetic':   _SAMPLE_WEIGHT_SYNTHETIC,
                'weight_real':        _SAMPLE_WEIGHT_REAL,
                'feedback_targets':   dict(_FEEDBACK_TARGET_CORRECTION),
            },
        )

        self._save(model, meta)
        self._model = model
        self._meta = meta
        self._loaded_from = MODEL_PATH.stat().st_mtime if MODEL_PATH.exists() else None
        return meta

    # ── Introspection ───────────────────────────────────────────────────
    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def meta(self) -> Optional[CalibratorMeta]:
        return self._meta


# ─────────────────────────────────────────────────────────────────────────────
#  Row-preparation helpers used by the management command
# ─────────────────────────────────────────────────────────────────────────────

def prepare_synthetic_rows(
    bootstrap_pairs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Run each synthetic pair through the live scoring pipeline and build
    a labeled training row from the result.

    The target is ``target_score - rule_based_score`` — i.e., the
    correction the model has to learn to apply.
    """
    # Imported here to avoid a circular import at module load time.
    from .matcher import JobMatcher
    jm = JobMatcher()
    rows: List[Dict[str, Any]] = []

    for pair in bootstrap_pairs:
        try:
            analysis = jm.generate_full_analysis(
                pair['resume_text'], pair['jd_text'],
            )
        except Exception as e:
            logger.warning("bootstrap: analysis failed for role=%s variant=%s: %s",
                           pair.get('role'), pair.get('variant'), e)
            continue

        features = analysis.get('scoringFeatures')
        if not features:
            continue

        rule_score = float(features.get('raw_score', analysis['matchScore']))
        target_correction = float(pair['target_score']) - rule_score
        rows.append({
            'features': features,
            'target':   target_correction,
            'source':   'synthetic',
            'meta':     {
                'role':          pair.get('role'),
                'variant':       pair.get('variant'),
                'target_score':  pair.get('target_score'),
                'rule_score':    rule_score,
            },
        })
    return rows


def prepare_real_rows(feedback_queryset) -> List[Dict[str, Any]]:
    """Build labeled training rows from AnalysisFeedback DB records.

    Each feedback row needs two pieces of data:
      - ``snapshot['features']`` — the feature vector captured at the time
        the analysis was run (added by matcher.py).
      - ``score_rating`` — maps to a target correction via
        _FEEDBACK_TARGET_CORRECTION.

    Feedback rows missing either piece are silently skipped.
    """
    rows: List[Dict[str, Any]] = []
    for fb in feedback_queryset:
        rating = fb.score_rating
        if rating not in _FEEDBACK_TARGET_CORRECTION:
            continue
        features = (fb.snapshot or {}).get('features')
        if not features:
            continue
        rows.append({
            'features': features,
            'target':   _FEEDBACK_TARGET_CORRECTION[rating],
            'source':   'real',
            'meta':     {
                'feedback_id':  fb.pk,
                'rating':       rating,
                'created_at':   fb.created_at.isoformat() if fb.created_at else None,
            },
        })
    return rows


# ─────────────────────────────────────────────────────────────────────────────
#  Public convenience — used from matcher.py at inference time.
# ─────────────────────────────────────────────────────────────────────────────

def predict_correction(ctx: Dict[str, Any]) -> float:
    """One-shot convenience for the hot path.

    ``ctx`` should contain ``match_results``, ``evidence_summary``, and
    ``raw_score``.  Returns 0.0 if no model is available.
    """
    try:
        return ScoreCalibrator.instance().predict(ctx)
    except Exception as e:
        logger.warning("score_calibrator: predict_correction failed: %s", e)
        return 0.0
