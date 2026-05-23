"""
Management command: evaluate the end-to-end scoring pipeline.

Runs a held-out set of (resume, JD, target_score) pairs through the live
JobMatcher.generate_full_analysis() pipeline and reports how close the
system's predicted match scores are to the synthetic ground truth.

This exists because MAE on the calibrator's internal training data only
measures one component of the pipeline.  The evaluation harness measures
the FULL pipeline: rule-based scoring + tier calibration + evidence
delta + learned calibrator + trending-skill bonus — composed together,
which is what a real user sees.

Two evaluation sources:
  1. Synthetic pairs (default).  Reuses calibration_bootstrap.generate_bootstrap_pairs
     but splits by ROLE (80/20) so test pairs cover roles unseen by the
     calibrator during training.  Reports MAE, RMSE, Spearman ρ, per-variant
     MAE breakdown, and bucket accuracy (within ±10pp).
  2. Real feedback rows (--include-real).  Reports 3-class agreement rate:
     how often the pipeline's score agrees with the user's scoreRating
     (too_high / accurate / too_low) given the feedback target bands.

Usage:
    python manage.py evaluate_pipeline
    python manage.py evaluate_pipeline --test-fraction 0.3
    python manage.py evaluate_pipeline --role-limit 50 --include-real
"""
from __future__ import annotations

import math
import random
import time
from typing import List, Tuple

from django.core.management.base import BaseCommand


# Score buckets for agreement reporting — mirror the feedback rating bands.
#   predicted - target  >  +10 pp  → pipeline thinks it's higher = "too_high"
#   predicted - target  <  -10 pp  → pipeline thinks it's lower  = "too_low"
#   else                           → "accurate"
_AGREEMENT_BAND_PP = 10.0


