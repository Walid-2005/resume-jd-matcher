"""
Management command: retrain the score calibrator.

Two-stage training:
  1. Generate synthetic bootstrap pairs from the role profiles.
  2. Pull real user feedback rows from AnalysisFeedback.
  3. Train a fresh model combining both (synthetic weight=1, real weight=3).
  4. Persist the pickle + metadata under matcher/trained_data/.

Usage:
    python manage.py retrain_calibrator                 # full retrain
    python manage.py retrain_calibrator --role-limit 20 # dev-speed retrain
    python manage.py retrain_calibrator --skip-real     # synthetic only
"""
from __future__ import annotations

import time
from django.core.management.base import BaseCommand

from matcher.models import AnalysisFeedback
from matcher.services.calibration_bootstrap import generate_bootstrap_pairs
from matcher.services.score_calibrator import (
    ScoreCalibrator,
    prepare_synthetic_rows,
    prepare_real_rows,
)


class Command(BaseCommand):
    help = "Retrain the score calibrator (synthetic bootstrap + real feedback)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--role-limit', type=int, default=None,
            help='Limit synthetic generation to first N roles (faster dev cycles).',
        )
        parser.add_argument(
            '--skip-real', action='store_true',
            help='Skip real-feedback rows; train on synthetic data only.',
        )
        parser.add_argument(
            '--skip-synthetic', action='store_true',
            help='Skip synthetic bootstrap; train on real feedback only.',
        )

    def handle(self, *args, **opts):
        role_limit   = opts.get('role_limit')
        skip_real    = opts.get('skip_real', False)
        skip_synth   = opts.get('skip_synthetic', False)

        t0 = time.time()

        # ── 1. Synthetic rows ────────────────────────────────────────────
        synthetic_rows = []
        if not skip_synth:
            self.stdout.write('Generating synthetic bootstrap pairs...')
            pairs = generate_bootstrap_pairs(role_limit=role_limit)
            self.stdout.write(f'  {len(pairs)} pairs generated.')

            self.stdout.write('Running pairs through scoring pipeline '
                              '(this takes a minute)...')
            synthetic_rows = prepare_synthetic_rows(pairs)
            self.stdout.write(f'  {len(synthetic_rows)} usable synthetic rows.')

        # ── 2. Real-feedback rows ───────────────────────────────────────
        real_rows = []
        if not skip_real:
            self.stdout.write('Loading real feedback rows...')
            qs = AnalysisFeedback.objects.exclude(score_rating__isnull=True)
            real_rows = prepare_real_rows(qs)
            self.stdout.write(f'  {len(real_rows)} usable feedback rows.')

        # ── 3. Train ────────────────────────────────────────────────────
        calibrator = ScoreCalibrator.instance()
        try:
            meta = calibrator.train(synthetic_rows, real_rows)
        except ValueError as e:
            self.stderr.write(self.style.ERROR(str(e)))
            return

        elapsed = time.time() - t0

        # ── 4. Report ───────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS('\nCalibrator retrained.'))
        self.stdout.write(f'  total rows:    {meta.n_train}')
        self.stdout.write(f'    synthetic:   {meta.n_synthetic}')
        self.stdout.write(f'    real:        {meta.n_real}')
        self.stdout.write(f'  MAE (train):   {meta.mae_train:.2f} pp')
        self.stdout.write(f'  MAE (hold):    {meta.mae_holdout:.2f} pp')
        self.stdout.write(f'  R²  (hold):    {meta.r2_holdout:.3f}')
        self.stdout.write(f'  trained_at:    {meta.trained_at}')
        self.stdout.write(f'  elapsed:       {elapsed:.1f}s')
