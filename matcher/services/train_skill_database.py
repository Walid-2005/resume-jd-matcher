"""
Training pipeline v2: Build 200+ role templates from multiple datasets.

Data sources:
1. UpdatedResumeDataSet.csv — 962 categorised resumes (skill extraction)
2. new_jobs.csv — 289 IT job titles with labeled skills
3. job_descriptions.csv — 853 real job postings (skill extraction)
4. Hand-curated expansions for underrepresented industries

Usage:
    python -m matcher.services.train_skill_database
"""

import csv
import re
import os
import json
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

# ── Master skill patterns ────────────────────────────────────────────
MASTER_SKILLS: Dict[str, List[str]] = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c",
        "php", "ruby", "go", "golang", "rust", "swift", "kotlin", "scala",
        "perl", "matlab", "r", "sql", "pl/sql", "t-sql", "html", "css",
        "sass", "less", "shell", "bash", "powershell", "lua", "haskell",
        "elixir", "clojure", "dart", "groovy", "objective-c", "assembly",
        "fortran", "cobol", "visual basic", "vb.net", "f#",
        "solidity", "verilog", "vhdl",
    ],
    "web_frameworks": [
        "react", "angular", "vue", "vue.js", "svelte", "next.js", "nextjs",
        "nuxt", "nuxt.js", "gatsby", "remix", "ember", "backbone",
        "node.js", "nodejs", "express", "express.js", "nestjs", "nest.js",
        "django", "flask", "fastapi", "spring", "spring boot", "springboot",
        "laravel", "symfony", "codeigniter", "ruby on rails", "rails",
        "asp.net", ".net", ".net core", "blazor",
        "jquery", "bootstrap", "tailwind", "tailwindcss",
        "material ui", "chakra ui", "ant design",
        "webpack", "vite", "babel", "parcel",
        "graphql", "rest api", "restful", "soap", "websocket", "grpc",
    ],
    "databases": [
        "mysql", "postgresql", "postgres", "mongodb", "redis", "oracle",
        "sqlite", "cassandra", "dynamodb", "couchdb", "couchbase",
        "elasticsearch", "neo4j", "firebase", "supabase", "mariadb",
        "mssql", "sql server", "snowflake", "bigquery", "redshift",
        "influxdb", "memcached", "hbase", "cockroachdb",
    ],
    "cloud_devops": [
        "aws", "amazon web services", "azure", "gcp", "google cloud",
        "docker", "kubernetes", "k8s", "jenkins", "terraform", "ansible",
        "chef", "puppet", "vagrant", "prometheus", "grafana", "nagios",
        "ci/cd", "github actions", "gitlab ci", "circleci", "travis ci",
        "argocd", "helm", "istio", "nginx", "apache",
        "cloudformation", "pulumi", "openstack",
        "heroku", "vercel", "netlify", "digitalocean", "linode",
        "lambda", "ec2", "s3", "ecs", "eks", "fargate", "cloudfront",
        "azure devops", "azure functions",
    ],
    "data_ml_ai": [
        "machine learning", "deep learning", "artificial intelligence",
        "neural networks", "natural language processing", "nlp",
        "computer vision", "data science", "data analysis", "data mining",
        "data engineering", "data visualization", "data warehousing",
        "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
        "opencv", "spacy", "nltk", "hugging face", "transformers",
        "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "jupyter", "spark", "pyspark", "hadoop", "hive", "pig",
        "kafka", "airflow", "luigi", "dbt", "mlflow",
        "regression", "classification", "clustering", "dimensionality reduction",
        "random forest", "decision trees", "svm", "knn", "xgboost",
        "gradient boosting", "ensemble methods", "bayesian",
        "cnn", "rnn", "lstm", "gan", "transformer", "bert", "gpt",
        "yolo", "resnet", "vgg", "unet",
        "reinforcement learning", "transfer learning", "federated learning",
        "feature engineering", "model deployment", "mlops",
        "tableau", "power bi", "looker", "qlik", "d3.js",
        "etl", "olap", "data pipeline",
        "statistics", "statistical analysis", "a/b testing",
        "time series", "forecasting", "anomaly detection",
        "recommendation systems", "chatbot", "llm",
        "langchain", "rag", "prompt engineering",
    ],
    "mobile": [
        "react native", "flutter", "ionic", "xamarin",
        "ios", "android", "swift", "kotlin", "swiftui",
        "objective-c", "xcode", "android studio",
        "mobile development", "cross-platform",
    ],
    "cybersecurity": [
        "cybersecurity", "information security", "network security",
        "penetration testing", "ethical hacking", "vulnerability assessment",
        "siem", "ids", "ips", "firewall", "encryption",
        "ssl", "tls", "oauth", "jwt", "sso", "ldap",
        "owasp", "nist", "iso 27001", "gdpr", "sox",
        "wireshark", "nmap", "metasploit", "burp suite",
        "incident response", "threat modeling", "malware analysis",
        "security audit", "compliance", "risk assessment",
    ],
    "testing_qa": [
        "selenium", "cypress", "jest", "mocha", "chai", "pytest",
        "junit", "testng", "cucumber", "appium", "postman",
        "unit testing", "integration testing", "e2e testing",
        "test automation", "manual testing", "qa",
        "performance testing", "load testing", "jmeter",
        "test driven development", "tdd", "bdd",
        "continuous testing", "regression testing",
        "api testing", "security testing",
    ],
    "version_control": [
        "git", "github", "gitlab", "bitbucket", "svn", "mercurial",
        "version control",
    ],
    "project_management": [
        "agile", "scrum", "kanban", "waterfall", "lean",
        "jira", "confluence", "trello", "asana", "monday.com",
        "notion", "clickup", "basecamp", "ms project",
        "project management", "sprint planning", "backlog grooming",
        "stakeholder management", "risk management",
        "pmp", "prince2", "safe",
    ],
    "design_tools": [
        "figma", "sketch", "adobe photoshop", "adobe illustrator",
        "adobe indesign", "adobe xd", "adobe premiere",
        "adobe after effects", "canva", "invision",
        "zeplin", "miro", "lucidchart",
        "ui/ux design", "ux research", "wireframing",
        "prototyping", "graphic design", "user interface",
        "user experience", "responsive design", "accessibility",
        "design thinking", "information architecture",
    ],
    "business_tools": [
        "microsoft office", "ms office", "excel", "word", "powerpoint",
        "outlook", "sharepoint", "teams", "onedrive",
        "google workspace", "google docs", "google sheets",
        "google slides", "gmail",
        "salesforce", "hubspot", "zoho", "sap", "oracle erp",
        "quickbooks", "xero", "sage",
        "slack", "zoom", "webex", "google meet",
        "wordpress", "shopify", "squarespace", "wix",
        "mailchimp", "sendgrid", "twilio",
    ],
    "marketing_skills": [
        "digital marketing", "content marketing", "social media marketing",
        "seo", "sem", "ppc", "google ads", "facebook ads",
        "email marketing", "marketing automation", "crm",
        "google analytics", "adobe analytics",
        "content strategy", "copywriting", "brand management",
        "influencer marketing", "affiliate marketing",
        "market research", "competitive analysis",
        "social media", "facebook", "instagram", "linkedin",
        "twitter", "tiktok", "youtube", "pinterest",
    ],
    "finance_accounting": [
        "accounting", "bookkeeping", "financial reporting",
        "financial analysis", "financial modeling", "budgeting",
        "forecasting", "tax preparation", "auditing",
        "accounts payable", "accounts receivable", "payroll",
        "investment analysis", "portfolio management",
        "risk management", "compliance", "regulatory reporting",
        "gaap", "ifrs", "cpa", "cfa", "acca",
        "bloomberg terminal", "capital iq",
    ],
    "healthcare": [
        "patient care", "medical records", "clinical research",
        "nursing", "pharmacy", "medical terminology",
        "hipaa", "ehr", "electronic health records",
        "first aid", "cpr", "vital signs", "phlebotomy", "triage",
        "clinical trials", "epidemiology", "biostatistics",
        "medical imaging", "telemedicine",
    ],
    "engineering": [
        "cad", "autocad", "solidworks", "catia", "ansys",
        "matlab", "simulink", "labview",
        "plc", "scada", "hmi",
        "lean manufacturing", "six sigma", "kaizen",
        "quality control", "quality assurance",
        "mechanical design", "electrical design",
        "circuit design", "pcb design",
        "3d printing", "cnc", "robotics",
    ],
    "blockchain": [
        "blockchain", "ethereum", "solidity", "smart contracts",
        "web3", "defi", "nft", "cryptocurrency",
        "hyperledger", "truffle", "hardhat", "ganache",
        "metamask", "ipfs", "consensus algorithms",
    ],
    "soft_skills": [
        "communication", "leadership", "teamwork", "collaboration",
        "problem solving", "critical thinking", "analytical skills",
        "time management", "mentoring", "training", "presentation",
        "negotiation", "customer service", "client relations",
        "attention to detail", "multitasking", "organizational skills",
        "interpersonal skills", "conflict resolution", "decision making",
        "adaptability", "creativity", "research", "writing",
        "public speaking", "emotional intelligence",
        "strategic thinking", "innovation", "self-motivated",
    ],
    "languages": [
        "english", "french", "spanish", "german", "italian",
        "portuguese", "chinese", "mandarin", "cantonese",
        "japanese", "korean", "arabic", "hindi", "urdu",
        "russian", "dutch", "swedish", "norwegian", "danish",
        "finnish", "polish", "turkish", "thai", "vietnamese",
        "malay", "indonesian", "tagalog", "hebrew", "bengali",
    ],
    "networking": [
        "tcp/ip", "dns", "dhcp", "vpn", "lan", "wan",
        "routing", "switching", "load balancing",
        "cisco", "juniper", "ccna", "ccnp",
        "software defined networking", "sdn",
        "network administration", "network architecture",
    ],
    "operating_systems": [
        "linux", "unix", "windows", "macos",
        "ubuntu", "centos", "red hat", "rhel", "debian",
        "fedora", "arch linux", "kali linux",
        "windows server",
    ],
    "supply_chain_ops": [
        "supply chain management", "logistics", "inventory management",
        "procurement", "vendor management", "warehousing",
        "demand planning", "production planning", "erp",
        "lean manufacturing", "six sigma", "continuous improvement",
    ],
    "legal": [
        "contract management", "contract review", "legal research",
        "litigation", "corporate law", "intellectual property",
        "regulatory compliance", "arbitration", "mediation",
        "legal writing", "due diligence", "paralegal",
    ],
    "education": [
        "curriculum development", "lesson planning", "classroom management",
        "student assessment", "educational technology", "e-learning",
        "instructional design", "tutoring", "pedagogy",
        "special education", "differentiated instruction",
    ],
    "real_estate": [
        "property management", "real estate", "leasing",
        "tenant relations", "property valuation", "mls",
        "real estate law", "negotiation",
    ],
    "media_communications": [
        "journalism", "media relations", "press releases",
        "public relations", "content creation", "video production",
        "audio editing", "photography", "broadcasting",
        "social media management", "editorial", "proofreading",
    ],
    "hr_recruitment": [
        "recruiting", "talent acquisition", "onboarding",
        "employee relations", "performance management",
        "compensation and benefits", "hris", "workday",
        "succession planning", "diversity and inclusion",
        "training and development", "labor relations",
    ],
}


