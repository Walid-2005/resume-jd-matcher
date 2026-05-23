# ResuMatch — Hybrid Resume × Job Description Matcher

Final-year project for COMP3025 (UNMC). A Django + React web application
that scores how well a resume matches a job description, combining a
deterministic rule-based engine with three lightweight ML augmentations:

- a Gradient-Boosted-Regressor **score calibrator** (FEATURE_VERSION 2)
- a sentence-transformer **bi-encoder** for paraphrase-based skill recovery
  on both the JD and the CV side
- an **emerging-skills tracker** that rewards trending skills

The full report lives in `Final_Report.md` / `Final_Report.docx`.

---

## Quick start

After cloning (or after deleting `venv/` and starting fresh):

```bash
# 1. Backend ────────────────────────────────────────────────────────
python3.12 -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver            # http://127.0.0.1:8000

# 2. Frontend (separate terminal) ───────────────────────────────────
cd "AI Resume Analyzer Interface"
npm install
npm run dev                           # http://localhost:5173
```

Open `http://localhost:5173` for the dev UI. The Vite dev server proxies
`/api/*` calls to Django on `:8000`.

For a production-style single-server build (Django serves the bundled
React app at `http://127.0.0.1:8000/`):

```bash
cd "AI Resume Analyzer Interface"
npm run build
# the build pipeline drops the bundle into static/frontend/
cd ..
python manage.py runserver
```

---

## Prerequisites

| Tool                 | Version            | Notes                                                   |
| -------------------- | ------------------ | ------------------------------------------------------- |
| **Python**           | 3.12 (3.11 ok)     | The venv was created against 3.12; 3.13 is untested.    |
| **pip**              | recent             | Bundled with Python.                                    |
| **Node.js**          | 18 or newer        | For the Vite frontend.                                  |
| **npm**              | bundled with Node  |                                                         |
| **Disk**             | ~3 GB free         | First run downloads the `all-MiniLM-L6-v2` model (~90 MB) plus PyTorch wheels (~800 MB) and a few more dependencies. |
| **CPU**              | any modern x86/ARM | No GPU required. Inference runs on CPU; an analysis takes ~2 s. |

The project ships with `db.sqlite3` so no external database is needed.

---

## Backend setup (detailed)

```bash
# 1. Create + activate the virtual environment.
#    Use python3.12 explicitly to match the lock file the project was
#    developed against.
python3.12 -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate

# 2. Install pinned dependencies.
pip install --upgrade pip
pip install -r requirements.txt

# 3. Apply migrations (creates the SQLite schema if db.sqlite3 doesn't
#    exist, or upgrades it if you've changed the models).
python manage.py migrate

# 4. (Optional) Create a superuser for the admin site.
python manage.py createsuperuser

# 5. Run the dev server.
python manage.py runserver
```

The first analysis after install will pause for ~30 s while
`sentence-transformers` downloads the `all-MiniLM-L6-v2` model into
`~/.cache/huggingface/`. Subsequent analyses are instant.

### What gets created

| Path                            | What                                          |
| ------------------------------- | --------------------------------------------- |
| `venv/`                         | Virtual environment.                          |
| `db.sqlite3`                    | Auth, analysis history, feedback, JD cache.   |
| `matcher/trained_data/score_calibrator.pkl` | Trained calibrator model. **Already shipped** in the repo, so the calibrator is active out of the box. Retrain with `python manage.py retrain_calibrator`. |
| `~/.cache/huggingface/`         | Downloaded bi-encoder weights (~90 MB).       |

---

## Frontend setup

The React UI lives in `AI Resume Analyzer Interface/` and is built with
Vite + React + MUI + Radix UI.

```bash
cd "AI Resume Analyzer Interface"

# Dev mode — fast HMR, frontend at :5173, talks to backend at :8000
npm install
npm run dev

# Production build — outputs to static/frontend/, served by Django at /
npm run build
```

`vite.config.ts` sets up the dev proxy for `/api/*` so the React app
works against `python manage.py runserver` without CORS configuration.

---

## Common operations

All commands assume an activated venv (`source venv/bin/activate`) at the
project root.

### Run the test suite

```bash
python manage.py test matcher
```

### Retrain the score calibrator

The calibrator is a `GradientBoostingRegressor` trained on synthetic
bootstrap pairs plus any real `AnalysisFeedback` rows the system has
collected.

```bash
# Full retrain (~30 s for 40 roles × 3 variants each)
python manage.py retrain_calibrator

# Faster iteration while developing
python manage.py retrain_calibrator --role-limit 10

# Synthetic only — skip user-feedback rows
python manage.py retrain_calibrator --skip-real
```

The new model is written atomically to
`matcher/trained_data/score_calibrator.pkl`. Live requests pick it up
automatically (the calibrator singleton compares mtime on every call).

### Evaluate the end-to-end pipeline

The held-out evaluation harness splits the role catalogue 80/20 at the
**role** level (not the pair level — prevents leakage) and reports MAE,
RMSE, Spearman ρ, within-band accuracy, and per-variant MAE.

```bash
# Full evaluation (~30 s)
python manage.py evaluate_pipeline

# Custom test fraction or RNG seed
python manage.py evaluate_pipeline --test-fraction 0.3 --seed 13

# Also score against real AnalysisFeedback rows
python manage.py evaluate_pipeline --include-real
```

