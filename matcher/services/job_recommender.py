"""
Job recommendation engine.

Given a user's extracted resume skills, experience level, and location,
generates relevant job recommendations with LinkedIn job-search URLs.

Uses the full 200+ trained ROLE_SKILL_TEMPLATES so recommendations are
diverse, skill-aware, and sorted by match percentage (highest first).
"""
from __future__ import annotations

import re
from urllib.parse import quote_plus

from .ml_matcher import ROLE_SKILL_TEMPLATES


# ── Category detection ──────────────────────────────────────────────────
# Assign each role to a display category for the frontend badge.

_CATEGORY_RULES: list[tuple[list[str], str]] = [
    # Order matters — first match wins
    (["ai ", "artificial intelligence", "machine learning", "deep learning",
      "nlp", "computer vision", "big data"], "ai"),
    (["data sci", "data analy", "data eng", "data arch", "database",
      "analytics", "business intelligence", "power bi"], "data"),
    (["cybersecurity", "security", "penetration", "network security"], "security"),
    (["network eng", "system admin", "it support", "it manag", "it eng",
      "it consult", "it audit", "help desk", "technical support"], "it"),
    (["devops", "cloud", "site reliability", "platform eng"], "devops"),
    (["software", "developer", "full stack", "front end", "back end",
      "web develop", "mobile develop", "java ", "python ", "php ",
      "dotnet", "c# ", "blockchain", "game develop", "api develop",
      "embedded", "mainframe", "programmer", "qa eng", "test auto",
      "software arch", "firmware"], "technology"),
    (["mechanical", "electrical", "civil", "automotive", "biomedical",
      "agricultural", "hardware"], "engineering"),
    (["product manag", "project manag", "scrum", "agile"], "management"),
    (["marketing", "seo", "social media", "content", "digital market",
      "graphic design", "ui/ux", "copywriter", "brand"], "marketing"),
    (["sales", "account manag", "account exec", "business develop",
      "retail"], "sales"),
    (["financ", "accountant", "auditor", "bank", "invest", "tax ",
      "treasury", "insurance", "credit", "actuary"], "finance"),
    (["doctor", "nurse", "pharma", "dentist", "dental", "health",
      "medical", "therapist", "veterinar", "optometri", "radiolog",
      "physiotherap", "dietitian", "speech"], "healthcare"),
    (["lawyer", "paralegal", "legal", "compliance", "counsel",
      "attorney"], "legal"),
    (["teacher", "tutor", "professor", "instruct", "education",
      "librarian"], "education"),
    (["journalist", "public relation", "video produc", "photograph",
      "animat", "music", "podcast", "editor"], "media"),
    (["hr ", "recruit", "training manag"], "hr"),
    (["supply chain", "logistics", "warehouse", "procurement",
      "inventory", "quality assur", "fleet"], "operations"),
    (["chef", "restaurant", "event plan", "travel", "flight attend",
      "customer service", "tour guide", "barista", "reception",
      "hotel", "front desk"], "hospitality"),
    (["real estate", "property", "construction", "architect",
      "interior design"], "real_estate"),
    (["chief ", "vice president", "director", "ceo", "cto", "cfo",
      "coo", "cmo", "cio"], "executive"),
    (["research", "scientist", "lab tech", "chemist", "environment"],
     "science"),
    (["plumber", "electrician", "welder", "hvac", "security guard"],
     "trades"),
    (["coach", "trainer", "sports", "fitness"], "sports"),
    (["social worker", "case manag", "policy", "urban plan",
      "grant writer", "sustainability"], "public_service"),
    (["writer", "translator", "technical writ"], "writing"),
]


def _categorize_role(role_name: str) -> str:
    """Assign a display category to a role name."""
    r = role_name.lower()
    for keywords, category in _CATEGORY_RULES:
        if any(kw in r for kw in keywords):
            return category
    return "general"


# ── Description templates ───────────────────────────────────────────────
# Short auto-generated descriptions per category so every card has context.

_CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "ai": "Work on artificial intelligence and machine learning solutions to solve complex problems.",
    "data": "Analyse, transform, and manage data to drive insights and business decisions.",
    "security": "Protect systems and data from cyber threats through security analysis and implementation.",
    "it": "Manage IT infrastructure, support users, and ensure technology systems run smoothly.",
    "devops": "Automate infrastructure, manage CI/CD pipelines, and ensure reliable cloud deployments.",
    "technology": "Design, develop, and maintain software applications and technical systems.",
    "engineering": "Apply engineering principles to design, build, and improve products and systems.",
    "management": "Plan, execute, and deliver projects while coordinating teams and stakeholders.",
    "marketing": "Create and execute marketing strategies to build brands and drive engagement.",
    "sales": "Drive revenue growth by identifying opportunities and building client relationships.",
    "finance": "Manage financial operations, analysis, and reporting to support business objectives.",
    "healthcare": "Provide patient care, medical services, and support health system operations.",
    "legal": "Handle legal matters, ensure compliance, and provide counsel on regulatory issues.",
    "education": "Educate, mentor, and develop learning experiences for students and trainees.",
    "media": "Create, produce, and distribute media content across various platforms.",
    "hr": "Manage talent acquisition, employee relations, and organisational development.",
    "operations": "Optimise supply chain, logistics, and operational processes for efficiency.",
    "hospitality": "Deliver excellent customer experiences in service and hospitality environments.",
    "real_estate": "Manage properties, real estate transactions, and construction projects.",
    "executive": "Lead organisations with strategic vision, stakeholder management, and governance.",
    "science": "Conduct research, experiments, and analysis to advance scientific knowledge.",
    "trades": "Perform skilled trade work in installation, maintenance, and repair.",
    "sports": "Coach, train, and support athletes and fitness programmes.",
    "public_service": "Serve communities through social work, policy, and public programmes.",
    "writing": "Create professional written content, documentation, and translations.",
    "general": "Contribute professional skills and expertise to organisational goals.",
}