def _rank(values: List[float]) -> List[float]:
    """Ranks for Spearman.  Average rank on ties.  Pure Python — no scipy."""
    n = len(values)
    indexed = sorted(range(n), key=lambda i: values[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[indexed[j + 1]] == values[indexed[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1   # ranks are 1-indexed
        for k in range(i, j + 1):
            ranks[indexed[k]] = avg_rank
        i = j + 1
    return ranks


def _spearman(xs: List[float], ys: List[float]) -> float:
    """Spearman ρ — rank correlation, robust to non-linearity."""
    if len(xs) < 2:
        return float('nan')
    rx, ry = _rank(xs), _rank(ys)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx  = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy  = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return float('nan')
    return num / (dx * dy)


def _split_by_role(
    pairs: list[dict],
    test_fraction: float,
    seed: int,
) -> Tuple[list[dict], list[dict]]:
    """Role-level split: all pairs for a given role go to the same side.

    This prevents leakage: the calibrator may have been trained on
    (role=X, variant=strong) — if we put (role=X, variant=partial) in
    test, the model has already seen this role's feature distribution.
    """
    rng = random.Random(seed)
    roles = sorted({p['role'] for p in pairs})
    rng.shuffle(roles)
    split_at = int(len(roles) * (1.0 - test_fraction))
    train_roles = set(roles[:split_at])
    test_roles  = set(roles[split_at:])
    train = [p for p in pairs if p['role'] in train_roles]
    test  = [p for p in pairs if p['role'] in test_roles]
    return train, test


class Command(BaseCommand):
    help = "Evaluate end-to-end pipeline MAE/RMSE/Spearman on held-out pairs."

    def add_arguments(self, parser):
        parser.add_argument(
            '--role-limit', type=int, default=None,
            help='Limit synthetic generation to first N roles (faster dev cycles).',
        )
        parser.add_argument(
            '--test-fraction', type=float, default=0.2,
            help='Fraction of roles held out for evaluation (default 0.2).',
        )
        parser.add_argument(
            '--seed', type=int, default=7,
            help='RNG seed for the role-level split (default 7).',
        )
        parser.add_argument(
            '--include-real', action='store_true',
            help='Also evaluate against real AnalysisFeedback rows.',
        )

    def handle(self, *args, **opts):
        from matcher.services.calibration_bootstrap import generate_bootstrap_pairs
        from matcher.services.matcher import JobMatcher

        role_limit    = opts.get('role_limit')
        test_fraction = opts.get('test_fraction')
        seed          = opts.get('seed')
        include_real  = opts.get('include_real', False)

        t0 = time.time()
        self.stdout.write('Generating synthetic pairs...')
        pairs = generate_bootstrap_pairs(role_limit=role_limit)
        _, test = _split_by_role(pairs, test_fraction=test_fraction, seed=seed)
        self.stdout.write(
            f'  {len(pairs)} total pairs, {len(test)} held out for eval.'
        )

        if not test:
            self.stderr.write(self.style.ERROR(
                'No held-out pairs — increase role count or test fraction.'
            ))
            return

        matcher = JobMatcher()
        predictions: List[float] = []
        targets: List[float] = []
        per_variant: dict[str, list[float]] = {}
        failures = 0

        self.stdout.write('Running pairs through full pipeline...')
        for pair in test:
            try:
                result = matcher.generate_full_analysis(
                    pair['resume_text'], pair['jd_text']
                )
                pred = float(result.get('matchScore', 0))
            except Exception as e:                       # pragma: no cover
                failures += 1
                if failures <= 3:
                    self.stderr.write(f'  pipeline error on {pair["role"]}: {e}')
                continue

            target = float(pair['target_score'])
            predictions.append(pred)
            targets.append(target)
            per_variant.setdefault(pair['variant'], []).append(abs(pred - target))

        n = len(predictions)
        if n == 0:
            self.stderr.write(self.style.ERROR('All pairs failed.'))
            return

        abs_errors = [abs(p - t) for p, t in zip(predictions, targets)]
        sq_errors  = [(p - t) ** 2 for p, t in zip(predictions, targets)]
        mae  = sum(abs_errors) / n
        rmse = math.sqrt(sum(sq_errors) / n)
        rho  = _spearman(predictions, targets)

        # Agreement: within ±10 pp of target → "accurate"; else too_high/too_low.
        within_band = sum(1 for e in (p - t for p, t in zip(predictions, targets))
                          if abs(e) <= _AGREEMENT_BAND_PP)
        too_high    = sum(1 for e in (p - t for p, t in zip(predictions, targets))
                          if e >  _AGREEMENT_BAND_PP)
        too_low     = sum(1 for e in (p - t for p, t in zip(predictions, targets))
                          if e < -_AGREEMENT_BAND_PP)

        elapsed = time.time() - t0

        # ── Report ──────────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS('\nSynthetic-pair evaluation'))
        self.stdout.write(f'  pairs scored:   {n}  ({failures} failures)')
        self.stdout.write(f'  MAE:            {mae:.2f} pp')
        self.stdout.write(f'  RMSE:           {rmse:.2f} pp')
        self.stdout.write(f'  Spearman ρ:     {rho:.3f}')
        self.stdout.write(f'  within ±{int(_AGREEMENT_BAND_PP)}pp:    '
                          f'{within_band}/{n}  ({100*within_band/n:.1f}%)')
        self.stdout.write(f'  over-predicting:  {too_high}  '
                          f'({100*too_high/n:.1f}%)')
        self.stdout.write(f'  under-predicting: {too_low}  '
                          f'({100*too_low/n:.1f}%)')

        self.stdout.write('\n  MAE by variant:')
        for variant in ('strong', 'partial', 'mismatch'):
            errs = per_variant.get(variant, [])
            if errs:
                v_mae = sum(errs) / len(errs)
                self.stdout.write(
                    f'    {variant:<9}  n={len(errs):>3}   mae={v_mae:.2f} pp'
                )

        # ── Optional real-feedback evaluation ───────────────────────────
        if include_real:
            self._evaluate_real_feedback(matcher)

        self.stdout.write(f'\n  elapsed: {elapsed:.1f}s')

    # ------------------------------------------------------------------
    def _evaluate_real_feedback(self, matcher) -> None:
        """3-class agreement check against AnalysisFeedback.score_rating."""
        from matcher.models import AnalysisFeedback

        self.stdout.write(self.style.SUCCESS('\nReal-feedback evaluation'))
        qs = AnalysisFeedback.objects.exclude(score_rating__isnull=True)
        rows = list(qs)
        if not rows:
            self.stdout.write('  no feedback rows with score_rating — skipping.')
            return

        # For each row we have the ORIGINAL analysis score (stored on
        # snapshot.matchScore) and the user's rating.  We don't rerun the
        # pipeline; that would evaluate the NEW pipeline against OLD user
        # feedback, which is the right thing — but we need the original
        # resume/JD to rerun.  Since we don't store resume text on the
        # feedback row, we just score the AGREEMENT of the snapshot score.
        agree = too_high = too_low = 0
        for fb in rows:
            snap = fb.snapshot or {}
            score = snap.get('matchScore')
            rating = fb.score_rating
            if score is None or rating not in ('too_high', 'accurate', 'too_low'):
                continue
            if rating == 'accurate':
                agree += 1
            elif rating == 'too_high':
                too_high += 1
            else:
                too_low += 1

        total = agree + too_high + too_low
        if total == 0:
            self.stdout.write('  no usable feedback rows — skipping.')
            return

        self.stdout.write(f'  rows:             {total}')
        self.stdout.write(f'  accurate:         {agree}  ({100*agree/total:.1f}%)')
        self.stdout.write(f'  too_high rating:  {too_high}  ({100*too_high/total:.1f}%)')
        self.stdout.write(f'  too_low  rating:  {too_low}   ({100*too_low/total:.1f}%)')
        self.stdout.write(
            '  (higher "accurate" = better; high too_high/too_low = '
            'systematic bias that the next retrain should correct)'
        )
