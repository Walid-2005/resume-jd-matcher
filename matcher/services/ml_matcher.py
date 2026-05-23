"""
ML-enhanced matching service with hybrid scoring system.
Combines structured rule-based skill matching, semantic similarity,
and experience alignment for accurate, explainable resume-job matching.
"""
import re
from typing import Dict, List, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity

# Import sentence transformers - required for ML matching
from sentence_transformers import SentenceTransformer

# Import recommendation generator for career-building suggestions
from .recommendations import RecommendationGenerator

# Import trained skill data from Kaggle dataset
from .trained_skills import (
    TRAINED_SKILL_DICTIONARY,
    TRAINED_ROLE_SKILL_TEMPLATES,
    TRAINED_ROLE_KEYWORD_MAP,
    SKILL_FREQUENCIES,
    ROLE_SKILL_PROFILES,
    ROLE_PROFILE_KEYWORDS,
)


# Predefined skill dictionary grouped by domain (hand-curated base)
_BASE_SKILL_DICTIONARY = {
    "hospitality": [
        "front desk", "customer service", "guest relations", "reservation systems",
        "hotel management", "concierge", "housekeeping", "event planning",
        "food and beverage", "hospitality management", "guest satisfaction",
        "check-in", "check-out", "room service", "banquet", "catering",
        "property management system", "opera pms", "front office",
    ],
    "technology": [
        "python", "java", "javascript", "typescript", "c++", "c#", "php", "ruby",
        "go", "rust", "swift", "kotlin", "scala", "perl", "matlab", "sql", "pl/sql",
        "html", "css", "sass", "less",
        "react", "angular", "vue", "node.js", "nodejs", "express", "django", "flask",
        "fastapi", "spring", "laravel", "asp.net", "jquery", "bootstrap", "tailwind",
        "mysql", "postgresql", "mongodb", "redis", "oracle", "sqlite", "cassandra",
        "dynamodb", "elasticsearch", "neo4j", "firebase", "supabase",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github",
        "gitlab", "ci/cd", "terraform", "ansible", "linux", "unix", "bash", "shell",
        "machine learning", "deep learning", "data science", "data analysis",
        "pandas", "numpy", "tensorflow", "pytorch", "scikit-learn", "keras",
        "opencv", "nlp", "computer vision", "artificial intelligence",
        "react native", "flutter", "ios", "android",
        "rest api", "graphql", "microservices", "websocket",
        "agile", "scrum", "kanban", "jira", "confluence",
    ],
    "business": [
        "microsoft office", "microsoft word", "microsoft excel", "microsoft powerpoint",
        "ms office", "ms word", "ms excel", "ms powerpoint",
        "excel", "word", "powerpoint", "outlook", "sharepoint", "teams",
        "google workspace", "google docs", "google sheets", "google slides",
        "salesforce", "sap", "quickbooks", "xero", "hubspot", "zoho",
        "tableau", "power bi", "qlik", "looker", "business intelligence",
        "project management", "strategic planning", "business development",
        "financial analysis", "budgeting", "forecasting", "risk management",
        "change management", "stakeholder management",
    ],
    "marketing": [
        "social media", "digital marketing", "content marketing", "seo", "sem",
        "ppc", "google ads", "email marketing", "marketing automation", "crm",
        "facebook", "instagram", "linkedin", "tiktok", "youtube",
        "adobe photoshop", "photoshop",
        "adobe illustrator", "illustrator",
        "adobe indesign", "indesign",
        "adobe premiere", "adobe after effects",
        "figma", "sketch", "canva", "graphic design", "ui/ux design",
        "video editing", "photo editing",
        "typography", "branding", "colour theory", "color theory",
        "motion design", "storyboarding", "wireframing",
    ],
    "healthcare": [
        "patient care", "medical records", "clinical research", "nursing",
        "pharmacy", "medical terminology", "hipaa", "ehr", "electronic health records",
        "first aid", "cpr", "vital signs", "phlebotomy", "triage",
    ],
    "finance": [
        "accounting", "bookkeeping", "financial reporting", "tax preparation",
        "auditing", "accounts payable", "accounts receivable", "payroll",
        "investment analysis", "portfolio management", "financial modeling",
        "financial modelling", "financial analysis", "valuation", "dcf",
        "discounted cash flow", "financial forecasting", "budgeting",
        "variance analysis", "p&l", "profit and loss", "bloomberg",
        "capital markets", "equity research", "credit analysis",
        "compliance", "regulatory reporting",
    ],
    "languages": [
        "french", "spanish", "german", "italian", "portuguese", "chinese",
        "mandarin", "japanese", "korean", "arabic", "hindi", "russian",
    ],
    "general": [
        "communication", "leadership", "teamwork", "collaboration",
        "problem solving", "critical thinking", "analytical skills",
        "time management", "mentoring", "training", "presentation",
        "negotiation", "customer service", "client relations",
        "attention to detail", "multitasking", "organizational skills",
        "interpersonal skills", "conflict resolution", "decision making",
        "adaptability", "creativity", "research", "writing",
        "public speaking", "data entry", "sales", "consulting",
    ],
}

# ── Merge hand-curated + trained skill dictionaries ───────────────
# The trained data from Kaggle supplements the curated base.
# Domain mapping: trained → base
_TRAINED_DOMAIN_MAP = {
    "technology": "technology",
    "business": "business",
    "marketing": "marketing",
    "finance": "finance",
    "healthcare": "healthcare",
    "engineering": "technology",  # engineering skills go into tech
    "general": "general",
    "languages": "languages",
}

SKILL_DICTIONARY: dict[str, list[str]] = {}
# Start from the curated base
for _domain, _skills in _BASE_SKILL_DICTIONARY.items():
    SKILL_DICTIONARY[_domain] = list(_skills)

# Merge trained skills
for _t_domain, _t_skills in TRAINED_SKILL_DICTIONARY.items():
    _target = _TRAINED_DOMAIN_MAP.get(_t_domain, "general")
    if _target not in SKILL_DICTIONARY:
        SKILL_DICTIONARY[_target] = []
    _existing = set(s.lower() for s in SKILL_DICTIONARY[_target])
    for _skill in _t_skills:
        if _skill.lower() not in _existing:
            SKILL_DICTIONARY[_target].append(_skill)
            _existing.add(_skill.lower())

# Clean up temp variables
del _domain, _skills, _t_domain, _t_skills, _target, _existing, _skill


# Synonym groups for partial matching across adjacent domains.
# Key = canonical skill name, Values = recognised synonyms / aliases.
# A skill may appear in multiple groups — the reverse lookup merges them
# so that partial-match checks remain a single O(1) set lookup.
SKILL_SYNONYMS = {
    # Data & analytics
    "data analysis": ["analytics", "data analytics", "analytical skills", "data interpretation"],
    "business intelligence": ["bi", "data visualization", "data visualisation", "reporting tools"],
    # Finance & accounting
    "financial reporting": ["financial analysis", "financial statements", "financial reports",
                            "financial modeling"],
    "financial modeling": ["financial modelling", "financial model", "financial models"],
    "valuation": ["dcf", "discounted cash flow", "company valuation", "equity valuation",
                  "business valuation", "lbo", "leveraged buyout"],
    "accounting": ["financial accounting", "financial management", "investment analysis"],
    "bookkeeping": ["financial records", "ledger management"],
    "budgeting": ["budget management", "financial planning", "forecasting"],
    "auditing": ["audit", "internal audit", "compliance review", "investment analysis"],
    # Tech
    "machine learning": ["ml", "predictive modeling", "predictive modelling"],
    "artificial intelligence": ["ai"],
    "sql": ["database querying", "database management", "relational databases"],
    # Tools
    "excel": ["spreadsheets", "ms excel", "microsoft excel"],
    "project management": ["programme management", "program management"],
    # Hospitality / service
    "customer service": ["customer support", "client service", "client support", "guest services"],
    # Soft skills
    "leadership": ["team leadership", "people management", "team management"],
    "teamwork": ["team collaboration", "collaboration", "team player"],
    "problem solving": ["troubleshooting", "analytical thinking", "critical thinking"],
    "communication": ["verbal communication", "written communication", "interpersonal communication"],
    "presentation": ["public speaking", "presenting"],
    # AI / ML synonyms
    "deep learning": ["neural networks", "deep neural networks", "cnn", "rnn", "lstm", "transformer"],
    "tensorflow": ["tensorflow.js", "tf", "keras"],
    "pytorch": ["torch"],
    "computer vision": ["image recognition", "object detection", "image processing", "yolo", "yolov5"],
    "nlp": ["natural language processing", "text mining", "text analysis", "language model"],
    "opencv": ["cv2", "image processing"],
    "data science": ["data mining", "statistical analysis", "statistical modeling"],
    "numpy": ["numerical computing"],
    "pandas": ["dataframe", "data manipulation"],
    "docker": ["containerization", "containers"],
    "git": ["github", "gitlab", "version control"],
    "react native": ["mobile development", "cross-platform mobile"],
    "agile": ["scrum", "kanban", "sprint planning"],
    "mysql": ["sql", "database", "relational database"],
    "flask": ["python web framework"],
    "figma": ["wireframing", "prototyping"],
    "jira": ["issue tracking", "project tracking"],
    # Creative / design tool short forms
    "adobe illustrator": ["illustrator"],
    "adobe photoshop":   ["photoshop"],
    "adobe indesign":    ["indesign"],
    "adobe premiere":    ["premiere pro", "premiere"],
    "adobe after effects": ["after effects", "ae"],
    "adobe xd":          ["xd"],
    # QA / testing
    "test automation":   ["automation", "automated testing", "automation testing", "test scripts"],
    "selenium":          ["selenium webdriver"],
    "api testing":       ["postman", "rest api testing"],
    # Cloud / infra short forms
    "kubernetes":        ["k8s"],
    "terraform":         ["infrastructure as code", "iac"],
    "ci/cd":             ["continuous integration", "continuous delivery", "continuous deployment",
                          "github actions", "jenkins", "gitlab ci"],
    # Networking
    "networking":        ["tcp/ip", "network administration", "network infrastructure"],
}

# Build a reverse lookup so every term (canonical + alias) maps to the full
# set of terms it is synonymous with.  A term that appears in multiple
# SKILL_SYNONYMS entries gets all groups merged (union), so one resume skill
# can partially match several different job skills.
_SYNONYM_GROUPS: dict[str, set[str]] = {}
for _canonical, _aliases in SKILL_SYNONYMS.items():
    _group = {_canonical.lower()} | {a.lower() for a in _aliases}
    for _term in _group:
        if _term in _SYNONYM_GROUPS:
            _SYNONYM_GROUPS[_term] = _SYNONYM_GROUPS[_term] | _group
        else:
            _SYNONYM_GROUPS[_term] = _group.copy()