def extract_skills_from_text(text: str) -> Set[str]:
    """Extract all matching skills from a text."""
    if not text or len(text.strip()) < 10:
        return set()

    text_lower = text.lower()
    normalized = re.sub(r'[^\w\s/#+\-.]', ' ', text_lower)
    normalized = re.sub(r'\s+', ' ', normalized)

    found: Set[str] = set()

    all_skills: List[Tuple[str, str]] = []
    for category, skills in MASTER_SKILLS.items():
        for skill in skills:
            all_skills.append((skill, category))
    all_skills.sort(key=lambda x: len(x[0]), reverse=True)

    for skill, category in all_skills:
        skill_lower = skill.lower()
        if len(skill_lower) < 2:
            continue
        if ' ' in skill_lower or '-' in skill_lower or '/' in skill_lower:
            if skill_lower in normalized:
                found.add(skill_lower)
        else:
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, normalized):
                found.add(skill_lower)

    return found


def categorize_skill(skill: str) -> str:
    """Return the category a skill belongs to."""
    skill_lower = skill.lower()
    for category, skills in MASTER_SKILLS.items():
        if skill_lower in [s.lower() for s in skills]:
            return category
    return "other"


# ── Hand-curated role templates for underrepresented industries ───
# These are industries the Kaggle datasets don't cover well.
MANUAL_ROLE_TEMPLATES: Dict[str, List[str]] = {
    # ── Education ──────────────────────────────────────────────
    "teacher": [
        "curriculum development", "lesson planning", "classroom management",
        "student assessment", "communication", "presentation",
        "microsoft office", "google workspace", "adaptability",
    ],
    "university professor": [
        "research", "writing", "curriculum development", "presentation",
        "mentoring", "communication", "data analysis", "critical thinking",
    ],
    "instructional designer": [
        "instructional design", "e-learning", "curriculum development",
        "educational technology", "writing", "communication",
        "adobe photoshop", "figma", "presentation",
    ],
    "tutor": [
        "tutoring", "communication", "patience", "adaptability",
        "lesson planning", "student assessment", "problem solving",
    ],
    "school administrator": [
        "leadership", "budgeting", "communication", "strategic planning",
        "stakeholder management", "microsoft office", "decision making",
    ],
    # ── Legal ─────────────────────────────────────────────────
    "lawyer": [
        "legal research", "legal writing", "litigation", "contract review",
        "negotiation", "critical thinking", "communication", "research",
    ],
    "paralegal": [
        "legal research", "legal writing", "contract management",
        "organizational skills", "attention to detail", "microsoft office",
        "communication", "research",
    ],
    "compliance officer": [
        "regulatory compliance", "risk assessment", "auditing",
        "compliance", "communication", "attention to detail",
        "analytical skills", "microsoft office",
    ],
    "corporate counsel": [
        "corporate law", "contract review", "legal research",
        "negotiation", "intellectual property", "communication",
        "regulatory compliance", "due diligence",
    ],
    # ── Real Estate / Construction ────────────────────────────
    "real estate agent": [
        "real estate", "negotiation", "communication", "sales",
        "client relations", "mls", "marketing", "customer service",
    ],
    "property manager": [
        "property management", "tenant relations", "budgeting",
        "customer service", "communication", "microsoft office",
        "negotiation", "organizational skills",
    ],
    "construction manager": [
        "project management", "budgeting", "autocad", "cad",
        "leadership", "risk management", "communication",
        "stakeholder management", "quality control",
    ],
    "architect": [
        "autocad", "cad", "3d printing", "design thinking",
        "communication", "presentation", "project management",
        "creativity", "attention to detail",
    ],
    "interior designer": [
        "autocad", "cad", "creativity", "communication",
        "client relations", "presentation", "budgeting",
        "adobe photoshop", "figma",
    ],
    # ── Media / Communications / Journalism ───────────────────
    "journalist": [
        "writing", "journalism", "research", "communication",
        "critical thinking", "social media", "content creation",
        "editorial", "proofreading",
    ],
    "public relations specialist": [
        "public relations", "media relations", "press releases",
        "communication", "writing", "social media management",
        "content creation", "presentation",
    ],
    "content writer": [
        "writing", "copywriting", "seo", "content strategy",
        "communication", "research", "social media",
        "wordpress", "content creation",
    ],
    "content strategist": [
        "content strategy", "seo", "content marketing",
        "google analytics", "communication", "writing",
        "social media", "research",
    ],
    "copywriter": [
        "copywriting", "writing", "communication", "creativity",
        "seo", "brand management", "content strategy", "research",
    ],
    "video producer": [
        "video production", "adobe premiere", "adobe after effects",
        "photography", "audio editing", "content creation",
        "communication", "creativity",
    ],
    "social media manager": [
        "social media management", "social media", "content creation",
        "google analytics", "communication", "copywriting",
        "facebook", "instagram", "linkedin", "tiktok",
    ],
    "podcast producer": [
        "audio editing", "content creation", "communication",
        "social media", "writing", "research", "creativity",
    ],
    # ── Healthcare (expanded) ─────────────────────────────────
    "doctor": [
        "patient care", "medical terminology", "clinical research",
        "communication", "decision making", "leadership",
        "attention to detail", "critical thinking",
    ],
    "pharmacist": [
        "pharmacy", "medical terminology", "patient care",
        "attention to detail", "communication", "regulatory compliance",
        "customer service",
    ],
    "physical therapist": [
        "patient care", "medical terminology", "communication",
        "problem solving", "first aid", "teamwork", "adaptability",
    ],
    "medical researcher": [
        "clinical research", "clinical trials", "biostatistics",
        "epidemiology", "data analysis", "research", "writing",
        "python", "statistics",
    ],
    "healthcare administrator": [
        "leadership", "budgeting", "hipaa", "compliance",
        "electronic health records", "project management",
        "communication", "microsoft office", "stakeholder management",
    ],
    "dental hygienist": [
        "patient care", "medical records", "communication",
        "attention to detail", "customer service", "first aid",
    ],
    "veterinarian": [
        "patient care", "medical terminology", "communication",
        "decision making", "attention to detail", "customer service",
    ],
    # ── Finance (expanded) ────────────────────────────────────
    "investment banker": [
        "financial modeling", "financial analysis", "excel",
        "bloomberg terminal", "capital iq", "communication",
        "presentation", "powerpoint", "accounting",
    ],
    "bank teller": [
        "customer service", "cash handling", "attention to detail",
        "communication", "microsoft office", "problem solving",
        "multitasking",
    ],
    "insurance agent": [
        "sales", "customer service", "negotiation",
        "communication", "crm", "microsoft office",
        "client relations", "risk assessment",
    ],
    "tax accountant": [
        "tax preparation", "accounting", "financial reporting",
        "excel", "gaap", "auditing", "attention to detail",
        "communication",
    ],
    "auditor": [
        "auditing", "financial reporting", "accounting", "compliance",
        "excel", "analytical skills", "attention to detail",
        "communication", "gaap",
    ],
    "financial planner": [
        "financial analysis", "portfolio management", "investment analysis",
        "communication", "client relations", "excel",
        "presentation", "cfa",
    ],
    "credit analyst": [
        "financial analysis", "risk assessment", "excel",
        "financial modeling", "communication", "analytical skills",
        "attention to detail",
    ],
    "treasury analyst": [
        "financial analysis", "forecasting", "excel",
        "budgeting", "financial modeling", "risk management",
        "communication",
    ],
    # ── HR / Recruitment ──────────────────────────────────────
    "recruiter": [
        "recruiting", "talent acquisition", "communication",
        "linkedin", "negotiation", "crm", "interpersonal skills",
        "organizational skills",
    ],
    "hr manager": [
        "employee relations", "performance management",
        "compensation and benefits", "recruiting", "leadership",
        "communication", "hris", "compliance",
        "training and development",
    ],
    "hr coordinator": [
        "onboarding", "hris", "communication", "microsoft office",
        "organizational skills", "attention to detail",
        "employee relations", "multitasking",
    ],
    "training manager": [
        "training and development", "instructional design",
        "e-learning", "leadership", "communication",
        "presentation", "curriculum development",
    ],
    # ── Operations / Logistics / Supply Chain ─────────────────
    "supply chain manager": [
        "supply chain management", "logistics", "procurement",
        "vendor management", "erp", "sap", "excel",
        "leadership", "negotiation", "budgeting",
    ],
    "logistics coordinator": [
        "logistics", "supply chain management", "communication",
        "organizational skills", "excel", "erp",
        "attention to detail", "multitasking",
    ],
    "warehouse manager": [
        "warehousing", "inventory management", "leadership",
        "logistics", "excel", "communication",
        "organizational skills", "six sigma",
    ],
    "procurement specialist": [
        "procurement", "vendor management", "negotiation",
        "excel", "communication", "contract management",
        "analytical skills", "erp",
    ],
    "inventory analyst": [
        "inventory management", "excel", "data analysis",
        "forecasting", "erp", "communication",
        "attention to detail", "sql",
    ],
    "quality assurance manager": [
        "quality control", "quality assurance", "six sigma",
        "lean manufacturing", "leadership", "communication",
        "continuous improvement", "auditing",
    ],
    # ── Sales / Business Development ──────────────────────────
    "sales manager": [
        "sales", "leadership", "crm", "salesforce",
        "communication", "negotiation", "strategic planning",
        "client relations", "presentation", "budgeting",
    ],
    "account manager": [
        "client relations", "sales", "crm", "communication",
        "negotiation", "stakeholder management", "presentation",
        "excel", "strategic planning",
    ],
    "business development manager": [
        "business development", "sales", "strategic planning",
        "negotiation", "communication", "client relations",
        "crm", "market research", "presentation",
    ],
    "sales engineer": [
        "sales", "communication", "presentation", "rest api",
        "problem solving", "python", "sql", "client relations",
    ],
    "retail manager": [
        "customer service", "leadership", "sales", "inventory management",
        "communication", "multitasking", "microsoft office",
        "training", "budgeting",
    ],
    "retail sales associate": [
        "customer service", "sales", "communication", "multitasking",
        "teamwork", "problem solving",
    ],
    "e-commerce manager": [
        "shopify", "seo", "digital marketing", "google analytics",
        "communication", "excel", "social media", "leadership",
    ],
    # ── Customer Support ──────────────────────────────────────
    "technical support engineer": [
        "linux", "networking", "customer service", "communication",
        "problem solving", "sql", "python", "ticketing systems",
    ],
    "help desk technician": [
        "customer service", "communication", "windows",
        "linux", "microsoft office", "problem solving",
        "networking", "multitasking",
    ],
    "call center manager": [
        "customer service", "leadership", "communication",
        "crm", "training", "performance management",
        "multitasking", "conflict resolution",
    ],
    # ── Creative / Arts ───────────────────────────────────────
    "photographer": [
        "photography", "adobe photoshop", "adobe illustrator",
        "communication", "creativity", "attention to detail",
        "video production",
    ],
    "animator": [
        "adobe after effects", "adobe premiere", "creativity",
        "3d printing", "communication", "attention to detail",
        "teamwork",
    ],
    "game developer": [
        "c++", "c#", "python", "javascript", "git",
        "problem solving", "teamwork", "creativity",
        "agile", "communication",
    ],
    "game designer": [
        "creativity", "communication", "teamwork", "problem solving",
        "writing", "presentation", "prototyping", "research",
    ],
    "music producer": [
        "audio editing", "creativity", "communication",
        "teamwork", "attention to detail",
    ],
    # ── Science / Research ────────────────────────────────────
    "research scientist": [
        "research", "data analysis", "python", "statistics",
        "writing", "communication", "critical thinking",
        "matlab", "presentation",
    ],
    "lab technician": [
        "research", "attention to detail", "data analysis",
        "quality control", "communication", "writing",
        "critical thinking",
    ],
    "environmental scientist": [
        "research", "data analysis", "writing", "communication",
        "statistics", "gis", "regulatory compliance", "critical thinking",
    ],
    "biomedical engineer": [
        "matlab", "cad", "research", "data analysis",
        "communication", "writing", "problem solving",
        "quality control",
    ],
    "chemist": [
        "research", "data analysis", "quality control",
        "writing", "communication", "attention to detail",
        "critical thinking",
    ],
    # ── Government / Public Sector ────────────────────────────
    "policy analyst": [
        "research", "data analysis", "writing", "communication",
        "critical thinking", "presentation", "strategic planning",
        "stakeholder management",
    ],
    "urban planner": [
        "cad", "autocad", "communication", "research",
        "project management", "presentation", "writing",
        "stakeholder management",
    ],
    "grant writer": [
        "writing", "research", "communication", "budgeting",
        "attention to detail", "project management",
    ],
    # ── Hospitality / Food / Tourism ──────────────────────────
    "restaurant manager": [
        "customer service", "leadership", "budgeting",
        "communication", "multitasking", "training",
        "inventory management", "food and beverage",
    ],
    "chef": [
        "food and beverage", "leadership", "teamwork",
        "creativity", "time management", "multitasking",
        "communication", "attention to detail",
    ],
    "event planner": [
        "event planning", "communication", "budgeting",
        "client relations", "negotiation", "multitasking",
        "organizational skills", "leadership",
    ],
    "travel agent": [
        "customer service", "communication", "sales",
        "organizational skills", "multitasking",
        "client relations", "negotiation",
    ],
    "flight attendant": [
        "customer service", "communication", "first aid",
        "teamwork", "multitasking", "conflict resolution",
        "adaptability",
    ],
    "tour guide": [
        "communication", "public speaking", "customer service",
        "adaptability", "teamwork", "research",
    ],
    # ── Transportation / Automotive ───────────────────────────
    "automotive engineer": [
        "cad", "autocad", "solidworks", "matlab",
        "mechanical design", "quality control",
        "communication", "problem solving",
    ],
    "fleet manager": [
        "logistics", "budgeting", "leadership",
        "communication", "vendor management", "compliance",
        "excel", "organizational skills",
    ],
    # ── Agriculture / Environment ─────────────────────────────
    "agricultural engineer": [
        "research", "data analysis", "cad", "matlab",
        "communication", "problem solving", "writing",
    ],
    "sustainability consultant": [
        "research", "data analysis", "communication",
        "writing", "regulatory compliance", "presentation",
        "strategic planning",
    ],
    # ── Fitness / Sports ──────────────────────────────────────
    "personal trainer": [
        "communication", "customer service", "first aid",
        "teamwork", "adaptability", "leadership",
    ],
    "sports coach": [
        "leadership", "communication", "teamwork",
        "strategic thinking", "training", "mentoring",
    ],
    "sports analyst": [
        "data analysis", "statistics", "excel", "python",
        "communication", "presentation", "research",
    ],
    # ── Executive / C-Suite ───────────────────────────────────
    "chief executive officer": [
        "leadership", "strategic planning", "communication",
        "stakeholder management", "budgeting", "decision making",
        "negotiation", "presentation",
    ],
    "chief technology officer": [
        "leadership", "strategic planning", "python", "aws",
        "docker", "communication", "agile", "stakeholder management",
    ],
    "chief financial officer": [
        "financial analysis", "budgeting", "leadership",
        "strategic planning", "financial reporting", "communication",
        "accounting", "compliance",
    ],
    "chief marketing officer": [
        "digital marketing", "strategic planning", "leadership",
        "brand management", "communication", "data analysis",
        "google analytics", "presentation",
    ],
    "chief operating officer": [
        "leadership", "strategic planning", "budgeting",
        "communication", "decision making", "stakeholder management",
        "project management", "risk management",
    ],
    "vice president": [
        "leadership", "strategic planning", "communication",
        "stakeholder management", "budgeting", "presentation",
        "decision making", "negotiation",
    ],
    "director": [
        "leadership", "strategic planning", "budgeting",
        "communication", "stakeholder management", "project management",
        "decision making", "presentation",
    ],
    # ── Data roles (expanded) ─────────────────────────────────
    "data analyst": [
        "sql", "excel", "python", "data analysis", "tableau",
        "power bi", "communication", "problem solving", "analytical skills",
    ],
    "data engineer": [
        "python", "sql", "aws", "docker", "postgresql", "mongodb",
        "data analysis", "git", "linux", "agile", "kafka", "spark",
    ],
    "business intelligence analyst": [
        "sql", "tableau", "power bi", "data analysis", "excel",
        "communication", "data visualization", "python",
    ],
    "data architect": [
        "sql", "data warehousing", "python", "aws", "snowflake",
        "bigquery", "data pipeline", "communication", "etl",
    ],
    "analytics engineer": [
        "sql", "python", "dbt", "data pipeline", "git",
        "data analysis", "communication", "snowflake",
    ],
    # ── Consulting ────────────────────────────────────────────
    "management consultant": [
        "communication", "presentation", "excel", "powerpoint",
        "data analysis", "problem solving", "project management",
        "leadership", "strategic planning", "teamwork",
    ],
    "it consultant": [
        "communication", "project management", "aws",
        "networking", "problem solving", "sql", "python",
        "presentation", "agile",
    ],
    "strategy consultant": [
        "strategic planning", "data analysis", "communication",
        "presentation", "excel", "problem solving",
        "market research", "leadership",
    ],
    # ── Additional roles for 200+ coverage ────────────────────────
    "librarian": [
        "research", "organizational skills", "communication",
        "customer service", "attention to detail", "writing",
        "microsoft office", "data analysis",
    ],
    "social worker": [
        "communication", "critical thinking", "problem solving",
        "writing", "interpersonal skills", "conflict resolution",
        "organizational skills", "teamwork",
    ],
    "occupational therapist": [
        "patient care", "communication", "problem solving",
        "attention to detail", "teamwork", "adaptability",
        "medical terminology",
    ],
    "speech therapist": [
        "patient care", "communication", "problem solving",
        "attention to detail", "medical terminology", "adaptability",
    ],
    "dietitian": [
        "patient care", "communication", "data analysis",
        "research", "attention to detail", "medical terminology",
    ],
    "security guard": [
        "communication", "customer service", "first aid",
        "conflict resolution", "attention to detail", "teamwork",
    ],
    "plumber": [
        "problem solving", "customer service", "communication",
        "attention to detail", "time management",
    ],
    "electrician": [
        "electrical design", "problem solving", "communication",
        "attention to detail", "customer service", "time management",
    ],
    "hvac technician": [
        "problem solving", "customer service", "communication",
        "attention to detail", "electrical design", "time management",
    ],
    "welder": [
        "attention to detail", "quality control", "teamwork",
        "communication", "problem solving",
    ],
    "insurance underwriter": [
        "risk assessment", "financial analysis", "analytical skills",
        "attention to detail", "communication", "excel",
    ],
    "actuary": [
        "statistics", "data analysis", "python", "excel",
        "financial modeling", "risk assessment", "communication",
    ],
    "technical writer": [
        "writing", "communication", "research", "attention to detail",
        "html", "css", "microsoft office", "content creation",
    ],
    "translator": [
        "communication", "writing", "attention to detail",
        "research", "proofreading", "organizational skills",
    ],
    "barista": [
        "customer service", "communication", "multitasking",
        "teamwork", "attention to detail",
    ],
    "receptionist": [
        "customer service", "communication", "microsoft office",
        "organizational skills", "multitasking", "attention to detail",
    ],
    "dental assistant": [
        "patient care", "communication", "attention to detail",
        "medical records", "customer service", "teamwork",
    ],
    "optometrist": [
        "patient care", "communication", "attention to detail",
        "medical terminology", "customer service", "problem solving",
    ],
    "radiologist": [
        "medical imaging", "patient care", "attention to detail",
        "communication", "medical terminology", "clinical research",
    ],
    "nurse practitioner": [
        "patient care", "clinical research", "medical terminology",
        "communication", "decision making", "leadership",
        "electronic health records",
    ],
    "physiotherapist": [
        "patient care", "communication", "problem solving",
        "medical terminology", "teamwork", "adaptability",
    ],
}