### Regenerate the figures used in the report

```bash
python /tmp/make_figures.py            # 12 schematic + ablation figures
python /tmp/make_analysis_figures.py   # 6 analytical figures from real data
```

(Both scripts write PNGs into `figures/`. They're idempotent.)

### Rebuild the Word version of the report

```bash
python /tmp/build_reference.py    # only if reference styling changed
python /tmp/build_with_cover.py   # body-content rebuild
```

---

## Project structure

```
FYP/
├── manage.py                            Django entry point
├── requirements.txt                     Python pinned deps
├── db.sqlite3                           Local DB (shipped with seed data)
├── reference.docx                       Pandoc style reference for docx export
├── Final_Report.md / .docx              FYP final report
├── figures/                             18 PNGs referenced by the report
│
├── resume_matcher/                      Django project package
│   ├── settings.py
│   └── urls.py
│
├── matcher/                             Main Django app
│   ├── models.py                        AnalysisFeedback, AnalysisHistory…
│   ├── views.py                         REST endpoints
│   ├── urls.py                          API routes
│   ├── trained_data/
│   │   └── score_calibrator.pkl         Trained calibrator (FEATURE_VERSION 2)
│   ├── management/commands/
│   │   ├── retrain_calibrator.py        Bootstrap + real-feedback retrain
│   │   └── evaluate_pipeline.py         Held-out evaluation harness
│   └── services/                        Pure logic — no Django dependencies
│       ├── matcher.py                   JobMatcher orchestrator
│       ├── ml_matcher.py                Bi-encoder + scoring + role taxonomy
│       ├── score_calibrator.py          Calibrator load/save/predict
│       ├── calibration_features.py      FEATURE_VERSION contract
│       ├── calibration_bootstrap.py     Synthetic pair generator
│       ├── role_inheritance.py          Parent-pointer role graph
│       ├── resume_parser.py             PDF / docx / text intake
│       ├── resume_sections.py           Section labelling for evidence scoring
│       ├── emerging_skills.py           Trending-skill bonus
│       └── trained_skills.py            Kaggle-derived skill dictionary
│
├── AI Resume Analyzer Interface/        React + Vite frontend
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│
├── static/                              Static assets shipped with Django
└── staticfiles/                         collectstatic output (gitignored)
```

---

## API surface (summary)

Mounted under `/api/`. See `matcher/urls.py` for the full list.

| Endpoint                            | Method | Purpose                                    |
| ----------------------------------- | ------ | ------------------------------------------ |
| `/api/register/`                    | POST   | Create a user account.                     |
| `/api/login/`                       | POST   | Session login.                             |
| `/api/logout/`                      | POST   | Session logout.                            |
| `/api/check-auth/`                  | GET    | Return current session state.              |
| `/api/analyze/`                     | POST   | The main scoring endpoint. Body: `{resume_text, job_description}` (or upload). Returns score, strengths, weaknesses, recommendations, AI insight. |
| `/api/history/`                     | GET    | List the current user's analyses.          |
| `/api/history/<id>/`                | GET    | Fetch a single past analysis.              |
| `/api/history/<id>/delete/`         | POST   | Delete an analysis.                        |
| `/api/export/<fmt>/`                | GET    | Export a report (`pdf` or `docx`).         |
| `/api/fetch-job/`                   | POST   | Pull a JD from a public job-board URL.     |
| `/api/recommend-jobs/`              | POST   | Career-path recommendations from a resume. |
| `/api/feedback/`                    | POST   | Submit a `score_rating` for retraining.    |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'sentence_transformers'`**
The venv isn't active or `pip install -r requirements.txt` failed. Check
`which python` returns a path inside `venv/`.

**`KeyError: 'all-MiniLM-L6-v2'` or HuggingFace timeout on first analysis**
First run needs internet access to fetch the model into
`~/.cache/huggingface/`. After that, the pipeline works offline.

**`sqlite3.OperationalError: no such table: …`**
You haven't run migrations yet. `python manage.py migrate`.

**Frontend at `:5173` shows "Failed to fetch /api/…"**
Django isn't running on `:8000`, or you opened the production-built
`/static/frontend/index.html` while also running Vite on `:5173`. Pick
one path: dev (`npm run dev` + `runserver`) or prod (`npm run build` +
`runserver`).

**Calibrator score doesn't change after retraining**
The calibrator singleton reloads on file mtime. Force a reload by
restarting `runserver`, or check that
`matcher/trained_data/score_calibrator.pkl` was actually rewritten.

**`FEATURE_VERSION` mismatch warning in logs**
The pickled calibrator was trained against a different feature schema
than the current code. Run `python manage.py retrain_calibrator` to
rebuild against the current `FEATURE_VERSION`.

---

## License + acknowledgements

Project written for COMP3025 (BSc Computer Science with AI),
University of Nottingham Malaysia Campus, 2025-2026 academic year.

External components used under their respective licences:
`Django`, `scikit-learn`, `sentence-transformers` (Apache 2.0),
`PyPDF2`, `python-docx` (MIT), `MUI` and `Radix UI` (MIT).

The `all-MiniLM-L6-v2` bi-encoder is from
[Sentence-Transformers](https://www.sbert.net/) (Apache 2.0).