# ── Role-based skill inference for vague job descriptions ────────────
# When a job description is too short / generic (e.g. "junior software
# engineer at a tech company"), the system infers expected skills from
# role keywords so the matching engine has something to work with.
ROLE_SKILL_TEMPLATES: dict[str, list[str]] = {
    # Technology / Engineering roles
    "software engineer": [
        "python", "javascript", "java", "sql", "git", "rest api",
        "agile", "problem solving", "communication", "teamwork",
    ],
    "software developer": [
        "python", "javascript", "java", "sql", "git", "rest api",
        "agile", "problem solving", "communication", "teamwork",
    ],
    "web developer": [
        "html", "css", "javascript", "react", "node.js", "sql",
        "git", "rest api", "problem solving", "communication",
    ],
    "frontend developer": [
        "html", "css", "javascript", "typescript", "react", "git",
        "figma", "rest api", "problem solving", "communication",
    ],
    "backend developer": [
        "python", "java", "sql", "rest api", "git", "docker",
        "postgresql", "agile", "problem solving", "communication",
    ],
    "full stack developer": [
        "javascript", "python", "react", "node.js", "sql", "git",
        "html", "css", "rest api", "docker",
    ],
    "data scientist": [
        "python", "sql", "machine learning", "data analysis", "pandas",
        "numpy", "tensorflow", "data science", "communication", "problem solving",
    ],
    "data analyst": [
        "sql", "excel", "python", "data analysis", "tableau",
        "power bi", "communication", "problem solving", "analytical skills",
    ],
    "data engineer": [
        "python", "sql", "aws", "docker", "postgresql", "mongodb",
        "data analysis", "git", "linux", "agile",
    ],
    "devops engineer": [
        "docker", "kubernetes", "aws", "linux", "git", "ci/cd",
        "terraform", "python", "bash", "jenkins",
    ],
    "cloud engineer": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "linux", "python", "ci/cd", "git",
    ],
    "mobile developer": [
        "react native", "flutter", "javascript", "typescript", "ios",
        "android", "git", "rest api", "agile", "problem solving",
    ],
    "machine learning engineer": [
        "python", "machine learning", "tensorflow", "pytorch", "sql",
        "deep learning", "data science", "git", "docker", "numpy",
    ],
    "ai developer": [
        "python", "machine learning", "deep learning", "tensorflow",
        "pytorch", "computer vision", "nlp", "data science", "numpy",
        "pandas", "opencv", "scikit-learn", "sql", "git", "docker",
        "rest api", "agile", "problem solving", "communication",
    ],
    "ai researcher": [
        "python", "machine learning", "deep learning", "tensorflow",
        "pytorch", "nlp", "computer vision", "data science", "numpy",
        "pandas", "scikit-learn", "research", "writing", "git",
    ],
    "computer vision engineer": [
        "python", "computer vision", "opencv", "tensorflow", "pytorch",
        "deep learning", "machine learning", "numpy", "docker", "git",
        "linux", "data science", "problem solving", "communication",
    ],
    "nlp engineer": [
        "python", "nlp", "machine learning", "deep learning",
        "tensorflow", "pytorch", "data science", "sql", "git",
        "docker", "communication", "problem solving",
    ],
    "qa engineer": [
        "python", "javascript", "sql", "git", "agile", "jira",
        "rest api", "problem solving", "communication", "teamwork",
    ],
    "cybersecurity analyst": [
        "linux", "python", "sql", "bash", "git", "communication",
        "problem solving", "analytical skills", "teamwork",
    ],
    "it support": [
        "linux", "microsoft office", "communication", "customer service",
        "problem solving", "teamwork", "excel", "teams",
    ],
    # Business / Management roles
    "business analyst": [
        "excel", "sql", "data analysis", "communication", "project management",
        "power bi", "stakeholder management", "problem solving", "presentation",
    ],
    "project manager": [
        "project management", "agile", "scrum", "jira", "communication",
        "leadership", "stakeholder management", "excel", "presentation",
    ],
    "product manager": [
        "agile", "data analysis", "communication", "leadership",
        "project management", "stakeholder management", "presentation",
        "problem solving", "strategic planning",
    ],
    "management consultant": [
        "communication", "presentation", "excel", "powerpoint",
        "data analysis", "problem solving", "project management",
        "leadership", "strategic planning", "teamwork",
    ],
    # Marketing / Creative roles
    "marketing manager": [
        "digital marketing", "social media", "seo", "google ads",
        "content marketing", "communication", "excel", "canva",
        "data analysis", "crm",
    ],
    "graphic designer": [
        "adobe photoshop", "adobe illustrator", "figma", "canva",
        "graphic design", "ui/ux design", "communication", "creativity",
    ],
    "ui/ux designer": [
        "figma", "adobe photoshop", "ui/ux design", "html", "css",
        "communication", "problem solving", "research", "presentation",
    ],
    # Finance / Accounting roles
    "accountant": [
        "accounting", "excel", "financial reporting", "bookkeeping",
        "tax preparation", "auditing", "communication", "attention to detail",
    ],
    "financial analyst": [
        "excel", "financial analysis", "financial modeling", "sql",
        "data analysis", "powerpoint", "communication", "budgeting",
    ],
    # Healthcare
    "registered nurse": [
        "patient care", "medical records", "first aid", "cpr",
        "communication", "teamwork", "attention to detail",
    ],
    # Hospitality
    "hotel front desk agent": [
        "customer service", "communication", "microsoft office",
        "reservation systems", "front desk", "guest relations",
        "problem solving", "teamwork", "multitasking",
        "hospitality management", "guest satisfaction",
    ],
    # Administrative / General
    "administrative assistant": [
        "microsoft office", "excel", "communication", "organizational skills",
        "time management", "customer service", "data entry", "teams",
    ],
    "customer service representative": [
        "customer service", "communication", "problem solving", "crm",
        "teamwork", "microsoft office", "multitasking", "attention to detail",
    ],
}

# ── Merge trained role templates into ROLE_SKILL_TEMPLATES ────────
# Add data-driven templates for roles not already covered
for _role, _skills in TRAINED_ROLE_SKILL_TEMPLATES.items():
    if _role not in ROLE_SKILL_TEMPLATES:
        # Filter out noisy skills like "less" (CSS less vs. word "less"),
        # "windows" (too generic), "go" (ambiguous)
        _noisy = {"less", "windows", "go", "teams", "assembly", "transformer"}
        _cleaned = [s for s in _skills if s not in _noisy]
        if len(_cleaned) >= 3:
            ROLE_SKILL_TEMPLATES[_role] = _cleaned
    else:
        # For existing roles, supplement with any trained skills not present
        _existing = set(s.lower() for s in ROLE_SKILL_TEMPLATES[_role])
        _noisy = {"less", "windows", "go", "teams", "assembly", "transformer"}
        for _skill in _skills:
            if _skill not in _noisy and _skill.lower() not in _existing:
                ROLE_SKILL_TEMPLATES[_role].append(_skill)
                _existing.add(_skill.lower())

del _role, _skills, _noisy, _cleaned, _existing, _skill

# Keyword fragments → template key mapping for fuzzy role detection
_ROLE_KEYWORD_MAP: list[tuple[list[str], str]] = [
    (["software engineer"], "software engineer"),
    (["software develop"], "software developer"),
    # Generic CS / programming JDs (e.g. "computer science summer
    # internship", "computer science graduate role") fall back to the
    # software engineer template so the matcher has a meaningful skill
    # surface instead of returning the empty set and producing a
    # degenerate score.
    (["computer science", "computer engineer", "comp sci", "cs intern",
      "cs internship", "programming intern"], "software engineer"),
    (["web develop"], "web developer"),
    (["frontend", "front end", "front-end"], "frontend developer"),
    (["backend", "back end", "back-end"], "backend developer"),
    (["full stack", "fullstack", "full-stack"], "full stack developer"),
    (["data scien"], "data scientist"),
    (["data analy"], "data analyst"),
    (["data engineer"], "data engineer"),
    (["devops", "dev ops", "site reliability"], "devops engineer"),
    (["cloud engineer", "cloud architect"], "cloud engineer"),
    (["mobile develop", "app develop"], "mobile developer"),
    (["artificial intelligence", "ai develop", "ai program"], "ai developer"),
    (["ai research", "machine learning research"], "ai researcher"),
    (["computer vision"], "computer vision engineer"),
    (["nlp engineer", "natural language"], "nlp engineer"),
    (["machine learning", "ml engineer", "ai engineer", "ml develop"], "machine learning engineer"),
    (["qa ", "quality assurance", "test engineer"], "qa engineer"),
    (["cyber", "security analyst", "infosec"], "cybersecurity analyst"),
    (["it support", "helpdesk", "help desk", "tech support"], "it support"),
    (["business analyst"], "business analyst"),
    (["project manag"], "project manager"),
    (["product manag"], "product manager"),
    (["consult"], "management consultant"),
    (["market"], "marketing manager"),
    (["graphic design"], "graphic designer"),
    (["ui/ux", "ux design", "ui design"], "ui/ux designer"),
    (["account"], "accountant"),
    (["financial analyst", "finance analyst"], "financial analyst"),
    (["nurs"], "registered nurse"),
    (["front desk", "receptionist", "hotel", "hospitality"], "hotel front desk agent"),
    (["admin assistant", "administrative", "secretary", "office assistant"], "administrative assistant"),
    (["customer service", "customer support", "call center", "call centre"], "customer service representative"),
    # ── Trained role keyword mappings (from Kaggle dataset) ───────
    (["java develop"], "java developer"),
    (["python develop"], "python developer"),
    (["dotnet", ".net develop", "c# develop"], "dotnet developer"),
    (["big data", "hadoop", "spark engineer"], "big data engineer"),
    (["blockchain", "web3", "smart contract"], "blockchain developer"),
    (["database admin", "dba", "database engineer"], "database administrator"),
    (["etl", "data pipeline", "data warehouse"], "etl developer"),
    (["sap develop", "sap consult"], "sap developer"),
    (["network security", "network engineer"], "network security engineer"),
    (["test automation", "automation test", "sdet"], "test automation engineer"),
    (["mechanical engineer"], "mechanical engineer"),
    (["electrical engineer"], "electrical engineer"),
    (["civil engineer"], "civil engineer"),
    (["human resource", "hr ", "hr manag"], "hr manager"),
    (["sales ", "sales represent", "account executive"], "sales representative"),
    (["operations manag"], "operations manager"),
    (["web design"], "web developer"),
    (["health", "fitness", "wellness"], "health and fitness professional"),
    (["legal", "advocate", "lawyer", "attorney"], "lawyer"),
]

# ── Merge trained keyword mappings ────────────────────────────────
# Only add mappings for roles that exist in ROLE_SKILL_TEMPLATES
# and whose keywords aren't already covered by the base map.
_existing_targets = {target for _, target in _ROLE_KEYWORD_MAP}
for _keywords, _role in TRAINED_ROLE_KEYWORD_MAP:
    if _role in ROLE_SKILL_TEMPLATES and _role not in _existing_targets:
        _ROLE_KEYWORD_MAP.append((_keywords, _role))
        _existing_targets.add(_role)
del _existing_targets, _keywords, _role


def infer_skills_from_role(text: str) -> list[str]:
    """Infer expected skills when the job description is too vague.

    Scans the text for role-related keywords and returns a list of
    expected skills from the matching ROLE_SKILL_TEMPLATES entry.

    Returns an empty list if no role can be detected.
    """
    text_lower = text.lower()
    for keywords, template_key in _ROLE_KEYWORD_MAP:
        for kw in keywords:
            if kw in text_lower:
                return list(ROLE_SKILL_TEMPLATES[template_key])
    return []