# ── Level prefix mapping ────────────────────────────────────────────────

_LEVEL_PREFIXES = {
    "junior": "Junior ",
    "mid": "",
    "senior": "Senior ",
}

_LEVEL_YEARS = {
    "junior": "0-2 years",
    "mid": "2-5 years",
    "senior": "5+ years",
}


# ── Public API ──────────────────────────────────────────────────────────

# ── Generic soft skills (should not inflate match scores alone) ──────────
_GENERIC_SOFT = {
    "communication", "teamwork", "problem solving", "time management",
    "leadership", "adaptability", "creativity", "attention to detail",
    "multitasking", "organizational skills", "interpersonal skills",
    "critical thinking", "decision making", "self-motivated",
    "conflict resolution", "customer service",
}

# Roles that should never get a seniority prefix
_NO_PREFIX_ROLES = {
    "chief executive officer", "chief technology officer",
    "chief financial officer", "chief operating officer",
    "chief marketing officer", "chief information officer",
    "chief of staff", "vice president", "director",
}


def get_job_recommendations(
    resume_skills: list[str],
    experience_level: str = "mid",
    location: str = "",
    max_results: int = 20,
) -> list[dict]:
    """Generate job recommendations based on resume skills.

    Scans all 200+ trained ROLE_SKILL_TEMPLATES, scores each with a
    composite formula that balances match_percentage with absolute
    match_count, and requires at least one domain-specific skill
    to prevent inflated scores from generic soft skills alone.

    Args:
        resume_skills: Skills extracted from the user's resume.
        experience_level: One of 'junior', 'mid', 'senior'.
        location: User's preferred location (city / country).
        max_results: Maximum number of recommendations to return.

    Returns:
        List of recommendation dicts sorted by composite score descending.
    """
    if not resume_skills:
        return []

    resume_set = {s.lower() for s in resume_skills}
    level = experience_level.lower() if experience_level else "mid"
    prefix = _LEVEL_PREFIXES.get(level, "")

    scored: list[tuple[float, dict]] = []

    for role_name, role_skills_list in ROLE_SKILL_TEMPLATES.items():
        role_skills = {s.lower() for s in role_skills_list}

        matched = resume_set & role_skills
        match_count = len(matched)
        total_skills = len(role_skills)

        if total_skills == 0:
            continue

        match_pct = round(match_count / total_skills * 100)

        # ── Quality gates ────────────────────────────────────────
        # 1. Minimum 2 matching skills
        if match_count < 2:
            continue

        # 2. At least 20% match
        if match_pct < 20:
            continue

        # 3. Require at least 1 non-soft-skill match to avoid
        #    "plumber" ranking high just because of communication
        domain_matches = matched - _GENERIC_SOFT
        if len(domain_matches) == 0 and total_skills >= 5:
            continue

        # ── Composite score ──────────────────────────────────────
        # Balance percentage (favours small skill sets) with
        # absolute count (favours deep matches).
        # Formula: 55% weight on percentage + 45% on normalised count
        normalised_count = min(match_count / 10.0, 1.0)  # Cap at 10
        composite = match_pct * 0.55 + normalised_count * 45

        # ── Build recommendation ─────────────────────────────────
        category = _categorize_role(role_name)

        # Don't add Junior/Senior to executive roles
        if role_name.lower() in _NO_PREFIX_ROLES:
            full_title = role_name.title()
        else:
            full_title = f"{prefix}{role_name.title()}"

        required_list = sorted(s.title() for s in role_skills)
        matched_list = sorted(s.title() for s in matched)
        missing_list = sorted(s.title() for s in role_skills - matched)

        linkedin_url = _build_linkedin_url(full_title, location)

        rec = {
            "title": full_title,
            "company": "Various companies hiring",
            "location": location if location else "Remote / Multiple locations",
            "required_skills": required_list,
            "matched_skills": matched_list,
            "missing_skills": missing_list[:8],
            "match_count": match_count,
            "total_skills": total_skills,
            "match_percentage": match_pct,
            "description": _CATEGORY_DESCRIPTIONS.get(
                category, _CATEGORY_DESCRIPTIONS["general"]
            ),
            "experience_level": _LEVEL_YEARS.get(level, "2-5 years"),
            "category": category,
            "linkedin_url": linkedin_url,
        }

        scored.append((composite, rec))

    # Sort by composite score descending, then title alphabetically
    scored.sort(key=lambda x: (-x[0], x[1]["title"]))

    return [rec for _, rec in scored[:max_results]]


def _build_linkedin_url(job_title: str, location: str = "") -> str:
    """Build a LinkedIn job search URL for a given title and location."""
    params = quote_plus(job_title)
    url = f"https://www.linkedin.com/jobs/search/?keywords={params}"
    if location:
        url += f"&location={quote_plus(location)}"
    return url