def train_from_all_datasets(data_dir: str) -> dict:
    """Process all datasets and build comprehensive role-skill templates."""

    all_role_skills: Dict[str, Counter] = defaultdict(Counter)
    all_extracted_skills: Set[str] = set()
    global_skill_counter = Counter()
    total_processed = 0

    # ── Source 1: Resume dataset (962 resumes) ────────────────────────
    resume_path = os.path.join(data_dir, 'UpdatedResumeDataSet.csv')
    if os.path.exists(resume_path):
        print("  [1/3] Processing UpdatedResumeDataSet.csv...")
        category_map = {
            'Java Developer': 'java developer',
            'Python Developer': 'python developer',
            'Web Designing': 'web designer',
            'DevOps Engineer': 'devops engineer',
            'Data Science': 'data scientist',
            'Testing': 'qa engineer',
            'Automation Testing': 'test automation engineer',
            'HR': 'hr coordinator',
            'Sales': 'sales representative',
            'Operations Manager': 'operations manager',
            'Business Analyst': 'business analyst',
            'Hadoop': 'big data engineer',
            'Blockchain': 'blockchain developer',
            'ETL Developer': 'etl developer',
            'DotNet Developer': 'dotnet developer',
            'Database': 'database administrator',
            'Network Security Engineer': 'network security engineer',
            'Mechanical Engineer': 'mechanical engineer',
            'Electrical Engineering': 'electrical engineer',
            'Civil Engineer': 'civil engineer',
            'Health and fitness': 'health and fitness professional',
            'PMO': 'project manager',
            'SAP Developer': 'sap developer',
            'Arts': 'creative professional',
            'Advocate': 'lawyer',
        }
        with open(resume_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat = row.get('Category', '').strip()
                role = category_map.get(cat, cat.lower())
                skills = extract_skills_from_text(row.get('Resume', ''))
                noisy = {"less", "windows", "go", "teams", "assembly", "transformer"}
                skills = skills - noisy
                for skill in skills:
                    all_role_skills[role][skill] += 1
                    global_skill_counter[skill] += 1
                all_extracted_skills.update(skills)
                total_processed += 1
        print(f"    → {total_processed} resumes processed")

    # ── Source 2: Job titles + skills (289 roles) ─────────────────────
    jobs_path = os.path.join(data_dir, 'job_titles_skills.csv')
    if os.path.exists(jobs_path):
        print("  [2/3] Processing job_titles_skills.csv...")
        count = 0
        with open(jobs_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get('Job Title', '').strip().lower()
                # Normalize to reduce tool-specific duplicates
                title = _normalize_title(title)
                if not title:
                    continue
                skill_text = row.get('Skills', '')
                desc = row.get('Job Description', '')

                # Parse labeled skills
                labeled_skills = [s.strip().lower() for s in skill_text.split(',') if s.strip()]

                # Also extract from description
                extracted = extract_skills_from_text(desc + ' ' + skill_text)
                noisy = {"less", "windows", "go", "teams", "assembly", "transformer"}
                extracted = extracted - noisy

                all_skills = set(labeled_skills) | extracted
                for skill in all_skills:
                    all_role_skills[title][skill] += 1
                    global_skill_counter[skill] += 1
                all_extracted_skills.update(all_skills)
                count += 1
                total_processed += 1
        print(f"    → {count} labeled job roles processed")

    # ── Source 3: Job descriptions (853 postings) ─────────────────────
    jd_path = os.path.join(data_dir, 'job_descriptions.csv')
    if os.path.exists(jd_path):
        print("  [3/3] Processing job_descriptions.csv...")
        count = 0
        with open(jd_path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                title = row.get('position_title', '').strip().lower()
                desc = row.get('job_description', '')
                model_resp = row.get('model_response', '')

                # Normalize similar titles
                title = _normalize_title(title)
                if not title:
                    continue

                skills = extract_skills_from_text(desc + ' ' + model_resp)
                noisy = {"less", "windows", "go", "teams", "assembly", "transformer"}
                skills = skills - noisy

                for skill in skills:
                    all_role_skills[title][skill] += 1
                    global_skill_counter[skill] += 1
                all_extracted_skills.update(skills)
                count += 1
                total_processed += 1
        print(f"    → {count} job descriptions processed")

    # ── Source 4: Manual templates ────────────────────────────────────
    print("  [+] Adding hand-curated templates...")
    manual_count = 0
    for role, skills in MANUAL_ROLE_TEMPLATES.items():
        if role not in all_role_skills or len(all_role_skills[role]) < 3:
            for skill in skills:
                all_role_skills[role][skill] += 5  # Weight manual entries
                global_skill_counter[skill] += 1
            all_extracted_skills.update(skills)
            manual_count += 1
    print(f"    → {manual_count} manual templates added")

    print(f"\n  Total entries processed: {total_processed}")
    print(f"  Total unique skills: {len(all_extracted_skills)}")
    print(f"  Total raw role entries: {len(all_role_skills)}")

    return {
        'role_skills': {k: dict(v) for k, v in all_role_skills.items()},
        'global_frequencies': dict(global_skill_counter),
        'all_skills': sorted(all_extracted_skills),
        'total_processed': total_processed,
    }


def _normalize_title(title: str) -> str:
    """Aggressively normalize job titles to reduce duplicates."""
    title = title.lower().strip()
    # Remove parenthetical content
    title = re.sub(r'\s*\([^)]*\)', '', title)
    # Remove everything after dash, comma, pipe, slash-alt, or "at/for/in/with"
    title = re.sub(r'\s*[-–|].*$', '', title)
    title = re.sub(r',\s*.+$', '', title)
    title = re.sub(r'\s+at\s+.+$', '', title)
    title = re.sub(r'\s+for\s+.+$', '', title)
    title = re.sub(r'\s+in\s+\w+\s*$', '', title)
    title = re.sub(r'\s+with\s+.+$', '', title)
    # Remove "/ alternative" patterns like "developer / programmer"
    title = re.sub(r'\s*/\s*\w[\w\s]*$', '', title)
    # Remove remote/hybrid/part-time/full-time qualifiers
    title = re.sub(r'\b(remote|hybrid|onsite|on-site|part-time|full-time|'
                   r'part time|full time|entry level|entry-level|ft|pt|'
                   r'casual|seasonal|temp|temporary|contract|freelance|'
                   r'100%|permanent)\b', '', title)
    # Remove seniority prefixes for merging (keep chief/executive/vp — they're role names)
    title = re.sub(r'^(senior|sr\.?|jr\.?|junior|lead|principal|staff|'
                   r'intern|global|regional)\s+', '', title)
    # Remove trailing roman numerals, numbers, letters
    title = re.sub(r'\s+(i{1,3}|iv|v|vi{0,3})\s*$', '', title)
    title = re.sub(r'\s+\d+\w*$', '', title)
    title = re.sub(r'\s+[a-z]\s*$', '', title)
    # Remove trailing special chars
    title = re.sub(r'\s*[/&:]\s*$', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    # Skip overly specific or garbage titles
    if len(title) > 45 or len(title) < 4:
        return ''
    if any(kw in title for kw in ['!', '~', '$', 'www.', 'http',
                                    'work from home', 'hiring',
                                    'positions', 'openings', 'r0',
                                    'team member', 'crew member',
                                    'holman', 'judge group',
                                    'waitlist', 'phoenix',
                                    'pagoda', 'richmond',
                                    'janitor', 'dishwasher',
                                    'cleaner', 'driver', 'installer',
                                    'cdl', 'dump truck',
                                    'mount royal', 'sylmar',
                                    'vans ', 'allstate',
                                    'kitchen exhaust',
                                    'astonishing', 'strength &',
                                    'hosts', 'hostesses']):
        return ''
    return title


def build_role_templates(results: dict, min_skills: int = 3) -> Dict[str, List[str]]:
    """Build deduplicated role templates from aggregated data."""

    # ── Step 1: Normalize all role names first ────────────────────
    # Merge skills from roles that normalize to the same base title
    normalized_skills: Dict[str, Counter] = defaultdict(Counter)
    role_skills = results['role_skills']

    for role, skill_counts in role_skills.items():
        base = _normalize_title(role)
        if not base:
            continue
        for skill, count in skill_counts.items():
            normalized_skills[base][skill] += count

    # ── Step 2: Tool-specific role → broader category mapping ────
    # Many datasets list tool-specific roles like "docker engineer";
    # merge these into standard industry roles.
    _DEVOPS_TOOLS = [
        'ansible', 'artifactory', 'bamboo', 'bitbucket', 'chef',
        'confluence', 'consul', 'docker', 'elk', 'envoy', 'falco',
        'fluentd', 'fortify', 'gerrit', 'git', 'github', 'gitlab',
        'gradle', 'grafana', 'groovy', 'helm', 'istio', 'jenkins',
        'kubernetes', 'maven', 'nagios', 'new relic', 'nexus', 'nomad',
        'notary', 'octopus deploy', 'openshift', 'openstack', 'packer',
        'powershell', 'puppet', 'splunk', 'terraform', 'xl deploy',
        'zabbix', 'datadog', 'windows packaging',
    ]
    _QA_TOOLS = ['coverage.py', 'jacoco', 'junit', 'selenium', 'cypress',
                 'jest', 'pytest', 'testng', 'appium', 'salesforce.com qa']

    # Pattern: "<tool> engineer/administrator/specialist" → canonical role
    tool_merge_targets: Dict[str, str] = {}
    for tool in _DEVOPS_TOOLS:
        for suffix in ['engineer', 'administrator', 'specialist',
                       'operations engineer', 'automation engineer']:
            tool_merge_targets[f'{tool} {suffix}'] = 'devops engineer'
    for tool in _QA_TOOLS:
        for suffix in ['engineer', 'tester', 'specialist']:
            tool_merge_targets[f'{tool} {suffix}'] = 'qa engineer'

    # ── Step 3: Explicit merge groups (consolidated, no duplicate keys) ──
    _MERGE_GROUPS = {
        # ── Software Engineering ──────────────────────────────
        'software engineer': [
            'software developer', 'software eng', 'coder',
            'computer programmer', 'programmer', 'software development',
            'software engineering', 'full stack software engineer',
            'system software development engineer', 'software development engineer',
            'systems programmer', 'statistical programmer',
            'application development', 'engineering lead', 'technical lead',
            'associate software engineering',
        ],
        'full stack developer': [
            'full stack web developer', 'full stack java developer',
            'full stack python developer',
        ],
        'web developer': [
            'web designer', 'web dev', 'website designer', 'webmaster',
            'web engineer', 'html and wordpress developer',
            'wordpress developer', 'wordpress web developer',
            'web content manager', 'web producer', 'web project manager',
            'front-end designer', 'ui web designer', 'web analytics developer',
        ],
        'front end developer': ['frontend web developer', 'frontend developer'],
        'back end developer': ['backend developer'],
        'mobile developer': [
            'mobile app developer', 'ios developer', 'android developer',
        ],
        'embedded software engineer': ['embedded systems engineer', 'embedded c++ developer'],

        # ── DevOps & Cloud ────────────────────────────────────
        'devops engineer': [
            'aws devops engineer', 'azure devops engineer',
            'gcp devops engineer', 'devsecops engineer',
            'devsecops architect', 'devops architect', 'devops manager',
            'build and release engineer', 'build engineer',
            'platform engineer', 'operations engineer',
            'site reliability engineer',
            'chef inspec engineer', 'chef operations engineer',
        ],
        'cloud architect': [
            'aws solutions architect', 'cloud administrator',
            'cloud automation engineer', 'cloud computing specialist',
            'cloud migration specialist', 'cloud network engineer',
            'cloud security engineer', 'cloud system administrator',
            'cloud system engineer', 'cloud/software architect',
            'cloud/software developer', 'cloud/software applications engineer',
            'infrastructure architect',
        ],

        # ── Data & AI ─────────────────────────────────────────
        'data scientist': ['data science specialist'],
        'data analyst': [
            'data analyst manager', 'data management analyst',
            'power bi analyst', 'data analytics senior mangager',
            'power bi developer', 'computer forensic analyst',
            'fraud systems analyst', 'grc product risk analyst',
            'analytics manager',
        ],
        'data engineer': [
            'data quality engineer', 'data warehouse programming specialist',
            'data modeler', 'data warehouse manager', 'datadog engineer',
        ],
        'database administrator': [
            'database analyst', 'database architect', 'database developer',
        ],
        'machine learning engineer': [
            'machine learning architect',
            'machine learning engineer for cybersecurity',
            'principle engineer in machine learning',
        ],
        'ai engineer': [
            'artificial intelligence engineer',
            'artificial intelligence architect',
            'ai software architect', 'artificial intelligence researcher',
            'artificial intelligence', 'ai researcher',
            'principle engineer in artificial intelligence',
            'natural language processing engineer',
        ],
        'big data engineer': [
            'big data architect', 'big data specialist',
            'admin big data', 'principle engineer in big data',
            'principle engineer in data analysis',
        ],
        'data entry clerk': [
            'data entry', 'data entry operator', 'data entry specialist',
            'data entry/auditor',
        ],

        # ── Security ──────────────────────────────────────────
        'cybersecurity analyst': [
            'cybersecurity engineer', 'cybersecurity specialist',
            'information security analyst', 'infosec analyst',
            'security analyst', 'security specialist',
            'security engineer', 'security consultant',
            'security administrator', 'security manager',
            'it security specialist', 'mobile security specialist',
            'data security engineer', 'director of security',
            'application security engineer',
        ],
        'network engineer': [
            'network analyst', 'network architect',
            'network infrastructure specialist', 'network operations engineer',
            'network reliability engineer', 'network system administrator',
            'network systems admin', 'network and systems administrator',
            'computer network architect', 'computer network specialist',
            'internet engineer',
        ],
        'network security engineer': ['penetration tester'],

        # ── IT & Support ──────────────────────────────────────
        'system administrator': [
            'systems administrator', 'linux administrator',
            'windows system administrator', 'cloud system administrator',
            'information technology system administrator',
            'it systems administrator', 'executive administrator',
        ],
        'it support specialist': [
            'computer support specialist', 'help desk technician',
            'it technician', 'it help desk technical support agent',
            'technical support representative', 'technical support agent',
            'tech support agent', 'technology specialist',
            'technology assistant',
        ],
        'it manager': [
            'it director', 'technology manager', 'technology officer',
            'information management systems director',
        ],
        'it consultant': [
            'erp consultant', 'sap consultant',
            'digital transformation consultant',
            'ecommerce consultant', 'seo consultant',
        ],

        # ── Project / Product Management ──────────────────────
        'project manager': [
            'pmo', 'program manager', 'program coordinator',
            'program director', 'agile project manager',
            'construction project manager', 'construction project managers',
            'digital development project manager',
            'environmental project manager',
            'infrastructure services project manager',
            'web project manager', 'digital program manager',
            'it project manager', 'water resources project manager',
            'contracting project management intern',
            'business development project manager',
            'project management administrator', 'project managers',
            'iteration manager', 'project manager 100%',
            'associate project manager',
        ],
        'product manager': ['technical product manager'],

        # ── Sales ─────────────────────────────────────────────
        'sales representative': [
            'sales associate', 'sales professional', 'sales specialist',
            'sales intern', 'field sales representative',
            'sales service representative', 'commission sales associate',
            'retail commission sales associate',
            'furniture sales associate', 'furniture sales associates',
            'retail cashier & sales floor support',
            'sales representatives', 'retail sales associate',
            'luxury sales stylist', 'sales leader',
            'retail furniture sales consultant',
            'vans retail sales associate',
            'real estate sales agent',
            'real estate acquisitions sales associate',
            'creative real estate agent',
        ],
        'sales manager': [
            'regional sales manager', 'regional sales director',
            'assistant sales manager', 'workday sales director',
        ],
        'sales executive': [
            'enterprise sales executive', 'field sales account executive',
            'outside sales executive', 'business sales account executive',
            'sales executive fiber', 'migrations sales executive',
            'it sales executive', 'it sales director',
            'technology sales consultant',
        ],
        'account executive': [
            'account delivery manager', 'clinical account executive',
            'catering sales executive',
        ],
        'account manager': [
            'ecommerce account manager', 'technical account manager',
        ],
        'business development manager': [
            'business development representative',
            'business development specialist',
            'business development associate',
            'business development executive',
            'business development center representative',
            'business development sales representative',
            'global business development',
            'manager business development',
            'business development & sales analyst',
            'business development manager private equity',
        ],

        # ── Marketing ─────────────────────────────────────────
        'marketing manager': [
            'marketing director', 'marketing coordinator',
            'marketing specialist', 'marketing advisor',
            'marketing visionary', 'marketing intern',
            'b2b marketing manager', 'marketing analytics manager',
            'marketing and visuals manager', 'marketing event coordinator',
            'marketing program manager', 'marketing project intern',
            'marketing content specialist', 'integrated marketing',
            'marketing communications intern', 'marketing & communications intern',
            'growth marketing specialist', 'performance marketing specialist',
            'sales & marketing specialist', 'sales and marketing coordinator',
            'sales and marketing representative', 'sales marketing specialist',
            'us sales & marketing', 'digital marketing sales',
            'marketing officer', 'vice president of marketing',
            'marketing',
        ],
        'digital marketing specialist': [
            'digital marketing internship', 'email marketing specialist',
            'seo manager', 'search optimization',
        ],
        'product marketing manager': ['pharmacy marketing representative'],
        'graphic designer': [
            'motion graphics artist', 'graphic effects supervisor',
            'layout artist', 'character designer', 'advertising design intern',
        ],
        'ui/ux designer': [
            'ui designer', 'ui (user interface) designer',
            'ux/ui designer', 'ux/ui specialist', 'ux/ui researcher',
            'interaction designer', 'application designer',
            'design consultant',
        ],
        'content creator': [
            'social content creator', 'live content creator',
        ],

        # ── Finance ───────────────────────────────────────────
        'accountant': [
            'accounting clerk', 'staff accountant',
            'audit staff accountant', 'accounts receivable',
        ],
        'financial analyst': [
            'finance analyst', 'fraud resolution analyst',
            'financial professional', 'director finance',
            'director financial business management',
            'director of finance', 'vp of finance',
        ],
        'investment banker': [
            'investment research', 'global investment research',
            'investment service partner',
            'real estate investment management associate',
        ],

        # ── Executive ─────────────────────────────────────────
        'chief executive officer': [
            'ceo', 'ceo/co', 'fractional ceo',
            'executive assistant to ceo', 'executive assistant to the ceo',
            'assistant to the ceo',
        ],
        'chief technology officer': ['cto', 'chief technology officer (cto)'],
        'chief financial officer': [
            'cfo', 'vice president & chief financial officer',
        ],
        'chief operating officer': [
            'coo', 'vice president of operations',
            'vice president operations', 'vice president operations excellence',
        ],
        'chief marketing officer': [
            'vice president marketing', 'vp marketing',
            'vp marketing & growth',
        ],
        'chief information officer': ['chief information officer (cio)'],
        'vice president': [
            'vp', 'pca & esa vice president',
            'vice president and managing director',
            'vice president/general manager',
            'vp client development', 'associate director',
        ],
        'director': [
            'managing director', 'implementation director',
            'integration director', 'director of development',
            'director of strategy & external relations',
            'director/head of strategy and business operations',
            'director hardware', 'director oracle',
            'art director', 'video art director',
            'director business systems', 'director of engineering',
        ],

        # ── Admin / Support ───────────────────────────────────
        'executive assistant': [
            'administrative assistant', 'administrative assistant iii',
            'administrative executive assistant',
            'executive administrative assistant',
            'office assistant', 'office clerk', 'general office clerk',
            'general clerk', 'clerical assistant', 'clerical',
            'office specialist', 'office administrator',
            'virtual administrative assistant',
            'site administrative assistant',
            'healthcare administrative assistant',
            'executive assistant to president', 'executive coordinator',
        ],
        'customer service representative': [
            'customer service', 'customer service professional',
            'customer service associate', 'customer channel service representative',
            'customer care embracer', 'customer support agent',
            'customer support specialist', 'customer experience specialist',
            'inbound customer service representative',
            'ccrd customer service representative',
            'customer service representative l2',
            'inbound customer service / sales',
            'customer service/sales',
            'customer service representative / inside sales',
            'customer service sales associate',
            'logistics customer service rep',
        ],
        'call center manager': [
            'fraud support call center representative',
            'inbound claims & call center representative',
        ],

        # ── HR ────────────────────────────────────────────────
        'recruiter': [
            'corporate recruiter', 'tech recruiter',
            'technical sourcing recruiter', 'talent acquisition advisor',
            'talent acquisition manager', 'talent acquisition recruiter',
            'talent acquisition specialist',
        ],
        'hr manager': [
            'hr director', 'hr generalist', 'human resources manager',
            'human resources director', 'human resources generalist',
            'human resources internship', 'hr business partner',
            'hr initiatives program lead', 'director human resources',
            'human resource coordinator',
        ],

        # ── Healthcare ────────────────────────────────────────
        'registered nurse': [
            'travel nurse', 'nursing assistant', 'nurse practitioner',
            'travel registered nurse', 'bilingual occupational registered nurse',
            'nurse administrator', 'rn supervisor', 'rn case manager',
            'assistant rn manager telemetry',
            'registered nurse mount royal',
            'sylmar certified nursing assistant cna',
            'nurse',
        ],
        'medical assistant': [
            'medical receptionist', 'medical office specialist',
            'patient care tech', 'patient access representative',
            'patient services specialist', 'medicaid fraud intake officer',
        ],
        'health and fitness professional': ['health solutions'],

        # ── Operations ────────────────────────────────────────
        'operations manager': ['strategic operations manager'],
        'compliance officer': [
            'compliance manager', 'compliance director',
            'program compliance manager', 'fraud & compliance',
            'analyst compliance',
        ],
        'restaurant manager': [
            'restaurant operations manager', 'restaurant team member',
        ],
        'warehouse manager': [
            'warehouse supervisor', 'warehouse management specialist',
        ],
        'supply chain analyst': ['supply chain analyst iv'],
        'construction manager': ['commercial construction manager'],
        'property manager': [
            'vice president of property management', 'vp real estate',
        ],

        # ── Investigator (merge all niche variants) ──────────
        'investigator': [
            'background investigator', 'civil rights investigator',
            'claims investigator', 'criminal investigator',
            'diversion investigator', 'fraud investigator',
            'private investigator', 'public investigator',
            'surveillance investigator', 'investigator support assistant',
            'organized retail crime investigator',
        ],

        # ── Misc ──────────────────────────────────────────────
        'teacher': ['art teacher', 'teachers', 'associate professor'],
        'business analyst': [
            'business systems analyst', 'systems analyst',
            'business associate', 'information technology analyst',
            'computer systems analyst',
        ],
        'business intelligence analyst': [
            'vice president of business intelligence',
            'business intelligence developer',
        ],
        'management consultant': [
            'management consulting director', 'strategy consultant',
            'strategy lead', 'consultant',
        ],
        'research scientist': [
            'computer and information research manager',
            'computer and information research scientist',
            'computer research scientist',
        ],
        'animator': [
            '2d artist/animator', '3d artist/animator', 'forensic animator',
            'technical animator', 'visual effects animator',
            'computer graphics animator', 'animation director',
        ],
        'case manager': [
            'di case manager', 'new business case manager',
            'medical case manager', 'associate new business case manager',
        ],
        'career coach': [
            'career coach counselor', 'career services coach',
            'career specialist instructor', 'job coach',
            'youth career coach', 'career coach waitlist',
            'college and career advisor',
        ],
        'real estate attorney': [
            'commercial real estate attorney',
            'large law real estate associate attorney',
        ],
        'lawyer': [
            'commercial contracts lawyer', 'commercial contracts attorney',
            'enforcement attorney', 'commercial counsel',
        ],
        'ecommerce manager': ['ecommerce engineer'],
        'clinical educator': [
            'cardiology clinical educator', 'perioperative educator',
            'fraud awareness educator', 'brand educator',
        ],
        'equity research analyst': [
            'equity research associate',
            'equity research biotech associate',
            'biotech equity research associate',
        ],
        'software architect': ['python architect', 'java architect'],
        'java developer': ['java software engineer'],
        'oracle developer': ['oracle sql developer'],
        'technical support engineer': ['production support engineer'],
        'it engineer': ['it apprentice'],
        'fitness coach': ['personal trainer', 'sports coach'],
        'mainframe developer': ['mainframe programmer analyst'],
        'geographic information systems analyst': ['gis analyst'],
        'software quality assurance analyst': ['software test engineer'],
        'credit analyst': ['credit collections lead'],
        'healthcare administrator': ['school administrator'],
    }

    # Apply tool-role merges first
    for role in list(normalized_skills.keys()):
        target = tool_merge_targets.get(role)
        if target:
            for skill, count in normalized_skills[role].items():
                normalized_skills[target][skill] += count
            del normalized_skills[role]

    # Apply explicit merge groups
    for canonical, variants in _MERGE_GROUPS.items():
        for variant in variants:
            norm_variant = _normalize_title(variant) or variant
            # Check both normalized and raw variant
            for check in [variant, norm_variant]:
                if check in normalized_skills and check != canonical:
                    for skill, count in normalized_skills[check].items():
                        normalized_skills[canonical][skill] += count
                    del normalized_skills[check]

    # ── Step 4: Build templates from merged data ──────────────────
    raw_templates = {}
    for role, skill_counts in normalized_skills.items():
        if not role or len(role) < 4:
            continue
        sorted_skills = sorted(skill_counts.items(), key=lambda x: -x[1])
        skills = [s for s, _ in sorted_skills[:20]]
        if len(skills) >= min_skills:
            raw_templates[role] = skills

    # ── Step 5: Filter out noisy / garbage roles ──────────────────
    _SKIP_WORDS = {
        'flex', 'front', 'full', 'part', 'multi', 'entry', 'nam',
        'mgr', 'selling', 'collections', 'acquisitions', 'governance',
        'litigation', 'principals', 'federal', 'advocate', 'associate',
        'hosts', 'hostesses', 'compositor', 'registrar', 'teller',
        'storyboard artist', 'rigging artist', 'vfx artist',
        'effects technical director', 'polygraph examiner',
        'kitchen exhaust', 'licensing coordinator',
        'field placement coordinator', 'coach', 'coordinator',
        'of staff', 'executive officer', 'information officer',
        'operating officer', 'financial officer',
        'special agent', 'development associate',
        'frameworks specialist', 'escalations specialist',
        'intelligence specialist', 'accessibility specialist',
        'automation specialist', 'card fraud', 'fraud representative',
        'bilingual care advocate', 'patient advocate specialist',
        'patient engagement liaison', 'education advocate',
        'knowledge manager', 'sharepoint manager', 'release manager',
        'firmware manager', 'new business manager',
        'technology adoption manager', 'requirements manager',
        'service manager', 'assistant controller',
        'advisory strategic resource manager', 'academic dean',
        'assistant manager', 'assurance senior',
        'therapeutic coach team lead', 'travel stna',
        'management internship', 'testing monitor', 'test center monitor',
        'manager', 'business development manager private equity',
    }
    _SKIP_PATTERNS = [
        r'\bat\s+\w+',        # "at [company]"
        r'\bspecialist\s+\d',  # "specialist 2"
        r'\blevel\s+\d',       # "level 3"
        r'\bphase\s+\d',
        r'\bremote\b',
        r'\bhybrid\b',
        r'work from home',
        r'\bteam\s+member\b',
        r'\bcrew\b',
        r'\br\d{4}',           # "r0049: ..."
        r'manager\s+(e|net|php|unix|linux|hardware|ecommerce)$',
        r'^(dir|nam)\s+',
        r'clerk$',
        r'assistant$',
        r'principle\s+engineer\s+in',  # Too niche
        r'^\w+\s+\d+%?$',     # "project manager 100%"
        r'certified nursing',
        r'mental health worker',
        r'stna$',
        r'crime\s+investigator',
        r'broadcast\s+media',
        r'solution\s+sales$',
        r'bulk\s+product',
        r'^cnc\s+programmer',  # Let "cnc programmer" stay as one
        r'engagement\s+director$',
        r'directory\s+business',
        r'sap\s+alliance',
        r'loss\s+prevention',
        r'identity\s+and\s+access',
    ]

    templates = {}
    for role, skills in raw_templates.items():
        # Skip exact garbage words
        if role in _SKIP_WORDS:
            continue
        # Skip pattern matches
        if any(re.search(p, role) for p in _SKIP_PATTERNS):
            continue
        # Skip overly long titles
        if len(role) > 45:
            continue
        # Skip single-word generic titles (only keep well-known roles)
        if ' ' not in role and role not in {
            'accountant', 'animator', 'architect', 'auditor',
            'barista', 'chef', 'chemist', 'copywriter', 'dietitian',
            'doctor', 'editor', 'electrician', 'journalist', 'lawyer',
            'librarian', 'optometrist', 'paralegal', 'pharmacist',
            'photographer', 'physiotherapist', 'plumber', 'radiologist',
            'realtor', 'receptionist', 'recruiter', 'teacher',
            'translator', 'tutor', 'veterinarian', 'welder',
        }:
            continue
        templates[role] = skills[:15]  # Cap at 15 skills per role

    return templates


def build_keyword_map(templates: Dict[str, List[str]]) -> List[Tuple[List[str], str]]:
    """Build keyword → role mapping for fuzzy role detection."""
    keyword_map = []

    for role in sorted(templates.keys()):
        keywords = [role]  # Full name always

        # Generate additional keyword fragments
        words = role.split()
        if len(words) >= 2:
            # Add first two words as a phrase
            keywords.append(' '.join(words[:2]))
        if len(words) >= 3:
            keywords.append(' '.join(words[:3]))

        # Add common abbreviations / alternates
        alternates = {
            'software engineer': ['software eng', 'swe'],
            'software developer': ['software dev'],
            'frontend developer': ['frontend', 'front end', 'front-end'],
            'backend developer': ['backend', 'back end', 'back-end'],
            'full stack developer': ['full stack', 'fullstack', 'full-stack'],
            'devops engineer': ['devops', 'dev ops'],
            'qa engineer': ['qa ', 'quality assurance'],
            'database administrator': ['dba', 'database admin'],
            'machine learning engineer': ['ml engineer', 'ml develop'],
            'project manager': ['project manag', 'pmo'],
            'product manager': ['product manag'],
            'data scientist': ['data scien'],
            'data analyst': ['data analy'],
            'business analyst': ['business analy'],
            'hr manager': ['human resource manag'],
            'hr coordinator': ['human resource coord', 'hr coord'],
            'recruiter': ['talent acquisition', 'recruiting'],
            'sales manager': ['sales manag'],
            'marketing': ['marketing manag'],
        }

        if role in alternates:
            keywords.extend(alternates[role])

        keyword_map.append((keywords, role))

    return keyword_map


def generate_python_module(templates: dict, results: dict, output_path: str):
    """Generate the trained_skills.py module."""

    # Build domain-grouped skill dictionary
    domain_mapping = {
        'programming_languages': 'technology',
        'web_frameworks': 'technology',
        'databases': 'technology',
        'cloud_devops': 'technology',
        'data_ml_ai': 'technology',
        'mobile': 'technology',
        'cybersecurity': 'technology',
        'testing_qa': 'technology',
        'version_control': 'technology',
        'networking': 'technology',
        'operating_systems': 'technology',
        'blockchain': 'technology',
        'project_management': 'business',
        'business_tools': 'business',
        'supply_chain_ops': 'business',
        'hr_recruitment': 'business',
        'marketing_skills': 'marketing',
        'design_tools': 'marketing',
        'media_communications': 'marketing',
        'finance_accounting': 'finance',
        'legal': 'finance',
        'healthcare': 'healthcare',
        'engineering': 'engineering',
        'education': 'general',
        'real_estate': 'business',
        'soft_skills': 'general',
        'languages': 'languages',
    }

    final_dict: Dict[str, Set[str]] = defaultdict(set)
    for skill in results['all_skills']:
        domain = categorize_skill(skill)
        target = domain_mapping.get(domain, 'general')
        final_dict[target].add(skill)

    # Build keyword map
    keyword_map = build_keyword_map(templates)

    with open(output_path, 'w') as f:
        f.write('"""\n')
        f.write('Auto-generated skill database trained on multiple datasets.\n')
        f.write(f'Total unique skills: {len(results["all_skills"])}\n')
        f.write(f'Total role templates: {len(templates)}\n')
        f.write(f'Data sources: Kaggle resumes, HuggingFace job titles, ')
        f.write('job descriptions, hand-curated expansions\n')
        f.write('"""\n\n')

        # TRAINED_SKILL_DICTIONARY
        f.write('TRAINED_SKILL_DICTIONARY: dict[str, list[str]] = {\n')
        for domain in sorted(final_dict.keys()):
            skills = sorted(final_dict[domain])
            f.write(f'    "{domain}": [\n')
            for i in range(0, len(skills), 6):
                chunk = skills[i:i+6]
                line = ', '.join(f'"{s}"' for s in chunk)
                f.write(f'        {line},\n')
            f.write('    ],\n')
        f.write('}\n\n')

        # TRAINED_ROLE_SKILL_TEMPLATES
        f.write(f'# {len(templates)} data-driven role-skill templates\n')
        f.write('TRAINED_ROLE_SKILL_TEMPLATES: dict[str, list[str]] = {\n')
        for role in sorted(templates.keys()):
            skills = templates[role]
            f.write(f'    "{role}": [\n')
            for i in range(0, len(skills), 5):
                chunk = skills[i:i+5]
                line = ', '.join(f'"{s}"' for s in chunk)
                f.write(f'        {line},\n')
            f.write('    ],\n')
        f.write('}\n\n')

        # TRAINED_ROLE_KEYWORD_MAP
        f.write(f'# {len(keyword_map)} keyword trigger mappings\n')
        f.write('TRAINED_ROLE_KEYWORD_MAP: list[tuple[list[str], str]] = [\n')
        for keywords, role in keyword_map:
            f.write(f'    ({keywords}, "{role}"),\n')
        f.write(']\n\n')

        # SKILL_FREQUENCIES
        f.write('SKILL_FREQUENCIES: dict[str, int] = {\n')
        top_skills = sorted(results['global_frequencies'].items(),
                            key=lambda x: -x[1])[:300]
        for skill, count in top_skills:
            f.write(f'    "{skill}": {count},\n')
        f.write('}\n')

    print(f"\n  Generated: {output_path}")
    print(f"  → {len(final_dict)} skill domains, "
          f"{sum(len(v) for v in final_dict.values())} skills")
    print(f"  → {len(templates)} role templates")
    print(f"  → {len(keyword_map)} keyword mappings")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, 'training_data')
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained_skills.py')

    print("=" * 70)
    print("  RESUMATCH AI — TRAINING PIPELINE v2")
    print("=" * 70)

    results = train_from_all_datasets(data_dir)
    templates = build_role_templates(results, min_skills=3)
    generate_python_module(templates, results, output_path)

    # Save raw results
    json_path = os.path.join(data_dir, 'training_results_v2.json')
    with open(json_path, 'w') as f:
        json.dump({
            'total_processed': results['total_processed'],
            'total_skills': len(results['all_skills']),
            'total_roles': len(templates),
            'roles': {k: v[:15] for k, v in templates.items()},
        }, f, indent=2)

    # Print category breakdown
    categories = defaultdict(list)
    for role in sorted(templates.keys()):
        r = role.lower()
        if any(kw in r for kw in ['ai ', 'artificial', 'machine learning',
               'data sci', 'nlp', 'computer vision', 'big data', 'deep learning']):
            categories['AI / Data Science'].append(role)
        elif any(kw in r for kw in ['data']):
            categories['Data / Analytics'].append(role)
        elif any(kw in r for kw in ['software', 'developer', 'engineer',
                 'devops', 'cloud', 'mobile', 'qa', 'java', 'python',
                 'dotnet', 'blockchain', 'database', 'etl', 'sap',
                 'web', 'frontend', 'backend', 'full stack',
                 'network', 'security', 'cyber', 'test', 'coder',
                 'programmer', 'admin', 'system', 'it ', 'architect']):
            categories['Technology'].append(role)
        elif any(kw in r for kw in ['product manag', 'project manag',
                 'scrum', 'agile']):
            categories['Product / Project Management'].append(role)
        elif any(kw in r for kw in ['market', 'graphic', 'ui', 'ux',
                 'design', 'creative', 'content', 'social media',
                 'copy', 'brand']):
            categories['Marketing / Creative'].append(role)
        elif any(kw in r for kw in ['sales', 'business develop', 'account manag',
                 'retail', 'e-commerce']):
            categories['Sales / Business Development'].append(role)
        elif any(kw in r for kw in ['financ', 'account', 'bank', 'invest',
                 'audit', 'tax', 'credit', 'treasury', 'insurance']):
            categories['Finance / Accounting'].append(role)
        elif any(kw in r for kw in ['doctor', 'nurs', 'pharm', 'health',
                 'dental', 'medic', 'physical therap', 'veterin']):
            categories['Healthcare'].append(role)
        elif any(kw in r for kw in ['lawyer', 'legal', 'paralegal',
                 'compliance', 'counsel']):
            categories['Legal'].append(role)
        elif any(kw in r for kw in ['teacher', 'professor', 'instruct',
                 'tutor', 'school']):
            categories['Education'].append(role)
        elif any(kw in r for kw in ['journal', 'public relation', 'video',
                 'podcast', 'photo', 'animat', 'music']):
            categories['Media / Arts'].append(role)
        elif any(kw in r for kw in ['hr ', 'recrui', 'talent', 'training']):
            categories['HR / Recruitment'].append(role)
        elif any(kw in r for kw in ['supply', 'logistics', 'warehouse',
                 'procure', 'inventory', 'quality']):
            categories['Operations / Supply Chain'].append(role)
        elif any(kw in r for kw in ['mechanical', 'electrical', 'civil',
                 'automotive', 'biomedic']):
            categories['Engineering (Non-Software)'].append(role)
        elif any(kw in r for kw in ['chef', 'restaurant', 'hotel',
                 'hospitality', 'travel', 'flight', 'event', 'tour',
                 'front desk', 'customer service']):
            categories['Hospitality / Service'].append(role)
        elif any(kw in r for kw in ['chief', 'ceo', 'cto', 'cfo', 'coo',
                 'vice president', 'director', 'vp ']):
            categories['Executive / C-Suite'].append(role)
        elif any(kw in r for kw in ['research', 'scientist', 'lab',
                 'chemist', 'environment']):
            categories['Science / Research'].append(role)
        elif any(kw in r for kw in ['real estate', 'property', 'construct',
                 'architect', 'interior']):
            categories['Real Estate / Construction'].append(role)
        else:
            categories['Other'].append(role)

    print(f"\n  {'═' * 60}")
    print(f"  ROLE COVERAGE BY INDUSTRY ({len(templates)} total)")
    print(f"  {'─' * 60}")
    for cat in sorted(categories.keys()):
        roles = categories[cat]
        print(f"\n  {cat} ({len(roles)} roles):")
        for r in sorted(roles):
            print(f"    • {r}")

    print(f"\n{'=' * 70}")
    print("  TRAINING COMPLETE")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