# ─────────────────────────────────────────────────────────────────────────────
#  Semantic skill recovery (bi-encoder cosine).
#
#  The rule-based matcher + synonym lookup handles literal skill names well.
#  Where it fails is *indirect phrasing*: a resume that says "designed ETL
#  pipelines for a 5B-row warehouse" won't be picked up for a JD requiring
#  "Data Engineering" unless the dictionary happens to link those strings.
#
#  This function plugs that gap.  For each missing JD skill we embed it
#  alongside the resume's prose sentences using the same sentence-transformer
#  bi-encoder that drives the rest of the ML pipeline (all-MiniLM-L6-v2,
#  384-dim), and recover any skill whose best-matching sentence clears a
#  cosine-similarity threshold.
#
#  Why bi-encoder rather than cross-encoder: we prototyped ms-marco and
#  stsb-distilroberta cross-encoders first.  On our calibration set
#  (hand-crafted (skill, sentence) pairs with known verdicts) the MS-MARCO
#  model couldn't separate relevant paraphrases (~-11 logits) from
#  irrelevant pairs (~-11 logits) — it's trained for QA-style queries,
#  not short asymmetric skill lookups.  STS-B was too heavy on CPU.  The
#  bi-encoder gave a clean 0.20-0.40 (relevant) vs 0.08-0.11 (irrelevant)
#  separation on the same pairs, so that's what we ship.  The "cross-encoder"
#  framing in commit history was a design exploration — bi-encoder cosine
#  turned out to be the right tool.
#
#  Failure modes are all fail-soft: model-load error, offline environment,
#  or any exception during rerank → empty recovery → zero correction.
# ─────────────────────────────────────────────────────────────────────────────

# Module-level lazy singleton.  The existing MLMatcher class loads its own
# instance per object, but this helper is called from matcher.py outside
# that class — we load once per process here and reuse.
_BIENCODER: Optional[object] = None
_BIENCODER_NAME = 'all-MiniLM-L6-v2'


def _get_biencoder():
    """Lazy-load and cache the bi-encoder used for semantic recovery."""
    global _BIENCODER
    if _BIENCODER is None:
        try:
            _BIENCODER = SentenceTransformer(_BIENCODER_NAME)
        except Exception:
            _BIENCODER = False     # sentinel: don't retry on every call
    return _BIENCODER or None


# Split resume text into candidate sentences for matching.  Simple regex
# split — we don't need linguistic correctness, just a pool of short-to-
# medium prose chunks.  Filter bullets that are too short to carry
# semantic content ("Python", "Git") — those are handled by keyword match.
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+|[•\-\*]\s+')


def _candidate_sentences(resume_text: str, max_sentences: int = 80) -> List[str]:
    """Produce a bounded pool of resume sentences for matching."""
    if not resume_text:
        return []
    raw = _SENTENCE_SPLIT.split(resume_text)
    out: List[str] = []
    for s in raw:
        s = s.strip()
        # Drop headers and very-short bullets; keep real prose.
        if len(s.split()) < 4:
            continue
        out.append(s)
        if len(out) >= max_sentences:
            break
    return out


# Cosine threshold tuned against a hand-crafted calibration set of
# (skill, resume sentence) pairs — relevant pairs scored 0.198-0.395,
# irrelevant pairs scored -0.033-0.105.  0.18 gives zero false positives
# and high recall on the calibration set; re-tune if the eval harness
# says otherwise.
_SEMANTIC_THRESHOLD = 0.18
_MAX_MISSING_RERANK = 15      # latency cap: only rerank the top N missing


# ─────────────────────────────────────────────────────────────────────────────
#  Kindred-skill families: paraphrase recovery for any skill in a family is
#  gated on the resume showing at least one EXPLICIT (dictionary-matched)
#  member of that family. This stops the bi-encoder from hallucinating
#  Python / SQL / Git matches in a Business & Management CV that mentions
#  generic prose like "promoted Zoom webinars" or "cash management system".
#  Soft skills (Communication, Teamwork, etc.) deliberately have no family
#  guard — they recover from prose evidence as before.
# ─────────────────────────────────────────────────────────────────────────────
_KINDRED_FAMILIES: Dict[str, set[str]] = {
    'programming': {
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
        'go', 'rust', 'kotlin', 'swift', 'scala', 'r', 'php', 'matlab',
        'perl', 'objective-c', 'dart',
    },
    'web': {
        'html', 'css', 'javascript', 'typescript', 'react', 'angular',
        'vue', 'vue.js', 'node.js', 'next.js', 'svelte', 'jquery',
        'rest api', 'graphql', 'webpack',
    },
    'ml': {
        'machine learning', 'deep learning', 'tensorflow', 'pytorch',
        'keras', 'scikit-learn', 'opencv', 'nlp', 'computer vision',
        'data science', 'pandas', 'numpy', 'matplotlib',
    },
    'devops': {
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform',
        'ansible', 'ci/cd', 'jenkins', 'github actions', 'cloudformation',
        'helm', 'prometheus', 'grafana',
    },
    'database': {
        'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis',
        'oracle', 'sqlite', 'cassandra', 'dynamodb', 'snowflake',
    },
    'testing': {
        'pytest', 'junit', 'selenium', 'jest', 'mocha', 'cypress',
        'unit testing', 'integration testing', 'qa', 'testing',
    },
    'version_control': {
        'git', 'github', 'gitlab', 'bitbucket', 'svn',
    },
    # "software practice" terms — agile, scrum, code review, CI/CD — are
    # inseparable from professional software work. The guard treats a skill
    # in this family as recoverable only when the resume shows explicit
    # evidence in one of the *technical* families (programming, web, ml,
    # devops, database, testing, version_control). Without this gate, the
    # bi-encoder happily promotes "Agile" / "Code Review" into a Business
    # & Management CV that mentions "managed retail systems".
    'software_practice': {
        'agile', 'scrum', 'kanban', 'code review', 'pair programming',
        'tdd', 'bdd', 'ci/cd', 'devops', 'continuous integration',
        'continuous deployment',
    },
}

# Names of the technical "anchor" families. A skill in `software_practice`
# (which has no anchors of its own) is allowed only when the resume has
# explicit evidence in any of these.
_TECHNICAL_ANCHOR_FAMILIES = {
    'programming', 'web', 'ml', 'devops', 'database',
    'testing', 'version_control',
}

# Reverse index: skill (lower) → family name(s) it belongs to.
_SKILL_TO_FAMILIES: Dict[str, set[str]] = {}
for _fam, _members in _KINDRED_FAMILIES.items():
    for _m in _members:
        _SKILL_TO_FAMILIES.setdefault(_m, set()).add(_fam)


def _kindred_guard_passes(skill: str, explicit_skills_lower: set[str]) -> bool:
    """Return True iff paraphrase recovery should be allowed for ``skill``.

    A technical skill (one that belongs to a defined family) is only
    recoverable via paraphrase when the resume already has at least ONE
    explicitly-listed skill from the same family. Skills that aren't
    flagged as technical (soft skills, generic terms) are always allowed.

    Special case: ``software_practice`` skills (agile, scrum, code review,
    CI/CD) require evidence in any *technical* anchor family — they're
    practice terms that mean nothing outside an engineering context.
    """
    families = _SKILL_TO_FAMILIES.get(skill.lower())
    if not families:
        return True  # not a guarded family — allow as before
    for fam in families:
        if explicit_skills_lower & _KINDRED_FAMILIES[fam]:
            return True
    # software_practice ⇒ also accept anchor-family evidence.
    if 'software_practice' in families:
        for anchor in _TECHNICAL_ANCHOR_FAMILIES:
            if explicit_skills_lower & _KINDRED_FAMILIES[anchor]:
                return True
    return False


def rerank_missing_skills(
    missing_skills: List[str],
    resume_text: str,
    explicit_skills: Optional[List[str]] = None,
) -> Dict[str, float]:
    """Return {skill: best_cosine_score} for semantically-demonstrated skills.

    Pipeline:
      1. Split the resume into candidate sentences.
      2. Embed sentences + missing skills once via the bi-encoder.
      3. For each missing skill, take the max cosine similarity across
         all sentences.
      4. Keep skills whose max ≥ ``_SEMANTIC_THRESHOLD`` AND that pass the
         kindred-skill guard (when ``explicit_skills`` is provided).

    All failures return ``{}`` so the caller transparently falls back to
    the rule-based behaviour.  Workload is capped by ``_MAX_MISSING_RERANK``.

    The ``explicit_skills`` argument enables type-guarding: a technical
    skill like "Python" is only recovered when the resume shows at least
    one explicit programming-language match. Without it, the bi-encoder
    happily promotes Python/SQL/Git matches in a Business & Management CV
    that says "managed retail systems" — see _kindred_guard_passes.
    """
    if not missing_skills or not resume_text:
        return {}

    bi = _get_biencoder()
    if bi is None:
        return {}

    try:
        sentences = _candidate_sentences(resume_text)
        if not sentences:
            return {}

        # Bound the workload: rerank only the first N missing skills.
        todo = missing_skills[:_MAX_MISSING_RERANK]

        # Kindred-skill guard: drop skills whose family has no explicit
        # representative in the resume. This must happen BEFORE the embed
        # so we don't waste compute on guaranteed rejects.
        explicit_lower = {s.lower() for s in (explicit_skills or [])}
        if explicit_skills is not None:
            todo = [s for s in todo if _kindred_guard_passes(s, explicit_lower)]
            if not todo:
                return {}

        # One-shot encode of both sides.
        sent_emb  = bi.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
        skill_emb = bi.encode(todo,      convert_to_numpy=True, show_progress_bar=False)

        # Cosine: (len(todo) × len(sentences)) matrix.  Max along the
        # sentence axis gives each skill's best match.
        sims = cosine_similarity(skill_emb, sent_emb)
        best_per_skill = sims.max(axis=1)

        # Threshold.
        return {
            todo[i]: float(best_per_skill[i])
            for i in range(len(todo))
            if best_per_skill[i] >= _SEMANTIC_THRESHOLD
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
#  ML safety net #1: scan the resume for skills the keyword matcher missed.
#
#  The rule pipeline already does two things:
#    (a) extract_skills() — exact dictionary lookup
#    (b) _infer_implicit_skills() — regex implication graph
#
#  Both are precise but recall-limited. A resume that says "Built a service
#  in Spring Boot exposing JSON endpoints" gets Spring Boot from (a) and
#  REST API from (b) — but a resume saying "Wrote the gateway in Go and
#  hooked it into Kafka" misses Go AND microservices because neither phrasing
#  hits a dictionary entry or an implication regex.
#
#  This pass embeds every skill in the union of role templates and the resume
#  prose, then promotes any skill whose best matching sentence clears a
#  conservative threshold (0.32 — much higher than the 0.18 used for JD-side
#  rerank, since here we sweep a much wider candidate surface).
# ─────────────────────────────────────────────────────────────────────────────

# Common skill surface = union of every skill across every role template.
# Cached on first call. Re-evaluating per request is cheap (~50 µs) but the
# embedding pass below is expensive without caching.
_RESUME_RECOVERY_THRESHOLD = 0.32   # tuned against a small hold-out
_RESUME_RECOVERY_MAX       = 8      # at most this many recoveries per resume
_COMMON_SKILL_EMB_CACHE: Optional[tuple] = None   # (skills_list, embeddings)


def _get_common_skill_embeddings():
    """Return (skills, embeddings) — embed every skill in the union of role
    templates exactly once per process. Cached forever after first call.
    """
    global _COMMON_SKILL_EMB_CACHE
    if _COMMON_SKILL_EMB_CACHE is not None:
        return _COMMON_SKILL_EMB_CACHE

    bi = _get_biencoder()
    if bi is None:
        _COMMON_SKILL_EMB_CACHE = ([], None)
        return _COMMON_SKILL_EMB_CACHE

    skill_set: set[str] = set()
    for tpl in ROLE_SKILL_TEMPLATES.values():
        for s in tpl:
            skill_set.add(s.lower())
    skills = sorted(skill_set)

    try:
        emb = bi.encode(skills, convert_to_numpy=True, show_progress_bar=False)
    except Exception:
        _COMMON_SKILL_EMB_CACHE = ([], None)
        return _COMMON_SKILL_EMB_CACHE

    _COMMON_SKILL_EMB_CACHE = (skills, emb)
    return _COMMON_SKILL_EMB_CACHE


def recover_skills_from_resume(
    resume_text: str,
    explicit_skills: List[str],
) -> List[str]:
    """ML safety net: detect skills demonstrated in resume prose that the
    keyword matcher and the implication graph both missed.

    Returns up to ``_RESUME_RECOVERY_MAX`` title-cased skill names. Never
    returns duplicates of ``explicit_skills``. Fail-soft: any error (model
    load, embedding, cosine) returns an empty list so the caller falls
    back to the rule-based behaviour transparently.
    """
    if not resume_text:
        return []

    skills, skill_emb = _get_common_skill_embeddings()
    if not skills or skill_emb is None:
        return []

    bi = _get_biencoder()
    if bi is None:
        return []

    try:
        sentences = _candidate_sentences(resume_text)
        if not sentences:
            return []

        sent_emb = bi.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
        sims = cosine_similarity(skill_emb, sent_emb)        # |skills| × |sent|
        best = sims.max(axis=1)

        explicit_lower = {s.lower() for s in explicit_skills}

        # Rank candidate skills by their best cosine; promote those that clear
        # the threshold and aren't already in the explicit list.
        ranked = sorted(
            range(len(skills)),
            key=lambda i: -best[i],
        )

        promoted: List[str] = []
        for i in ranked:
            if best[i] < _RESUME_RECOVERY_THRESHOLD:
                break
            sk = skills[i]
            if sk in explicit_lower:
                continue
            # Kindred-skill guard: don't promote a technical skill into
            # a CV that has no explicit member of its family. Avoids the
            # bi-encoder hallucinating Python/SQL/Git in non-technical
            # business CVs that contain only generic prose.
            if not _kindred_guard_passes(sk, explicit_lower):
                continue
            promoted.append(sk.title())
            if len(promoted) >= _RESUME_RECOVERY_MAX:
                break
        return promoted
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
#  ML safety net #2: when a JD falls through every keyword router, ask the
#  bi-encoder which role profile it semantically resembles most.
#
#  Used as the LAST fallback after extract_keywords_from_job_description has
#  tried (a) literal extraction, (b) infer_skills_from_role keyword match.
#  Without this, a JD like "Build internal dashboards for the marketing team"
#  produces zero skills because none of the keyword routers fire.
# ─────────────────────────────────────────────────────────────────────────────

_JD_ROLE_THRESHOLD          = 0.28   # tuned: 0.30 cut off legitimate
                                     # matches like "build dashboards with
                                     # SQL" → analytics engineer (0.286).
_ROLE_TEMPLATE_EMB_CACHE: Optional[tuple] = None  # (role_keys, embeddings)


def _get_role_template_embeddings():
    """Embed each role template's "title + skills" string once per process.

    The embedded text is a short blob like:
        "software engineer. typical skills: python, javascript, java, sql, git"
    That fingerprints both the role name and its skill surface, giving the
    bi-encoder enough signal to pick the closest match for an unfamiliar JD.
    """
    global _ROLE_TEMPLATE_EMB_CACHE
    if _ROLE_TEMPLATE_EMB_CACHE is not None:
        return _ROLE_TEMPLATE_EMB_CACHE

    bi = _get_biencoder()
    if bi is None:
        _ROLE_TEMPLATE_EMB_CACHE = ([], None)
        return _ROLE_TEMPLATE_EMB_CACHE

    role_keys = list(ROLE_SKILL_TEMPLATES.keys())
    blobs = [
        f"{key}. typical skills: {', '.join(ROLE_SKILL_TEMPLATES[key])}"
        for key in role_keys
    ]
    try:
        emb = bi.encode(blobs, convert_to_numpy=True, show_progress_bar=False)
    except Exception:
        _ROLE_TEMPLATE_EMB_CACHE = ([], None)
        return _ROLE_TEMPLATE_EMB_CACHE

    _ROLE_TEMPLATE_EMB_CACHE = (role_keys, emb)
    return _ROLE_TEMPLATE_EMB_CACHE


def find_closest_role_profile(
    jd_text: str,
) -> tuple[Optional[List[str]], Optional[str], float]:
    """Return (skill_list, role_key, confidence) for the closest semantic
    match in ROLE_SKILL_TEMPLATES.

    Returns (None, None, 0.0) when nothing clears ``_JD_ROLE_THRESHOLD`` or
    when the bi-encoder is unavailable. The caller decides whether to use
    the result; this function is best-effort.
    """
    if not jd_text or not jd_text.strip():
        return None, None, 0.0

    role_keys, role_emb = _get_role_template_embeddings()
    if not role_keys or role_emb is None:
        return None, None, 0.0

    bi = _get_biencoder()
    if bi is None:
        return None, None, 0.0

    try:
        jd_emb = bi.encode([jd_text], convert_to_numpy=True, show_progress_bar=False)
        sims = cosine_similarity(jd_emb, role_emb)[0]    # length = |roles|
        best_i = int(sims.argmax())
        best_sim = float(sims[best_i])
        if best_sim < _JD_ROLE_THRESHOLD:
            return None, None, best_sim
        role_key = role_keys[best_i]
        return list(ROLE_SKILL_TEMPLATES[role_key]), role_key, best_sim
    except Exception:
        return None, None, 0.0


def get_role_profile(text: str) -> dict | None:
    """Detect the role from job description text and return its tiered skill profile.

    Resolution order:
      1. Hand-curated profile via ROLE_PROFILE_KEYWORDS (50 roles) — highest
         quality, always preferred when it matches.
      2. Inherited profile via role_inheritance.get_inherited_profile() — any
         role in _ROLE_KEYWORD_MAP that has a nominated parent in
         ROLE_PARENT_MAP.  Synthesises core/expected/advanced tiers from the
         parent's profile + the child's flat template.
      3. None — caller falls back to flat scoring.
    """
    text_lower = text.lower()

    # 1. Direct profile match (the 50 curated roles).
    for keywords, profile_key in ROLE_PROFILE_KEYWORDS:
        for kw in keywords:
            if kw in text_lower:
                return ROLE_SKILL_PROFILES.get(profile_key)

    # 2. Inherited profile for roles with a flat template but no curated
    #    profile of their own (~100 additional roles).
    from .role_inheritance import get_inherited_profile
    for keywords, template_key in _ROLE_KEYWORD_MAP:
        for kw in keywords:
            if kw in text_lower:
                # Some _ROLE_KEYWORD_MAP shortcuts (e.g. "nurs" → "registered
                # nurse", "mechanical engineer" → "mechanical engineer") point
                # at a template key that is ALSO a profiled role.  In that
                # case skip inheritance and return the real profile directly —
                # otherwise get_inherited_profile returns None (the
                # "parent itself" guard) and detection falls to flat scoring.
                if template_key in ROLE_SKILL_PROFILES:
                    return ROLE_SKILL_PROFILES[template_key]
                inherited = get_inherited_profile(
                    template_key, ROLE_SKILL_TEMPLATES, ROLE_SKILL_PROFILES,
                )
                if inherited is not None:
                    return inherited
                # No parent nominated — give up rather than guess.
                return None

    return None


def parse_jd_tiers(jd_text: str) -> dict[str, List[str]]:
    """
    Split a job description into required vs preferred skill groups.

    Handles three common JD formats:
      1. Sectioned  — "Requirements:\\n- Python\\n\\nNice to have:\\n- Spark"
      2. Inline     — "Must have Python and SQL.  Spark is preferred."
      3. Unlabelled — no signals found; everything treated as unclassified
                      (→ scored as required, preserving backward-compatibility).

    Returns:
        {
          'required':     list[str],  # missing these = full penalty
          'preferred':    list[str],  # matching these = bonus; missing = no penalty
          'unclassified': list[str],  # no signal found → treated as required in scoring
        }
    """
    # ── Section-header detectors ────────────────────────────────────────────
    _REQ_HEADER = re.compile(
        r'^\s*(?:[•\-\*–·]\s*)?'
        r'(?:requirements?|must[- ]have|essential[s]?|mandatory'
        r'|minimum qualifications?|what you(?:\'ll)? need'
        r'|you(?:\'ll)? (?:have|bring|need)|must possess'
        r'|hard requirements?|required qualifications?|required skills?'
        r'|key requirements?|core requirements?)'
        # Allow " / …", " - …", " (…)" suffixes before the colon so that
        # compound headers like "Requirements / Must have:" still match.
        r'(?:\s*[/|\-–]\s*[\w][\w\s\-]*?)?\s*[:\-]?\s*$',
        re.IGNORECASE,
    )
    _PREF_HEADER = re.compile(
        r'^\s*(?:[•\-\*–·]\s*)?'
        r'(?:preferred|nice[- ]to[- ]have|bonus|desirable|advantageous'
        r'|good to have|ideally|beneficial|would be (?:a )?plus'
        r'|not required but|extra credit|preferred qualifications?'
        r'|preferred skills?|nice to haves?|great to have'
        r'|we(?:\'d)? love if you have)'
        # Allow " / …", " - …" suffixes so that "Preferred / Nice to have:"
        # and similar compound headers are recognised.
        r'(?:\s*[/|\-–]\s*[\w][\w\s\-]*?)?\s*[:\-]?\s*$',
        re.IGNORECASE,
    )

    # ── Inline-signal detectors ─────────────────────────────────────────────
    _REQ_INLINE = re.compile(
        r'\b(?:required|mandatory|essential|must[- ]have|must possess)\b',
        re.IGNORECASE,
    )
    _PREF_INLINE = re.compile(
        r'\b(?:preferr?ed?|nice[- ]to[- ]have|bonus|desirable|ideally?'
        r'|advantageous|would be (?:a )?plus|good to have)\b',
        re.IGNORECASE,
    )

    req_lines:  List[str] = []
    pref_lines: List[str] = []
    uncl_lines: List[str] = []
    current_section = 'unclassified'

    for line in jd_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # 1. Section header → switch mode
        if _REQ_HEADER.match(stripped):
            current_section = 'required'
            continue
        if _PREF_HEADER.match(stripped):
            current_section = 'preferred'
            continue

        # 2. Long non-bulleted paragraph → reset to unclassified
        is_bullet = stripped[:1] in ('•', '-', '*', '–', '·')
        if not is_bullet and len(stripped.split()) > 12 and current_section != 'unclassified':
            current_section = 'unclassified'

        # 3. Route to bucket
        if current_section == 'required':
            req_lines.append(stripped)
        elif current_section == 'preferred':
            pref_lines.append(stripped)
        else:
            # Check preferred BEFORE required: "preferred but not mandatory" must
            # route to preferred even though "mandatory" also appears on the line.
            if _PREF_INLINE.search(stripped):
                pref_lines.append(stripped)
            elif _REQ_INLINE.search(stripped):
                req_lines.append(stripped)
            else:
                uncl_lines.append(stripped)

    # ── Extract skills from each bucket ────────────────────────────────────
    req_skills  = extract_skills('\n'.join(req_lines))  if req_lines  else []
    pref_skills = extract_skills('\n'.join(pref_lines)) if pref_lines else []
    uncl_skills = extract_skills('\n'.join(uncl_lines)) if uncl_lines else []

    # Deduplicate across buckets (priority: required > unclassified > preferred)
    seen: set[str] = set()

    def _dedup(lst: List[str]) -> List[str]:
        out = []
        for s in lst:
            k = s.lower()
            if k not in seen:
                seen.add(k)
                out.append(s)
        return out

    req_skills  = _dedup(req_skills)
    uncl_skills = _dedup(uncl_skills)
    pref_skills = _dedup(pref_skills)

    return {
        'required':     req_skills,
        'preferred':    pref_skills,
        'unclassified': uncl_skills,
        # Raw text per bucket — callers can run raw-token extraction on each
        # to catch skills that aren't in SKILL_DICTIONARY (e.g. Figma, Retool).
        'required_text':     '\n'.join(req_lines),
        'preferred_text':    '\n'.join(pref_lines),
        'unclassified_text': '\n'.join(uncl_lines),
    }


# ── Raw JD token extraction — catches "invisible" skills ────────────────────
# Words that look like skill tokens (all-caps, CamelCase, special chars) but
# are actually noise — English words, role nouns, pronouns, etc.
_RAW_TOKEN_NOISE: set[str] = {
    # Pronouns / articles / prepositions (in caps)
    'the', 'and', 'or', 'but', 'if', 'for', 'with', 'from', 'to', 'of', 'in',
    'on', 'at', 'by', 'an', 'as', 'is', 'are', 'be', 'was', 'were', 'will',
    'we', 'you', 'i', 'he', 'she', 'they', 'us', 'our', 'your', 'their',
    'who', 'what', 'when', 'where', 'why', 'how', 'this', 'that', 'these',
    'those', 'which', 'all', 'any', 'each', 'some', 'many', 'most', 'other',
    # Modals / auxiliaries
    'can', 'may', 'should', 'would', 'could', 'must', 'might', 'shall',
    # Common JD nouns (not skills)
    'role', 'job', 'team', 'company', 'work', 'working', 'works', 'worked',
    'day', 'week', 'month', 'year', 'years', 'time', 'times', 'hour', 'hours',
    'candidate', 'candidates', 'applicant', 'applicants', 'position', 'positions',
    'title', 'department', 'office', 'location', 'remote', 'hybrid', 'onsite',
    'salary', 'compensation', 'benefits', 'perks',
    'ability', 'skills', 'skill', 'experience', 'knowledge', 'understanding',
    'familiarity', 'proficiency', 'expertise', 'background', 'qualifications',
    'requirements', 'responsibilities', 'duties', 'tasks',
    'environment', 'industry', 'sector', 'domain', 'field',
    'project', 'projects', 'product', 'products', 'service', 'services',
    'client', 'clients', 'customer', 'customers', 'user', 'users',
    'stakeholder', 'stakeholders', 'partner', 'partners', 'vendor', 'vendors',
    'report', 'reports', 'reporting', 'meeting', 'meetings',
    # Role-title words (match role, not a skill)
    'engineer', 'engineers', 'developer', 'developers', 'manager', 'managers',
    'analyst', 'analysts', 'designer', 'designers', 'specialist', 'specialists',
    'coordinator', 'director', 'lead', 'senior', 'junior', 'mid', 'principal',
    'staff', 'architect', 'architects', 'officer', 'officers', 'executive',
    'executives', 'consultant', 'consultants', 'assistant', 'assistants',
    'intern', 'interns', 'trainee',
    # Sentence starters / connectors
    'note', 'please', 'ensure', 'include', 'about', 'overview', 'summary',
    'description', 'mission', 'vision', 'values', 'culture',
    # Very common tech-adjacent but too generic in isolation
    'tech', 'it', 'technology', 'technologies', 'tools', 'tool', 'software',
    'hardware', 'system', 'systems', 'platform', 'platforms', 'application',
    'applications', 'solution', 'solutions', 'data', 'information',
    # Numbers / months / days (as tokens)
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    # Other common
    'new', 'good', 'great', 'strong', 'excellent', 'high', 'low', 'best',
    'nice', 'must', 'have', 'has', 'had', 'need', 'needs', 'plus', 'bonus',
    'essential', 'preferred', 'required', 'mandatory', 'desirable',
    # Generic business words
    'goals', 'objectives', 'strategy', 'strategies', 'process', 'processes',
    'quality', 'performance', 'growth', 'success', 'impact',
}


def extract_raw_jd_tokens(jd_text: str, known_skills: Optional[List[str]] = None) -> List[str]:
    """
    Extract technical-looking tokens from a JD that are candidate skills —
    acronyms (AWS, GDPR), CamelCase (ReactJS, PowerBI), special-char tokens
    (C++, C#, .NET, Node.js), and Title-case words appearing in tech-signal
    contexts ("experience with X", "proficient in X").

    This catches "invisible" skills not present in SKILL_DICTIONARY so they
    can still drive scoring against the resume.

    Args:
        jd_text: Raw job description text.
        known_skills: Skills already extracted via the dictionary path —
                      excluded from the raw token list to avoid duplicates.

    Returns:
        List of candidate tokens (original casing, deduplicated).
    """
    if not jd_text or len(jd_text.strip()) < 5:
        return []

    known_lower: set[str] = {s.lower() for s in (known_skills or [])}
    tokens: list[str] = []
    seen: set[str] = set()

    def _add(tok: str) -> None:
        key = tok.lower()
        if key in seen or key in known_lower or key in _RAW_TOKEN_NOISE:
            return
        if len(tok) < 2:
            return
        # Reject pure numbers
        if tok.replace('.', '').replace('+', '').replace('#', '').isdigit():
            return
        seen.add(key)
        tokens.append(tok)

    # 1. All-caps acronyms (2–8 chars) — AWS, SQL, GDPR, HIPAA, REST, API
    for m in re.finditer(r'\b[A-Z]{2,8}\b', jd_text):
        _add(m.group())

    # 2. CamelCase / PascalCase — ReactJS, TypeScript, PowerBI, ElasticSearch
    for m in re.finditer(r'\b[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+\b', jd_text):
        _add(m.group())

    # 3. Special-char tech tokens — C++, C#, .NET, Node.js, F#, Vue.js
    for m in re.finditer(r'\b[A-Za-z][A-Za-z0-9]*[+#.][A-Za-z0-9+#.]*\b', jd_text):
        tok = m.group()
        # Require at least one letter, avoid tokens that are all punctuation
        if re.search(r'[A-Za-z]', tok) and len(tok) >= 2:
            _add(tok)

    # 4. Title-case words in tech-context ("experience with X", "using Y")
    #    Catches: Figma, Airtable, Retool, Snowflake, Kubernetes, Looker, etc.
    _CTX = re.compile(
        r'(?:experience|proficien(?:t|cy)|familiar(?:ity)?|knowledge|skilled|'
        r'expert(?:ise)?|working|work|using|use|hands[- ]on|exposure|'
        r'competent|strong|fluent|comfortable)\s+(?:in|with|of|on|using)\s+'
        # Capture a list: Token1(, Token2)(, Token3)( or/and Token4)...
        r'([A-Z][A-Za-z0-9.+#\-]+'
        r'(?:\s*(?:,|/|\bor\b|\band\b)\s*[A-Z][A-Za-z0-9.+#\-]+){0,4})',
        re.IGNORECASE,
    )
    for m in _CTX.finditer(jd_text):
        phrase = m.group(1)
        # Split on commas, slashes, " or ", " and "
        for piece in re.split(r'\s*(?:,|/|\s\bor\b\s|\s\band\b\s)\s*', phrase):
            piece = piece.strip()
            # Only accept title-case or acronym-style tokens here
            if piece and (piece[0].isupper() or any(c in piece for c in '.+#')):
                _add(piece)

    return tokens


def _are_synonyms(skill_a: str, skill_b: str) -> bool:
    """Return True if two skill names belong to the same synonym group."""
    group = _SYNONYM_GROUPS.get(skill_a.lower())
    return group is not None and skill_b.lower() in group


def extract_skills(text: str) -> List[str]:
    """
    Extract skills from text using rule-based matching against SKILL_DICTIONARY.

    Converts text to lowercase and matches multi-word and single-word phrases
    from the dictionary. Avoids partial or single-character matches.

    Args:
        text: Input text (resume or job description)

    Returns:
        List of detected skill strings (title-cased, deduplicated)
    """
    if not text or len(text.strip()) < 5:
        return []

    text_lower = text.lower()
    # Normalize punctuation to spaces for better boundary matching
    normalized = re.sub(r'[^\w\s/#+\-.]', ' ', text_lower)

    found: list[str] = []
    seen: set[str] = set()

    # Collect all skills and sort longest-first to prefer multi-word matches
    all_skills: list[str] = []
    for skills in SKILL_DICTIONARY.values():
        all_skills.extend(skills)
    all_skills.sort(key=len, reverse=True)

    for skill in all_skills:
        if len(skill) < 2:
            # Skip single-character entries (e.g. "r")
            continue

        skill_lower = skill.lower()
        if skill_lower in seen:
            continue

        if ' ' in skill_lower or '-' in skill_lower:
            # Multi-word / hyphenated: direct substring match
            if skill_lower in normalized:
                found.append(skill.title())
                seen.add(skill_lower)
        else:
            # Single-word: require word boundaries
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, normalized):
                found.append(skill.title())
                seen.add(skill_lower)

    return found


class MLMatcher:
    """
    ML-enhanced matcher with hybrid scoring system.

    Scoring Components:
    1. Rule-based skill match ratio with synonym support (60%)
    2. SentenceTransformer semantic similarity (25%)
    3. Experience alignment (15%)
    """

    # Configurable scoring weights (sum should equal 1.0)
    WEIGHTS = {
        'skill_match': 0.60,    # Structured skill match ratio (primary signal)
        'semantic': 0.25,       # Semantic similarity weight (supporting signal)
        'experience': 0.15,     # Experience alignment weight
    }

    # Adaptive-weighting presets, selected at scoring time based on how much
    # structured coverage we have.  Experience weight is kept constant so the
    # only trade-off is between "trust the dictionary" and "lean on semantics".
    #
    #   high — profile present AND JD + resume both have plenty of dict-level
    #          skills → structured signal is highly reliable, de-weight semantic
    #   low  — no profile AND very few dict-level JD skills → structural signal
    #          is thin, lean on semantic similarity instead
    #   baseline — everything else; matches the default WEIGHTS above
    ADAPTIVE_WEIGHTS = {
        'high':     {'skill_match': 0.70, 'semantic': 0.15, 'experience': 0.15},
        'baseline': {'skill_match': 0.60, 'semantic': 0.25, 'experience': 0.15},
        'low':      {'skill_match': 0.40, 'semantic': 0.45, 'experience': 0.15},
    }
    
    # Experience-related keyword patterns for alignment scoring
    EXPERIENCE_PATTERNS = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'(\d+)\+?\s*years?\s+(?:of\s+)?(?:professional|relevant|industry)',
        r'experience\s+(?:of\s+)?(\d+)\+?\s*years?',
        r'(\d+)\s*-\s*\d+\s*years?',
    ]

    # Role level detection patterns
    #
    # Levels: 'intern' < 'junior' < 'mid' < 'senior'
    #
    # 'intern' is its own bucket separate from 'junior' because the
    # expectation profile differs: an intern is expected to be LEARNING,
    # so they get the largest leniency on advanced/expected-tier skills
    # and the largest bonuses for degree + extracurricular signals. A
    # junior is expected to DELIVER on the fundamentals from day one.
    ROLE_LEVEL_PATTERNS = {
        'intern': [
            r'\bintern(ship|s)?\b', r'\bplacement\b', r'\bco-?op\b',
            r'\btrainee(ship)?\b', r'\bapprentic(e|eship)\b',
            r'(summer|winter|spring|industrial|year-?long)\s+'
            r'(intern|placement|co-?op|trainee|programme|program)',
            r'\bstudent\s+(role|position|opportunity)\b',
            r'\bwork\s+experience\s+(placement|programme|program)\b',
        ],
        'junior': [
            r'junior\s+\w+', r'entry\s+level', r'associate\s+\w+', r'graduate\s+\w+',
            r'0-2\s+years', r'0-3\s+years', r'1-2\s+years', r'1-3\s+years',
            r'no\s+experience\s+required', r'willingness\s+to\s+learn',
            r'\bnew\s+grad(uate)?\b', r'\bearly\s+career\b',
        ],
        'senior': [
            r'senior\s+\w+', r'lead\s+\w+', r'principal\s+\w+', r'sr\.\s+\w+',
            # Year patterns: require an explicit "+" so "5+ years" matches
            # but "3-5 years" (a range whose upper bound happens to be 5)
            # falls through to the mid bucket. The (?<!-) lookbehind also
            # rejects ranges expressed as "3-5+ years" (rare but seen).
            r'(?<!-)5\+\s*years', r'(?<!-)7\+\s*years', r'(?<!-)10\+\s*years',
            r'\b(8|9|1[0-9]|20)\+?\s*years',
            r'extensive\s+experience', r'deep\s+expertise', r'strategic\s+thinking',
        ],
        'mid': [
            r'mid\s+level', r'mid-level', r'intermediate', r'\d+-\d+\s+years\s+experience',
            r'2-5\s+years', r'3-5\s+years', r'3-7\s+years',
        ],
    }
    
    def __init__(self, config_weights: Optional[Dict[str, float]] = None):
        """
        Initialize ML matcher with optional custom weights.

        Args:
            config_weights: Optional dict with keys 'skill_match', 'semantic', 'experience'
                          Values should sum to 1.0
        """
        # Validate and set weights
        if config_weights:
            self.WEIGHTS = config_weights
            total = sum(self.WEIGHTS.values())
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"Weights must sum to 1.0, got {total}")

        # Load sentence transformer model - required for semantic matching
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            raise ImportError(
                f"Failed to load sentence transformer model. "
                f"Model 'all-MiniLM-L6-v2' will be downloaded on first use. "
                f"Error: {str(e)}"
            )

        # Initialize recommendation generator for career-building suggestions
        self.recommendation_generator = RecommendationGenerator()
    
    def detect_role_level(self, job_description: str) -> str:
        """
        Detect role level (intern/junior/mid/senior) from job description.

        Returns:
            One of {'intern', 'junior', 'mid', 'senior'} — defaults to 'mid'.
        """
        job_lower = job_description.lower()

        # Order of resolution matters. Check the MOST SPECIFIC patterns first,
        # so a "senior software engineer internship" (rare but possible — e.g.
        # an internship for a postgrad researcher) gets 'senior' rather than
        # 'intern'. Within the same specificity, intern beats junior because
        # an "intern" classification triggers stronger leniency than 'junior',
        # and we'd rather over-classify on the lenient side for early-career
        # candidates than under-classify and unfairly penalise them.
        for level in ['senior', 'intern', 'junior', 'mid']:
            for pattern in self.ROLE_LEVEL_PATTERNS[level]:
                if re.search(pattern, job_lower, re.IGNORECASE):
                    return level

        return 'mid'
    
    def calculate_skill_match(self, resume_skills: List[str],
                              job_skills: List[str],
                              role_profile: dict = None,
                              preferred_job_skills: List[str] = None) -> Dict[str, any]:
        """
        Calculate structured skill match between resume and required job skills.

        ``preferred_job_skills`` (optional) are skills the JD marks as "nice to
        have".  Matching them adds a small bonus (≤ 5 pp); *missing* them has no
        penalty.  They appear in ``preferred_missing`` in the return dict so the
        UI can surface them separately from hard-required gaps.

        Tier weights when a role_profile is supplied:
            core skill     → weight 3.0  (non-negotiable)
            expected skill → weight 1.5  (commonly required)
            advanced skill → weight 0.5  (nice-to-have / senior)
            other skill    → weight 1.0  (in JD but not profiled)

        Without a profile the original flat ratio is used:
            ratio = (full_matches + 0.5 * partial_matches) / total_job_skills
        """
        if not job_skills:
            return {
                'matched_skills': [],
                'partial_skills': [],
                'missing_skills': [],
                'match_ratio': 0.0,
                'core_missing': [],
                'expected_missing': [],
                'advanced_missing': [],
                'preferred_missing': [],
            }

        resume_set = set(s.lower() for s in resume_skills)
        job_set    = set(s.lower() for s in job_skills)

        # ── 1. Exact matches (required skills) ───────────────────────
        exact_lower = resume_set & job_set

        # ── 2. Partial / synonym matches (required skills) ───────────
        partial_lower: set[str] = set()
        for j_skill in job_set - exact_lower:
            for r_skill in resume_set:
                if _are_synonyms(j_skill, r_skill):
                    partial_lower.add(j_skill)
                    break

        # ── 3. True misses (required) ─────────────────────────────────
        missing_lower = job_set - exact_lower - partial_lower

        matched_skills = [s for s in job_skills if s.lower() in exact_lower]
        partial_skills = [s for s in job_skills if s.lower() in partial_lower]
        missing_skills = [s for s in job_skills if s.lower() in missing_lower]

        # ── 4. Tier weight map ────────────────────────────────────────
        tier_weights: dict[str, float] = {}
        if role_profile:
            for skill in role_profile.get('core', []):
                tier_weights[skill.lower()] = 3.0
            for skill in role_profile.get('expected', []):
                tier_weights[skill.lower()] = 1.5
            for skill in role_profile.get('advanced', []):
                tier_weights[skill.lower()] = 0.5

        # ── 5. Base match ratio (required skills only) ────────────────
        total = len(job_set)
        if role_profile and tier_weights:
            weighted_total   = sum(tier_weights.get(s, 1.0) for s in job_set)
            weighted_matched = (
                sum(tier_weights.get(s, 1.0) for s in exact_lower)
                + 0.5 * sum(tier_weights.get(s, 1.0) for s in partial_lower)
            )
            base_ratio = weighted_matched / weighted_total if weighted_total > 0 else 0.0
        else:
            base_ratio = (len(exact_lower) + 0.5 * len(partial_lower)) / total if total else 0.0

        # ── 6. Preferred-skills bonus (max +5 pp, zero penalty for misses) ──
        preferred_missing: List[str] = []
        bonus = 0.0

        if preferred_job_skills:
            pref_set = set(s.lower() for s in preferred_job_skills)

            pref_exact: set[str] = resume_set & pref_set
            pref_partial: set[str] = set()
            for j_skill in pref_set - pref_exact:
                for r_skill in resume_set:
                    if _are_synonyms(j_skill, r_skill):
                        pref_partial.add(j_skill)
                        break

            pref_miss_lower = pref_set - pref_exact - pref_partial
            preferred_missing = [s for s in preferred_job_skills if s.lower() in pref_miss_lower]

            # Bonus: fraction of preferred matched × 0.05
            pref_matched_count = len(pref_exact) + 0.5 * len(pref_partial)
            if len(pref_set) > 0:
                bonus = 0.05 * (pref_matched_count / len(pref_set))

        match_ratio = min(1.0, base_ratio + bonus)

        # ── 7. Tier-labelled missing (required skills only) ───────────
        core_missing: List[str] = []
        expected_missing: List[str] = []
        advanced_missing: List[str] = []
        if role_profile:
            for s in missing_skills:
                w = tier_weights.get(s.lower(), 1.0)
                if w >= 3.0:
                    core_missing.append(s)
                elif w >= 1.5:
                    expected_missing.append(s)
                elif w < 1.0:
                    advanced_missing.append(s)

        return {
            'matched_skills':   matched_skills,
            'partial_skills':   partial_skills,
            'missing_skills':   missing_skills,
            'match_ratio':      match_ratio,
            'core_missing':     core_missing,
            'expected_missing': expected_missing,
            'advanced_missing': advanced_missing,
            'preferred_missing': preferred_missing,
        }

    def calculate_experience_alignment(self, resume_text: str,
                                        job_description: str) -> float:
        """
        Calculate experience alignment score using keyword detection.

        Looks for mentions of years of experience, seniority indicators, and
        action verbs that signal hands-on professional experience.

        Args:
            resume_text: Resume text
            job_description: Job description text

        Returns:
            Score from 0.0 to 1.0
        """
        if not resume_text or not job_description:
            return 0.0

        resume_lower = resume_text.lower()
        job_lower = job_description.lower()
        score = 0.0

        # 1. Check for years-of-experience mentions in the resume
        resume_years = []
        for pattern in self.EXPERIENCE_PATTERNS:
            matches = re.findall(pattern, resume_lower)
            resume_years.extend(int(m) for m in matches)

        job_years = []
        for pattern in self.EXPERIENCE_PATTERNS:
            matches = re.findall(pattern, job_lower)
            job_years.extend(int(m) for m in matches)

        if resume_years and job_years:
            max_resume = max(resume_years)
            min_job = min(job_years)
            if max_resume >= min_job:
                score += 0.4  # Meets or exceeds experience requirement
            else:
                # Partial credit based on how close they are
                score += 0.4 * (max_resume / min_job) if min_job > 0 else 0.0
        elif resume_years and not job_years:
            score += 0.2  # Has experience but job doesn't specify
        elif not resume_years and not job_years:
            score += 0.2  # Neither specifies — neutral

        # 2. Check for action verbs indicating hands-on experience
        action_verbs = [
            'managed', 'led', 'developed', 'implemented', 'designed',
            'built', 'created', 'delivered', 'improved', 'increased',
            'reduced', 'trained', 'supervised', 'coordinated', 'executed',
            'maintained', 'optimized', 'launched', 'resolved', 'achieved',
        ]
        verb_count = sum(1 for v in action_verbs if re.search(r'\b' + v + r'\b', resume_lower))
        # Cap contribution at 0.3
        score += min(0.3, verb_count * 0.03)

        # 3. Check for education/certification signals
        education_keywords = [
            'bachelor', 'master', 'phd', 'degree', 'diploma', 'certificate',
            'certified', 'certification', 'university', 'college',
        ]
        edu_count = sum(1 for kw in education_keywords if kw in resume_lower)
        score += min(0.3, edu_count * 0.06)

        return min(1.0, score)
    
    def _adaptive_weights(self, *, has_profile: bool,
                          n_job_skills: int, n_resume_skills: int,
                          n_matched: int) -> Tuple[Dict[str, float], str]:
        """Pick a weight preset based on how much structured signal we have.

        Rationale: when the role has a profile AND we extracted plenty of
        dictionary-level skills from both sides, the skill-match ratio is a
        high-fidelity signal — semantic similarity mostly adds noise.  When we
        have thin structural signal (no profile + very few JD skills), semantic
        similarity becomes the main way to tell a close match from a far one.

        If the caller overrides ``self.WEIGHTS`` (custom config), we skip
        adaptation and return those weights unchanged — external config wins.

        Returns:
            (weights, tier_name) — tier_name is 'custom', 'high', 'baseline',
            or 'low'.
        """
        # External override: respect it, don't second-guess
        default_w = self.ADAPTIVE_WEIGHTS['baseline']
        if any(abs(self.WEIGHTS[k] - default_w[k]) > 0.001 for k in default_w):
            return self.WEIGHTS, 'custom'

        # High-coverage: profile + enough dict skills on both sides + something
        # actually matched.  The n_matched guard prevents a run of "5 resume
        # skills, 5 JD skills, zero overlap" from triggering a score that
        # trusts the structural signal — that case should lean on semantic.
        if (has_profile
                and n_job_skills >= 5
                and n_resume_skills >= 5
                and n_matched >= 2):
            return self.ADAPTIVE_WEIGHTS['high'], 'high'

        # Low-coverage: no profile AND the JD yielded almost nothing via the
        # dictionary — semantic similarity is the only lever that still works.
        if (not has_profile) and n_job_skills < 3:
            return self.ADAPTIVE_WEIGHTS['low'], 'low'

        return self.ADAPTIVE_WEIGHTS['baseline'], 'baseline'

    def calculate_hybrid_match_score(self, resume_text: str, job_description: str,
                                   resume_skills: List[str], job_skills: List[str],
                                   skill_database: List[str] = None,
                                   preferred_job_skills: List[str] = None) -> Dict[str, any]:
        """
        Calculate comprehensive hybrid match score with detailed breakdown.

        Scoring:
        - 60% structured skill match ratio (exact + 0.5 * partial)
        - 25% SentenceTransformer semantic similarity
        - 15% experience alignment

        ``preferred_job_skills``, when provided, add a small bonus (≤ 5 pp) when
        matched — missing them carries no penalty.  They are returned under the
        ``preferred_missing`` key for display in the UI.
        """
        # Component 1: Structured skill match (primary signal — 60%)
        _role_profile = get_role_profile(job_description)
        skill_result = self.calculate_skill_match(
            resume_skills, job_skills, _role_profile, preferred_job_skills
        )
        skill_match_score = skill_result['match_ratio'] * 100

        # Consistency: if no exact *and* no partial matches, skill score = 0
        if not skill_result['matched_skills'] and not skill_result['partial_skills']:
            skill_match_score = 0.0

        # Component 2: Semantic similarity (supporting signal — 25%)
        semantic_sim = self.calculate_semantic_similarity(resume_text, job_description)
        semantic_score = semantic_sim * 100

        # Component 3: Experience alignment (15%)
        experience_alignment = self.calculate_experience_alignment(
            resume_text, job_description
        )
        experience_score = experience_alignment * 100

        # ── Adaptive weighting ────────────────────────────────────────────
        # Pick a weight preset based on how much structured signal is present.
        # See ``_adaptive_weights`` for the rules.
        _weights, _weights_tier = self._adaptive_weights(
            has_profile     = _role_profile is not None,
            n_job_skills    = len(job_skills or []),
            n_resume_skills = len(resume_skills or []),
            n_matched       = len(skill_result['matched_skills'])
                             + len(skill_result.get('partial_skills', [])),
        )

        total_score = (
            skill_match_score * _weights['skill_match'] +
            semantic_score    * _weights['semantic']    +
            experience_score  * _weights['experience']
        )

        role_level = self.detect_role_level(job_description)

        return {
            'final_score':   min(100, max(0, round(total_score, 1))),
            'total_score':   min(100, max(0, round(total_score, 1))),
            'skill_match_score': round(skill_match_score, 1),
            'semantic_score':    round(semantic_score, 1),
            'experience_score':  round(experience_score, 1),
            'scoring_weights':   dict(_weights),
            'weights_tier':      _weights_tier,
            'matched_skills':    skill_result['matched_skills'],
            'partial_skills':    skill_result['partial_skills'],
            'missing_skills':    skill_result['missing_skills'],
            'resume_skills':     resume_skills,
            'job_skills':        job_skills,
            'matched_critical_skills': skill_result['matched_skills'],
            'missing_critical_skills': skill_result['missing_skills'],
            'role_level':        role_level,
            'core_missing':      skill_result.get('core_missing', []),
            'expected_missing':  skill_result.get('expected_missing', []),
            'advanced_missing':  skill_result.get('advanced_missing', []),
            'preferred_missing': skill_result.get('preferred_missing', []),
            'has_role_profile':  _role_profile is not None,
        }
    
    def _filter_invalid_skills(self, skills: List[str]) -> List[str]:
        """
        Filter out invalid tokens (single letters, empty strings, etc.) from skill lists.
        
        Args:
            skills: List of skill strings
            
        Returns:
            Filtered list of valid skills
        """
        if not skills:
            return []
        
        valid_skills = []
        for skill in skills:
            skill_clean = skill.strip()
            # Filter out: empty strings, single letters, very short tokens
            if (len(skill_clean) > 1 and 
                not re.match(r'^[a-z]$', skill_clean.lower()) and
                len(skill_clean) >= 2):
                valid_skills.append(skill_clean)
        
        return valid_skills
    
    def _ensure_fact_consistency(self, found_skills: List[str], missing_skills: List[str],
                                 matched_critical: List[str], missing_critical: List[str]) -> Tuple[List[str], List[str], List[str], List[str]]:
        """
        Ensure fact-consistency between matched/missing skills and critical skills.
        Removes contradictions and filters invalid tokens.
        
        Args:
            found_skills: List of matched skills
            missing_skills: List of missing skills
            matched_critical: List of matched critical skills
            missing_critical: List of missing critical skills
            
        Returns:
            Tuple of (filtered_found, filtered_missing, filtered_matched_critical, filtered_missing_critical)
        """
        # Filter invalid tokens
        found_skills = self._filter_invalid_skills(found_skills)
        missing_skills = self._filter_invalid_skills(missing_skills)
        matched_critical = self._filter_invalid_skills(matched_critical)
        missing_critical = self._filter_invalid_skills(missing_critical)
        
        # Normalize for comparison (lowercase)
        found_lower = set(s.lower() for s in found_skills)
        missing_lower = set(s.lower() for s in missing_skills)
        matched_critical_lower = set(s.lower() for s in matched_critical)
        missing_critical_lower = set(s.lower() for s in missing_critical)
        
        # Remove contradictions: if a skill is in found_skills, it can't be in missing_skills
        missing_skills = [s for s in missing_skills if s.lower() not in found_lower]
        
        # Ensure critical skills are consistent with found/missing
        # If a critical skill is matched, it should be in found_skills (or at least not contradict)
        matched_critical = [s for s in matched_critical if s.lower() not in missing_lower]
        
        # If a critical skill is missing, it should be in missing_skills (or at least not contradict)
        missing_critical = [s for s in missing_critical if s.lower() not in found_lower]
        
        return found_skills, missing_skills, matched_critical, missing_critical
    
    def _calculate_score_breakdown_explanation(self, match_results: Dict[str, any]) -> str:
        """
        Generate mathematically transparent score breakdown explanation.
        FOR DEBUGGING/ADMIN USE ONLY - not shown to end users.

        Args:
            match_results: Results from calculate_hybrid_match_score

        Returns:
            Explanation string
        """
        skill = match_results['skill_match_score']
        semantic = match_results['semantic_score']
        experience = match_results['experience_score']

        # Prefer the adaptive weights actually used to produce total_score, so
        # the breakdown reconciles.  Fall back to the default WEIGHTS for
        # backward-compatibility with callers that skip the adaptive path.
        _w = match_results.get('scoring_weights', self.WEIGHTS)
        skill_weighted      = skill      * _w['skill_match']
        semantic_weighted   = semantic   * _w['semantic']
        experience_weighted = experience * _w['experience']

        total_calculated = skill_weighted + semantic_weighted + experience_weighted
        total_actual = match_results['total_score']

        explanation_parts = [
            f"Score breakdown: Skill match {skill:.1f}% (weighted: {skill_weighted:.1f}%), "
            f"Semantic similarity {semantic:.1f}% (weighted: {semantic_weighted:.1f}%), "
            f"Experience alignment {experience:.1f}% (weighted: {experience_weighted:.1f}%). "
        ]

        if abs(total_calculated - total_actual) > 1.0:
            explanation_parts.append(
                f"[Score calculation: {total_calculated:.1f}% ≈ {total_actual:.1f}%] "
            )

        return ''.join(explanation_parts)
    
    def generate_structured_feedback(self, match_results: Dict[str, any],
                                   found_skills: List[str], missing_skills: List[str],
                                   role_type: Optional[str] = None,
                                   industry: Optional[str] = None) -> Dict[str, any]:
        """
        Generate structured feedback for debugging/admin use.

        Args:
            match_results: Results from calculate_hybrid_match_score
            found_skills: List of matched skills
            missing_skills: List of missing skills
            role_type: Detected role type (optional)
            industry: Detected industry (optional)

        Returns:
            Dict with structured feedback components
        """
        score = match_results['total_score']
        role_level = match_results['role_level']

        found_skills, missing_skills, matched_critical, missing_critical = (
            self._ensure_fact_consistency(
                found_skills, missing_skills,
                match_results.get('matched_critical_skills', []),
                match_results.get('missing_critical_skills', []),
            )
        )

        if score >= 85:
            match_category = 'excellent'
        elif score >= 70:
            match_category = 'strong'
        elif score >= 50:
            match_category = 'moderate'
        else:
            match_category = 'limited'

        return {
            'match_category': match_category,
            'match_score': score,
            '_debug': {
                'score_breakdown': {
                    'skill_match': match_results['skill_match_score'],
                    'semantic_similarity': match_results['semantic_score'],
                    'experience_alignment': match_results['experience_score'],
                },
                'score_breakdown_explanation': (
                    self._calculate_score_breakdown_explanation(match_results)
                ),
                'role_level': role_level,
            },
            'matched_skills': {
                'count': len(found_skills),
                'skills': found_skills[:10],
            },
            'missing_skills': {
                'count': len(missing_skills),
                'skills': missing_skills[:10],
            },
        }
    
    def generate_ai_insight(self, match_results: Dict[str, any],
                            role_type: Optional[str] = None,
                            industry: Optional[str] = None) -> str:
        """
        Generate a career-advisor-style AI insight as a single readable string.

        Structure:
        A. 1-2 sentence reason for score (references specific skills)
        B. Key gaps listed inline (if any)
        C. 3-5 actionable bullet-point recommendations

        Args:
            match_results: Results from calculate_hybrid_match_score
            role_type: Detected role type (e.g. 'front_desk', 'developer')
            industry: Detected industry (e.g. 'hospitality', 'technology')

        Returns:
            Plain-language insight string with no ML terminology.
        """
        score = match_results['total_score']
        matched = self._filter_invalid_skills(match_results.get('matched_skills', []))
        missing = self._filter_invalid_skills(match_results.get('missing_skills', []))
        role_level = match_results.get('role_level', 'mid')

        parts: list[str] = []

        # ── Part A: Reason for score ──────────────────────────────────────
        parts.append(self._build_score_reason(score, matched, missing))

        # ── Part B: Key gaps ──────────────────────────────────────────────
        if missing:
            top_missing = missing[:5]
            parts.append(
                f"Key gaps: {', '.join(top_missing)}."
            )

        # ── Part C: Actionable recommendations (3-5 bullets) ──────────────
        recs = self._build_recommendations(missing, role_type, role_level, industry)
        if recs:
            parts.append("Next steps:")
            parts.extend(recs)

        return "\n".join(parts)

    # ── Private helpers for generate_ai_insight ───────────────────────────

    def _build_score_reason(self, score: float,
                            matched: List[str],
                            missing: List[str]) -> str:
        """Return 1-2 sentences explaining WHY the score is what it is."""
        matched_count = len(matched)
        missing_count = len(missing)
        total_required = matched_count + missing_count

        if score >= 85:
            reason = (
                f"Your resume is a strong fit ({int(score)}% match). "
                f"You demonstrate {matched_count} of the {total_required} "
                f"skills this role requires"
            )
            if matched:
                reason += f", including {', '.join(matched[:3])}"
            return reason + "."

        if score >= 70:
            reason = (
                f"Your resume is a solid match ({int(score)}% match) with "
                f"{matched_count} of {total_required} required skills present"
            )
            if missing:
                reason += (
                    f", but the employer is also looking for "
                    f"{', '.join(missing[:2])}"
                )
            return reason + "."

        if score >= 50:
            reason = (
                f"Your resume partially matches this role ({int(score)}% match). "
                f"You cover {matched_count} of {total_required} required skills"
            )
            if missing:
                reason += (
                    f", however {missing_count} skill(s) the job emphasizes "
                    f"are not clearly shown — notably {', '.join(missing[:2])}"
                )
            return reason + "."

        # Below 50
        if matched:
            reason = (
                f"There is limited overlap between your resume and this role "
                f"({int(score)}% match). While you show {', '.join(matched[:2])}, "
                f"the position requires {missing_count} additional skill(s) you "
                f"haven't demonstrated yet"
            )
        else:
            reason = (
                f"Your resume does not yet reflect the core skills for this "
                f"position ({int(score)}% match). The role requires "
                f"{', '.join(missing[:3]) if missing else 'skills'} that are "
                f"not present in your resume"
            )
        return reason + "."

    def _build_recommendations(self, missing: List[str],
                               role_type: Optional[str],
                               role_level: str,
                               industry: Optional[str]) -> List[str]:
        """Return 3-5 specific, actionable bullet points."""
        recs: list[str] = []

        # 1. Courses / certifications for top missing skills
        for skill in missing[:2]:
            course = self._get_course_suggestion(skill, role_type, industry)
            recs.append(f"  - {course}")

        # 2. Real-world opportunity (role-specific)
        opp = self._get_opportunity_suggestion(role_type, role_level, industry)
        if opp:
            recs.append(f"  - {opp}")

        # 3. Resume improvement tip (role-specific)
        resume_tip = self._get_resume_tip(missing, role_type, role_level)
        if resume_tip:
            recs.append(f"  - {resume_tip}")

        # 4. Extra tip if we have room and missing skills remain
        if len(recs) < 5 and len(missing) > 2:
            extra_skill = missing[2]
            recs.append(
                f"  - Search for \"{extra_skill}\" tutorials on LinkedIn "
                f"Learning or YouTube to build foundational knowledge."
            )

        return recs[:5]

    def _get_course_suggestion(self, skill: str,
                               role_type: Optional[str],
                               industry: Optional[str]) -> str:
        """Map a single missing skill to a specific course recommendation."""
        s = skill.lower()

        # Technology skills
        tech_courses = {
            'python': 'Complete "Python for Everybody" on Coursera (University of Michigan) to build your Python proficiency.',
            'java': 'Enroll in "Java Programming and Software Engineering Fundamentals" on Coursera (Duke University).',
            'javascript': 'Take "The Complete JavaScript Course" on Udemy or "JavaScript Basics" on Coursera.',
            'typescript': 'Complete "Understanding TypeScript" on Udemy to add TypeScript to your skill set.',
            'sql': 'Take "SQL for Data Science" on Coursera (UC Davis) to demonstrate database querying ability.',
            'react': 'Enroll in "React - The Complete Guide" on Udemy or Meta\'s Front-End Developer Certificate on Coursera.',
            'angular': 'Complete "Angular - The Complete Guide" on Udemy to build Angular project experience.',
            'node.js': 'Take "Server-side Development with NodeJS" on Coursera (Hong Kong UST).',
            'machine learning': 'Complete Andrew Ng\'s "Machine Learning Specialization" on Coursera (Stanford/DeepLearning.AI).',
            'data analysis': 'Enroll in Google\'s "Data Analytics Professional Certificate" on Coursera.',
            'data science': 'Complete IBM\'s "Data Science Professional Certificate" on Coursera.',
            'aws': 'Prepare for the AWS Cloud Practitioner certification through AWS Skill Builder (free tier available).',
            'docker': 'Take "Docker Mastery" on Udemy to learn containerisation fundamentals.',
            'kubernetes': 'Enroll in "Kubernetes for Developers" on Linux Foundation or Udemy.',
            'git': 'Complete "Version Control with Git" on Coursera (Atlassian) to demonstrate collaboration skills.',
            'agile': 'Earn a Certified ScrumMaster (CSM) or take "Agile with Atlassian Jira" on Coursera.',
            'scrum': 'Earn a Certified ScrumMaster (CSM) or take "Agile with Atlassian Jira" on Coursera.',
        }
        if s in tech_courses:
            return tech_courses[s]

        # Hospitality skills
        if industry == 'hospitality' or role_type in ('front_desk', 'customer_service'):
            hospitality_courses = {
                'front desk': 'Complete "Hotel Management" on Coursera (ESSEC Business School) to strengthen your front desk credentials.',
                'guest relations': 'Take "Hospitality & Tourism Management" on edX (University of Queensland) for guest relations training.',
                'reservation systems': 'Learn Opera PMS through Oracle\'s free training modules or "Hotel Reservation Systems" on Udemy.',
                'customer service': 'Earn the "Customer Service Excellence" certificate on Coursera or take CVS Health\'s Customer Service course.',
                'event planning': 'Enroll in "Event Management" on Coursera (University of the Highlands and Islands).',
                'hospitality management': 'Complete "Hotel Management: Distribution, Revenue and Demand" on Coursera (ESSEC).',
            }
            if s in hospitality_courses:
                return hospitality_courses[s]

        # Business / soft skills
        soft_courses = {
            'communication': 'Take "Improving Communication Skills" on Coursera (University of Pennsylvania).',
            'leadership': 'Enroll in "Inspiring and Motivating Individuals" on Coursera (University of Michigan).',
            'project management': 'Earn Google\'s "Project Management Professional Certificate" on Coursera.',
            'teamwork': 'Complete "Teamwork Skills" on Coursera (University of Colorado) to showcase collaboration ability.',
            'problem solving': 'Take "Creative Problem Solving" on Coursera (University of Minnesota).',
            'presentation': 'Enroll in "Presentation Skills" on LinkedIn Learning to sharpen your delivery.',
            'negotiation': 'Complete "Successful Negotiation" on Coursera (University of Michigan).',
            'excel': 'Take "Excel Skills for Business" on Coursera (Macquarie University).',
            'tableau': 'Complete "Data Visualization with Tableau" on Coursera (UC Davis).',
            'power bi': 'Enroll in "Microsoft Power BI Data Analyst" on Coursera (Microsoft).',
            'financial analysis': 'Take "Financial Analysis" on Coursera (University of Illinois) to build finance skills.',
        }
        if s in soft_courses:
            return soft_courses[s]

        # Fallback: still specific, not generic
        return (
            f"Search for \"{skill}\" courses on Coursera, edX, or LinkedIn "
            f"Learning and complete at least one certified program to "
            f"demonstrate this skill on your resume."
        )

    def _get_opportunity_suggestion(self, role_type: Optional[str],
                                    role_level: str,
                                    industry: Optional[str]) -> str:
        """Return one real-world opportunity suggestion tailored to role."""
        if role_type == 'front_desk' or industry == 'hospitality':
            if role_level == 'junior':
                return (
                    "Apply for part-time front desk or guest services roles "
                    "at local hotels, hostels, or event venues to build "
                    "hands-on hospitality experience."
                )
            return (
                "Seek a short-term contract or seasonal position at a hotel "
                "or resort to add direct hospitality experience to your resume."
            )

        if role_type == 'customer_service':
            if role_level == 'junior':
                return (
                    "Volunteer at a community help desk, call centre, or "
                    "retail store to gain verifiable customer-facing experience."
                )
            return (
                "Take on a customer success or support lead project at your "
                "current organisation to demonstrate service leadership."
            )

        if role_type == 'developer':
            if role_level == 'junior':
                return (
                    "Build 2-3 portfolio projects on GitHub using the "
                    "technologies listed in this job posting, and include "
                    "live demo links in your resume."
                )
            if role_level == 'senior':
                return (
                    "Contribute to open-source projects or mentor junior "
                    "developers to demonstrate technical leadership beyond "
                    "your day job."
                )
            return (
                "Publish a side project or technical blog post showcasing "
                "the missing skills to provide tangible proof of ability."
            )

        if role_type == 'analyst':
            return (
                "Complete a Kaggle competition or build a data analysis "
                "portfolio project to demonstrate analytical skills with "
                "real datasets."
            )

        # Generic
        if role_level == 'junior':
            return (
                "Look for internships, apprenticeships, or volunteer "
                "positions in this field to build verifiable experience."
            )
        return (
            "Take on a cross-functional project or freelance engagement "
            "that lets you practise the missing skills in a real-world setting."
        )

    def _get_resume_tip(self, missing: List[str],
                        role_type: Optional[str],
                        role_level: str) -> str:
        """Return one specific resume-improvement tip."""
        if role_type == 'front_desk' or role_type == 'customer_service':
            return (
                "Add a dedicated \"Hospitality Skills\" or \"Customer "
                "Service\" section to your resume listing specific systems "
                "(e.g., Opera PMS, reservation platforms) and measurable "
                "achievements (e.g., \"handled 50+ guest check-ins daily\")."
            )

        if role_type == 'developer':
            if missing:
                tech_list = ', '.join(missing[:3])
                return (
                    f"Create a \"Technical Skills\" section that explicitly "
                    f"lists {tech_list}, and reference these technologies in "
                    f"your project descriptions with quantified results "
                    f"(e.g., \"reduced API response time by 40%\")."
                )
            return (
                "Quantify your engineering impact in each role — include "
                "metrics like response time improvements, user growth, or "
                "lines of code shipped."
            )

        if role_type == 'analyst':
            return (
                "Highlight specific tools (Excel, Tableau, SQL) in a "
                "\"Technical Skills\" section and describe analysis outcomes "
                "with numbers (e.g., \"identified $200K in cost savings\")."
            )

        # Generic
        if missing:
            return (
                f"Review your resume and explicitly mention "
                f"{', '.join(missing[:2])} in your skills section or work "
                f"experience descriptions, with concrete examples of how "
                f"you've applied them."
            )
        return (
            "Use strong action verbs (led, designed, delivered) and "
            "include measurable outcomes in every bullet point to make "
            "your experience stand out."
        )
    
    # ========== Core Methods ==========

    def calculate_semantic_similarity(self, text1, text2):
        """Calculate semantic similarity between two texts using sentence transformers."""
        if not text1 or not text2:
            return 0.0

        embeddings = self.sentence_model.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)

    # ========== Legacy Methods (for backward compatibility) ==========

    def extract_skills_semantic(self, text, skill_database):
        """Extract skills from text — now delegates to rule-based extract_skills."""
        return extract_skills(text)

    def extract_key_phrases(self, text, max_phrases=20):
        """Extract key phrases — now delegates to rule-based extract_skills."""
        return extract_skills(text)[:max_phrases]

    def calculate_ml_match_score(self, resume_text, job_description, keyword_score):
        """Legacy method for backward compatibility."""
        semantic_sim = self.calculate_semantic_similarity(resume_text, job_description)
        semantic_score = semantic_sim * 100
        ml_score = (keyword_score * 0.6) + (semantic_score * 0.4)
        return min(100, max(0, int(ml_score)))

    def extract_semantic_keywords(self, text, top_n=30):
        """Extract keywords — now delegates to rule-based extract_skills."""
        return extract_skills(text)[:top_n]
