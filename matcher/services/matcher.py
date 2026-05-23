import re

# Import ML matcher and rule-based skill extraction
from .ml_matcher import (
    MLMatcher, extract_skills as extract_skills_from_dict,
    infer_skills_from_role, get_role_profile, parse_jd_tiers,
    extract_raw_jd_tokens,
)
from .job_analyzer import JobAnalyzer
from .skill_extractor import SkillExtractor
from .recommendations import RecommendationGenerator
from .resume_sections import (
    parse_resume_sections, classify_skill_evidence,
    compute_evidence_summary, evidence_score_delta,
    EVIDENCE_SECTIONS,
)


class JobMatcher:
    """Match resume with job description and generate analysis."""
    
    def __init__(self):
        """
        Initialize JobMatcher with ML-enhanced matching.
        ML libraries (scikit-learn, sentence-transformers) are required.
        """
        # Initialize ML matcher - required for system to work
        try:
            self.ml_matcher = MLMatcher()
        except Exception as e:
            raise ImportError(
                f"Failed to initialize ML matcher. ML libraries are required. "
                f"Please install: pip install scikit-learn numpy sentence-transformers. "
                f"Error: {str(e)}"
            )
        
        # Initialize job analyzer
        self.job_analyzer = JobAnalyzer()
        
        # Expanded common skills keywords
        self.common_skills = [
            # Programming Languages
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin',
            'typescript', 'html', 'css', 'scala', 'perl', 'r', 'matlab', 'sql', 'pl/sql',
            # Web Technologies
            'react', 'angular', 'vue', 'node.js', 'nodejs', 'express', 'django', 'flask', 'fastapi',
            'spring', 'laravel', 'asp.net', 'jquery', 'bootstrap', 'tailwind', 'sass', 'less',
            # Databases
            'mysql', 'postgresql', 'mongodb', 'redis', 'oracle', 'sqlite', 'cassandra', 'dynamodb',
            'elasticsearch', 'neo4j', 'firebase', 'supabase',
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab',
            'ci/cd', 'terraform', 'ansible', 'chef', 'puppet', 'linux', 'unix', 'bash', 'shell',
            # Data & ML
            'machine learning', 'deep learning', 'data science', 'data analysis', 'pandas', 'numpy',
            'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'opencv', 'nlp', 'computer vision',
            # Mobile
            'react native', 'flutter', 'ios', 'android', 'xamarin', 'ionic',
            # Business Software & Tools
            'microsoft office', 'microsoft word', 'microsoft excel', 'microsoft powerpoint', 'microsoft teams',
            'microsoft planner', 'ms office', 'ms word', 'ms excel', 'ms powerpoint',
            'excel', 'word', 'powerpoint', 'outlook', 'sharepoint', 'onedrive', 'teams', 'planner',
            'google workspace', 'google docs', 'google sheets', 'google slides', 'gmail',
            'salesforce', 'sap', 'oracle', 'quickbooks', 'xero', 'hubspot', 'zoho',
            'tableau', 'power bi', 'qlik', 'looker', 'analytics', 'business intelligence',
            # Customer Service Platforms
            'zendesk', 'freshdesk', 'intercom', 'servicenow', 'helpdesk', 'freshservice',
            # HR / People Platforms
            'workday', 'bamboohr', 'peoplesoft', 'adp', 'greenhouse', 'lever', 'hris',
            # Finance / Accounting Software
            'netsuite', 'sage', 'myob', 'quickbooks', 'xero',
            # Marketing Tools
            'mailchimp', 'hootsuite', 'buffer', 'semrush', 'ahrefs', 'moz',
            'google analytics', 'google ads', 'facebook ads', 'meta ads',
            # CRM / Sales Tools
            'pipedrive', 'microsoft dynamics', 'zoho crm', 'freshsales',
            # Social Media & Marketing
            'social media', 'facebook', 'twitter', 'instagram', 'linkedin', 'tiktok', 'youtube',
            'digital marketing', 'content marketing', 'seo', 'sem', 'ppc', 'google ads',
            'email marketing', 'marketing automation', 'crm',
            # Design & Creative Tools
            'adobe photoshop', 'adobe illustrator', 'adobe indesign', 'adobe premiere', 'adobe after effects',
            'figma', 'sketch', 'canva', 'imovie', 'final cut pro', 'premiere pro',
            'video editing', 'photo editing', 'graphic design', 'ui/ux design',
            # Project Management & Collaboration
            'agile', 'scrum', 'kanban', 'jira', 'confluence', 'slack', 'microsoft teams',
            'asana', 'trello', 'basecamp', 'monday.com', 'notion', 'clickup',
            'microservices', 'rest api', 'graphql', 'soap', 'websocket',
            # Languages
            'french', 'spanish', 'german', 'italian', 'portuguese', 'chinese', 'mandarin',
            'japanese', 'korean', 'arabic', 'hindi', 'russian',
            # Business & Soft Skills
            'communication', 'leadership', 'teamwork', 'collaboration', 'problem solving',
            'project management', 'time management', 'critical thinking', 'analytical skills',
            'mentoring', 'training', 'presentation', 'negotiation', 'customer service',
            'client relations', 'stakeholder management', 'strategic planning', 'business development',
            'sales', 'marketing', 'consulting', 'data analysis', 'financial analysis',
            'budgeting', 'forecasting', 'risk management', 'change management',
            # Additional Tools
            'zoom', 'webex', 'microsoft teams', 'skype', 'google meet',
            'wordpress', 'shopify', 'squarespace', 'wix'
        ]
        
        # Initialize skill extractor and recommendation generator (after common_skills is set)
        self.skill_extractor = SkillExtractor(self.common_skills)
        self.recommendation_generator = RecommendationGenerator()
    
    def extract_skills(self, text):
        """Extract skills from text using rule-based dictionary matching."""
        if not text:
            return []

        # Primary: structured dictionary-based extraction
        found_skills = extract_skills_from_dict(text)

        # Secondary: match against the legacy common_skills list for coverage
        text_lower = text.lower()
        normalized_text = re.sub(r'[^\w\s]', ' ', text_lower)
        sorted_skills = sorted(self.common_skills, key=len, reverse=True)

        for skill in sorted_skills:
            if len(skill) < 2:
                continue
            if ' ' in skill:
                if skill in normalized_text:
                    found_skills.append(skill.title())
            else:
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, normalized_text):
                    found_skills.append(skill.title())

        # Extract skills from experience descriptions
        experience_skills = self.skill_extractor.extract_skills_from_experience(text)
        found_skills.extend(experience_skills)

        # Normalise common abbreviations before deduplication
        _ALIASES = {
            'js': 'javascript',
            'ts': 'typescript',
            'py': 'python',
            'ml': 'machine learning',
            'dl': 'deep learning',
            'oop': 'object-oriented programming',
            'rest': 'rest api',
            'k8s': 'kubernetes',
            'tf': 'tensorflow',
        }
        normalised = []
        for skill in found_skills:
            mapped = _ALIASES.get(skill.lower(), skill.lower())
            normalised.append(mapped.title())
        found_skills = normalised

        # Also detect aliases directly in raw text (e.g. "JS, PHP" in project bullets)
        for alias, full in _ALIASES.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower) and full.title() not in [s.lower() for s in found_skills]:
                found_skills.append(full.title())

        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in found_skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill.title())

        return unique_skills
    
    def extract_keywords_from_job_description(self, job_description):
        """Extract clean skill names from job description using rule-based matching.

        When the job description is too vague and yields fewer than 3 skills,
        the system infers expected skills from role keywords (e.g. "software
        engineer" → Python, JavaScript, Git, SQL …).  This ensures meaningful
        matching even for short / generic prompts.
        """
        job_skills = self.extract_skills(job_description)

        # Filter out generic/noisy words
        seen = set()
        unique_skills = []
        skip_patterns = [
            'experience', 'required', 'preferred', 'years', 'knowledge of',
            'proficiency in', 'familiarity with', 'must have', 'should have',
            'skills', 'skill', 'ability',
        ]

        for skill in job_skills:
            skill_lower = skill.lower().strip()
            if skill_lower in seen:
                continue
            if self.job_analyzer.is_generic_word(skill_lower):
                continue
            if any(pattern in skill_lower for pattern in skip_patterns):
                continue
            seen.add(skill_lower)
            unique_skills.append(skill)

        # Fallback: if the JD is too vague, infer skills from role keywords
        if len(unique_skills) < 3:
            inferred = infer_skills_from_role(job_description)
            if inferred:
                for skill in inferred:
                    skill_title = skill.title()
                    if skill_title.lower() not in seen:
                        seen.add(skill_title.lower())
                        unique_skills.append(skill_title)

        # ML fallback: if the keyword router still came up short, ask the
        # bi-encoder for the semantically closest role template. This catches
        # JDs that don't use any of the literal role keywords ("Build internal
        # dashboards for the marketing team" → data analyst by similarity).
        if len(unique_skills) < 3:
            try:
                from .ml_matcher import find_closest_role_profile as _closest
                ml_skills, ml_role, ml_conf = _closest(job_description)
                if ml_skills:
                    for skill in ml_skills:
                        skill_title = skill.title()
                        if skill_title.lower() not in seen:
                            seen.add(skill_title.lower())
                            unique_skills.append(skill_title)
            except Exception:
                pass

        # Last-resort safety net: if even after the keyword fallback AND the
        # ML fallback we still don't have at least three skills to score
        # against, the JD is too thin to evaluate. Falling through to the
        # matcher with an empty job_skills list produces a degenerate score
        # and self-contradictory weakness messages (matched=[] AND
        # missing=[] simultaneously). Better behaviour: hand it a tiny
        # placeholder set so the matcher still has *something* to compute
        # against, and the downstream weakness layer reports the JD's
        # brevity rather than the resume's quality.
        if len(unique_skills) < 3:
            generic_safety_set = [
                'Communication', 'Problem Solving', 'Teamwork',
            ]
            for skill in generic_safety_set:
                if skill.lower() not in seen:
                    seen.add(skill.lower())
                    unique_skills.append(skill)

        return unique_skills[:25]
    
    def calculate_match_score(self, resume_text, job_description):
        """Calculate match score using hybrid scoring (skill match + semantic + experience)."""
        resume_skills = self.extract_skills(resume_text)
        job_skills = self.extract_keywords_from_job_description(job_description)

        match_results = self.ml_matcher.calculate_hybrid_match_score(
            resume_text, job_description,
            resume_skills, job_skills,
        )
        return int(match_results['total_score'])

    # Skills that should never appear as "missing" in a software / AI / engineering role
    _DEV_ROLE_IRRELEVANT_SKILLS = {
        "compensation and benefits", "payroll", "employee relations", "recruiting",
        "talent acquisition", "hris", "onboarding", "succession planning",
        "real estate", "real estate law", "property management", "leasing",
        "tenant relations", "mls", "property valuation",
    }

    # ── Implicit skill implication graph ─────────────────────────────────
    # Maps regex patterns found in resume text → skills they demonstrate.
    # These are added to resume_skills for scoring so a candidate who USES
    # Flask doesn't get penalised for not writing "REST API" explicitly.
    _SKILL_IMPLICATIONS = [
        # Web frameworks → REST API + language
        (r'\bflask\b',                          ['rest api', 'python']),
        (r'\bdjango\b',                         ['rest api', 'python']),
        (r'\bfastapi\b',                        ['rest api', 'python']),
        (r'\bexpress\b',                        ['rest api', 'javascript', 'node.js']),
        (r'\blaravel\b',                        ['rest api', 'php']),
        (r'\bspring\s*boot\b',                  ['rest api', 'java']),
        (r'\bnode\.?js\b',                      ['javascript', 'node.js']),
        # Explicit API mentions
        (r'\brest(ful)?\s*(api|endpoint|service|call)\b', ['rest api']),
        (r'\bapi\s*(endpoint|call|request|response|integration)\b', ['rest api']),
        # Mobile
        (r'\breact\s*native\b',                 ['javascript', 'mobile development']),
        (r'\bflutter\b',                        ['dart', 'mobile development']),
        # ML / AI frameworks
        (r'\btensorflow\b',                     ['machine learning', 'deep learning', 'python']),
        (r'\bpytorch\b',                        ['machine learning', 'deep learning', 'python']),
        (r'\bkeras\b',                          ['machine learning', 'deep learning', 'python']),
        (r'\byolo(v\d+)?\b',                    ['computer vision', 'machine learning', 'python']),
        (r'\bopencv\b',                         ['computer vision', 'python']),
        (r'\bscikit.?learn\b',                  ['machine learning', 'python']),
        (r'\btrain(ed)?\s+(a\s+)?(model|classifier|network|neural)\b', ['machine learning']),
        (r'\bneural\s+net(work)?\b',            ['deep learning', 'machine learning']),
        (r'\b(image|object)\s+(detect|classif|recogni)\w+\b', ['computer vision', 'machine learning']),
        # Data
        (r'\bpandas\b',                         ['python', 'data analysis']),
        (r'\bnumpy\b',                          ['python', 'data analysis']),
        (r'\bmatplotlib\b',                     ['python', 'data analysis']),
        (r'\bsql\s+(query|queries|schema|table|join)\b', ['sql']),
        (r'\b(mysql|postgresql|sqlite|mongodb|oracle)\b', ['sql', 'database']),
        # DevOps / Cloud
        (r'\bdocker\b',                         ['docker', 'devops']),
        (r'\bkubernetes\b',                     ['kubernetes', 'docker', 'devops']),
        (r'\bci[/ ]?cd\b',                      ['ci/cd', 'devops']),
        (r'\bjenkins\b',                        ['ci/cd', 'devops']),
        (r'\bgithub\s+actions\b',               ['ci/cd', 'git']),
        (r'\b(aws|amazon\s+web\s+services|ec2|s3\b|lambda\b|rds\b)\b', ['aws', 'cloud computing']),
        (r'\bazure\b',                          ['azure', 'cloud computing']),
        (r'\bgcp\b|google\s+cloud',             ['gcp', 'cloud computing']),
        (r'\bterraform\b',                      ['infrastructure as code', 'devops']),
        # Git / Version control
        (r'\bgithub\.com\b',                    ['git', 'github']),
        (r'\bgit\s+(commit|push|pull|branch|merge|clone)\b', ['git']),
        # Unity / Game dev
        (r'\bunity\b',                          ['c#', 'game development']),
        # Testing
        (r'\bunit\s+test(ing)?\b',              ['testing']),
        (r'\bjunit\b',                          ['testing', 'java']),
        (r'\bpytest\b',                         ['testing', 'python']),
        (r'\bselenium\b',                       ['testing', 'automation']),
        # Soft / process skills demonstrated through work
        (r'\bstakeholder\b',                    ['stakeholder management', 'communication']),
        (r'\b(code|peer)\s+review\b',           ['code review']),
        (r'\bscrum\b',                          ['agile', 'scrum']),
        (r'\bsprint\s+(planning|review|retrospective)\b', ['agile', 'scrum']),
        (r'\b(product|project)\s+backlog\b',    ['agile']),
        (r'\bmicroservice\b',                   ['microservices']),
        (r'\bgraphql\b',                        ['graphql', 'rest api']),
        # Communication / teamwork demonstrated through work descriptions
        (r'\b(present(ed|ation)?|demo(nstrat)?|pitch(ed)?)\b',  ['communication', 'presentation']),
        (r'\b(led|lead|manag(ed)?|coordinat(ed)?|direct(ed)?)\b', ['leadership', 'teamwork']),
        (r'\bcross.functional\b',               ['teamwork', 'collaboration']),
        (r'\bcollaborat\w+\b',                  ['teamwork', 'collaboration']),
        (r'\bclient|customer\b',                ['communication', 'customer service']),
        # Problem solving demonstrated through achievements
        (r'\b(debug|troubleshoot|resolv|optimis|optim[iz])\w+\b', ['problem solving']),
        (r'\b(achiev|improv|reduc|increas)\w+\s+\w*\s*\d+%', ['problem solving']),
        (r'\b(design(ed)?|architect(ed)?|built|developed)\s+(a\s+)?(system|solution|pipeline|platform)\b',
         ['problem solving', 'system design']),
        # Research / analytical
        (r'\b(analys[ei]|evaluat|investigat|explor|research)\w+\b', ['research', 'analytical skills']),
        (r'\b(model|algorithm|statistical|heuristic)\b', ['research', 'analytical skills']),
        # Writing / documentation
        (r'\b(report|document(ation)?|proposal|specification|write-up|write up)\b', ['writing']),
        (r'\b(deck|slide|presentation)\b', ['writing', 'communication']),

        # ── Project Management ────────────────────────────────────────────
        (r'\bjira\b',                               ['agile', 'project management']),
        (r'\bconfluence\b',                         ['project management', 'documentation']),
        (r'\b(trello|asana|monday\.com|notion)\b',  ['project management']),
        (r'\bgantt\b',                              ['project management']),
        (r'\b(roadmap|product\s+backlog)\b',        ['project management', 'strategic planning']),
        (r'\b(deliverable|milestone|timeline)\b',   ['project management']),
        (r'\b(budget|cost)\s+(track|manag|overrun|forecast)\w*\b', ['budgeting', 'project management']),
        (r'\brisk\s+(assess|manag|mitig)\w+\b',     ['risk management']),
        (r'\bokr\b',                                ['strategic planning', 'project management']),
        (r'\bkpi\b',                                ['data analysis', 'strategic planning']),

        # ── Finance / Accounting ──────────────────────────────────────────
        (r'\bp[&/]l\b|profit\s+(and\s+)?loss',      ['financial analysis', 'financial modelling']),
        (r'\bbalance\s+sheet\b',                    ['financial analysis', 'accounting']),
        (r'\bincome\s+statement\b',                 ['financial analysis', 'accounting']),
        (r'\bfinancial\s+(model|report|plan|analy)\w+\b', ['financial analysis', 'financial modelling']),
        (r'\bfinancial\s+modell?ing\b',             ['financial modelling', 'valuation', 'financial analysis']),
        (r'\bdcf\b|discounted\s+cash\s+flow\b',     ['valuation', 'financial modelling', 'financial analysis']),
        (r'\b(lbo|leveraged\s+buy.?out)\b',         ['valuation', 'financial modelling']),
        (r'\bvaluat\w+\b',                          ['valuation', 'financial analysis']),
        (r'\bbloomberg\s+terminal\b',               ['bloomberg', 'financial analysis']),
        (r'\bvariance\s+analysis\b',                ['financial analysis', 'analytical skills']),
        (r'\bforecast\w+\b',                        ['forecasting', 'financial analysis']),
        (r'\bbudget\w+\b',                          ['budgeting', 'financial analysis']),
        (r'\bpivot\s+table\b',                      ['excel', 'data analysis']),
        (r'\bvlookup\b|v\s*lookup\b',               ['excel', 'data analysis']),
        (r'\bquickbooks\b',                         ['accounting', 'quickbooks']),
        (r'\bxero\b',                               ['accounting', 'xero']),
        (r'\b(month.end|year.end)\s+(close|report|process)\w*\b', ['accounting', 'financial analysis']),
        (r'\baccounts\s+(payable|receivable)\b',    ['accounting']),
        (r'\breconciliat\w+\b',                     ['accounting', 'financial analysis']),
        (r'\baudit\b',                              ['accounting', 'compliance']),
        (r'\btax\s+(return|filing|compliance|prep)\w*\b', ['accounting', 'tax']),

        # ── Creative / Design ─────────────────────────────────────────────
        (r'\b(adobe\s+)?(photoshop|illustrator|indesign)\b',
         ['graphic design', 'adobe photoshop']),
        (r'\b(graphic\s+design|visual\s+design|brand\s+design)\b',
         ['graphic design', 'branding']),
        (r'\b(ba|bfa|bsc|bachelor|degree)\s+(in\s+)?(graphic|visual\s+comm|design)\w*\b',
         ['graphic design']),
        (r'\b(colour\s+grading|color\s+grading|video\s+edit)\w*\b',
         ['video editing', 'adobe premiere']),
        (r'\b(motion\s+design|motion\s+graphic)\w*\b',
         ['motion design', 'adobe after effects']),
        (r'\b(storyboard)\w*\b',                    ['storyboarding', 'creativity']),
        (r'\b(ui|ux|user\s+experience)\s+(design|designer)\b',
         ['ui/ux design', 'figma', 'wireframing']),

        # ── Marketing & Digital ───────────────────────────────────────────
        (r'\bgoogle\s+analytics\b',                 ['digital marketing', 'data analysis']),
        (r'\bga4\b',                                ['digital marketing', 'data analysis']),
        (r'\bseo\b|search\s+engine\s+optim\w+',    ['seo', 'digital marketing']),
        (r'\bsem\b|search\s+engine\s+market\w+',   ['sem', 'digital marketing']),
        (r'\bgoogle\s+ads\b',                       ['ppc', 'digital marketing']),
        (r'\b(facebook\s+ads|meta\s+ads)\b',        ['ppc', 'digital marketing', 'social media']),
        (r'\bhubspot\b',                            ['crm', 'email marketing', 'hubspot']),
        (r'\bmailchimp\b',                          ['email marketing', 'marketing automation']),
        (r'\b(email\s+marketing|email\s+campaign)\b', ['email marketing', 'digital marketing']),
        (r'\bcontent\s+(calendar|strateg|creat|market)\w*\b', ['content marketing', 'digital marketing']),
        (r'\b(marketing\s+campaign|campaign\s+manag)\w*\b', ['marketing', 'digital marketing']),
        (r'\ba/?b\s*test\w*\b',                     ['analytical skills', 'digital marketing']),
        (r'\bconversion\s+rate\b',                  ['digital marketing', 'analytical skills']),
        (r'\bsocial\s+media\b',                     ['social media', 'social media management']),
        (r'\bsocial\s+media\s+(manag|strateg|post|content|schedul)\w+\b', ['social media', 'social media management', 'content marketing']),
        (r'\b(copywriting|copy\s+writing)\b',       ['copywriting', 'content marketing']),
        (r'\bbrand\s+(awareness|strateg|identit)\w*\b', ['branding', 'marketing']),

        # ── HR / People ───────────────────────────────────────────────────
        (r'\b(recruit|hiring|talent\s+acqui)\w+\b', ['recruiting', 'talent acquisition']),
        (r'\bonboard\w+\b',                         ['onboarding', 'talent acquisition']),
        (r'\bperformance\s+(review|appraisal|management)\b', ['employee relations', 'performance management']),
        (r'\btraining\s+(and\s+)?(development|program|session)\b', ['training', 'learning and development']),
        (r'\b(employee\s+engagement|engagement\s+survey)\b', ['employee relations']),
        (r'\bjob\s+(description|posting|advert)\b', ['recruiting']),
        (r'\binterview(ed|ing|s)?\b',               ['recruiting', 'talent acquisition']),
        (r'\bhris\b',                               ['hris']),
        (r'\bworkday\b',                            ['hris', 'workday']),
        (r'\blearning\s+(and\s+)?development\b',    ['learning and development', 'training']),
        (r'\bpayroll\b',                            ['payroll', 'hris']),
        (r'\b(offboard|exit\s+interview)\b',        ['employee relations']),

        # ── Sales ─────────────────────────────────────────────────────────
        (r'\bsalesforce\b',                         ['salesforce', 'crm', 'sales']),
        (r'\bzoho\s+crm\b',                         ['crm', 'sales']),
        (r'\b(sales\s+pipeline|pipeline\s+manag)\w*\b', ['sales', 'crm']),
        (r'\b(quota|sales\s+target)\b',             ['sales']),
        (r'\bcold\s+(call\w*|email\w*|outreach\w*)\b', ['sales', 'communication']),
        (r'\b(prospect|lead\s+generat)\w+\b',       ['sales', 'business development']),
        (r'\b(upsell|cross.sell)\b',                ['sales', 'customer service']),
        (r'\b(close|closed)\s+(a\s+)?(deal|sale|contract)\b', ['sales', 'negotiation']),
        (r'\baccount\s+manag\w+\b',                 ['account management', 'sales']),
        (r'\bcrm\b',                                ['crm', 'customer service']),

        # ── Customer Service ──────────────────────────────────────────────
        (r'\b(resolv|handl)\w+\s+(customer|client|complaint|issue|query|enquiry)\b',
         ['customer service', 'problem solving']),
        (r'\bzendesk\b',                            ['customer service', 'zendesk']),
        (r'\bfreshdesk\b',                          ['customer service', 'freshdesk']),
        (r'\bservice\s+desk\b',                     ['customer service']),
        (r'\bcustomer\s+satisfaction\b',            ['customer service']),
        (r'\bnps\b',                                ['customer service', 'data analysis']),

        # ── Legal / Compliance ────────────────────────────────────────────
        (r'\bcontract\s+(review|draft|negotiat)\w*\b', ['negotiation', 'legal']),
        (r'\bcompliance\b',                         ['compliance', 'risk management']),
        (r'\bdue\s+diligence\b',                    ['research', 'analytical skills']),
        (r'\bregulat\w+\s+(complian|framew|require)\w+\b', ['compliance', 'risk management']),
    ]

    # ── Skills considered "advanced / nice-to-have" for JUNIOR roles ─────
    # Missing these should penalise a junior candidate less than missing core skills.
    _JUNIOR_ADVANCED_SKILLS = {
        # Cloud & infrastructure — learned on the job
        'aws', 'azure', 'gcp', 'cloud computing', 'docker', 'kubernetes',
        'terraform', 'ci/cd', 'jenkins', 'github actions',
        'infrastructure as code', 'ansible', 'chef', 'puppet',
        # Advanced architecture
        'microservices', 'system design', 'distributed systems',
        'cloud architecture', 'serverless',
        # Advanced data / messaging
        'elasticsearch', 'kafka', 'redis', 'rabbitmq', 'cassandra',
        # Advanced API patterns
        'graphql', 'grpc', 'websocket',
        # Code quality tools
        'code review', 'testing',
        # ── Business / Finance — too senior for graduates ─────────────────
        'strategic planning', 'business strategy', 'financial modelling',
        'investment analysis', 'portfolio management', 'mergers and acquisitions',
        'due diligence', 'board reporting', 'executive presentations',
        'corporate finance', 'private equity', 'derivatives',
        # ── HR — too senior for entry-level ──────────────────────────────
        'succession planning', 'organizational design', 'change management',
        'hr strategy', 'talent management', 'compensation and benefits',
        # ── Marketing — too senior for graduates ─────────────────────────
        'brand strategy', 'marketing strategy', 'p&l management', 'media buying',
        'programmatic advertising', 'attribution modelling',
        # ── Sales — too senior for entry-level ───────────────────────────
        'enterprise sales', 'channel management', 'strategic partnerships',
        'revenue operations', 'sales strategy',
        # ── PM — too senior ───────────────────────────────────────────────
        'program management', 'enterprise architecture',
        'organizational change management',
    }

    # ── Core skills for common junior roles ──────────────────────────────
    _JUNIOR_CORE_SKILLS = {
        'python', 'javascript', 'java', 'sql', 'git', 'react',
        'html', 'css', 'rest api', 'agile', 'problem solving',
        'communication', 'teamwork', 'testing', 'node.js',
    }

    def _infer_implicit_skills(self, resume_text: str) -> list:
        """
        Scan resume text for evidence of skills not explicitly listed.

        Uses the _SKILL_IMPLICATIONS graph: each entry is a (pattern, [skills])
        pair.  When the pattern matches, the implied skills are added to the
        returned list so they count toward the match score.

        Returns a deduplicated list of inferred skill strings (title-cased).
        """
        text_lower = resume_text.lower()
        inferred: set = set()
        for pattern, skills in self._SKILL_IMPLICATIONS:
            if re.search(pattern, text_lower):
                for skill in skills:
                    inferred.add(skill)
        return [s.title() for s in sorted(inferred)]

    def _apply_role_calibration(
        self,
        raw_score: int,
        missing_skills: list,
        resume_lower: str,
        role_level: str,
        job_skills: list,
        matched_skills: list,
        degree_relevant: bool = False,
        degree_mismatch: bool = False,
    ) -> int:
        """
        Adjust the raw match score based on role seniority level and
        candidate profile signals.

        Intern roles:
        - The most lenient profile. Interns are expected to be LEARNING.
        - Advanced AND expected-tier skills are discounted (the rule
          baseline only counts core skills).
        - +8 boost for any degree (vs +5 at junior) — being a student
          IS the qualification for an internship.
        - +4 extra if the degree is domain-relevant.
        - +3 boost for extracurricular leadership signals (student
          council, club committee, hackathon, project lead).
        - Total cap: +25 pts over raw score.

        Junior roles:
        - Advanced/infrastructure skills (Kubernetes, Terraform, …) count
          less — they're learned on the job, not expected at entry level.
        - Having any degree gives a +5 boost (strong signal for junior
          hiring).
        - Having a *domain-relevant* degree adds a further +3 on top.
        - Having internship/placement experience gives a +4 boost.
        - Total cap: +18 pts over raw score.

        Senior roles:
        - Penalty is unchanged for missing core technical skills.
        - No degree/internship bonus (experience matters more).

        Mid roles:
        - Slight bonus (+3) for degree + internship combo, plus +2 if
          the degree is domain-relevant.
        """
        if role_level == 'intern':
            bonus = 0.0

            # Discount BOTH advanced AND expected-tier skills from the
            # missing-list when computing the effective skill score. An
            # intern who knows the core fundamentals (e.g. a programming
            # language and version control for a CS internship) should
            # not be penalised for not yet knowing Docker / Kubernetes /
            # AWS — those are explicitly things internships TEACH.
            _profile = get_role_profile(' '.join(missing_skills + matched_skills))
            _profile_advanced = (
                {s.lower() for s in _profile.get('advanced', [])}
                if _profile else set()
            )
            _profile_expected = (
                {s.lower() for s in _profile.get('expected', [])}
                if _profile else set()
            )
            _discounted = (
                _profile_advanced
                | _profile_expected
                | self._JUNIOR_ADVANCED_SKILLS
            )

            discounted_in_missing = [
                s for s in missing_skills if s.lower() in _discounted
            ]
            if discounted_in_missing and job_skills:
                effective_total = len(job_skills) - len(discounted_in_missing)
                if effective_total > 0:
                    effective_ratio = len(matched_skills) / effective_total
                    effective_skill_score = min(100, effective_ratio * 100)
                    original_skill_score = (
                        len(matched_skills) / len(job_skills)
                    ) * 100
                    skill_improvement = effective_skill_score - original_skill_score
                    # Skill match is 60% of total score
                    bonus += skill_improvement * 0.60

            # Degree signal — for an intern, the degree is THE
            # qualification. A domain-relevant degree on top is worth
            # nearly as much as a year of professional experience for a
            # junior hire.
            has_degree = bool(re.search(
                r'(bsc|b\.sc|bachelor|master|mba|phd|m\.sc|hons|honours|'
                r'first\s+class|second\s+class|university|college|in\s+progress)',
                resume_lower,
            ))
            if has_degree:
                bonus += 8.0
                if degree_relevant:
                    bonus += 4.0
                elif degree_mismatch:
                    # Wrong degree for the role: dilute the +8 generic-
                    # degree bonus rather than zero it out (any degree is
                    # still better than none for an intern), but cap the
                    # net contribution at +4 instead of +12.
                    bonus -= 4.0

            # Extracurricular leadership signal — student council, club
            # exec, hackathon, project lead, sports captain. For an
            # internship these are evidence of self-direction, which
            # employers value as much as professional experience for an
            # early-career hire.
            has_extracurricular_lead = bool(re.search(
                r'\b(student\s+council|club|society|committee|'
                r'hackathon|capstone|final[- ]year\s+project|'
                r'project\s+lead|team\s+lead|captain|president|'
                r'vice[- ]president|founder|co-?founder|prefect|ambassador|'
                r'volunteer|ngo)\b',
                resume_lower,
            ))
            if has_extracurricular_lead:
                bonus += 3.0

            calibrated = raw_score + int(round(min(bonus, 25.0)))
            return min(100, calibrated)

        if role_level == 'junior':
            bonus = 0.0

            # Use the role profile's advanced tier if available, else fall back
            # to the broad _JUNIOR_ADVANCED_SKILLS set
            _profile = get_role_profile(' '.join(missing_skills + matched_skills))
            _profile_advanced = (
                {s.lower() for s in _profile.get('advanced', [])}
                if _profile else set()
            )
            _advanced_set = _profile_advanced | self._JUNIOR_ADVANCED_SKILLS
            # Recalculate skill score excluding advanced skills from requirements
            advanced_in_missing = [
                s for s in missing_skills
                if s.lower() in _advanced_set
            ]
            if advanced_in_missing and job_skills:
                # Effective job skills = job_skills minus advanced ones
                effective_total = len(job_skills) - len(advanced_in_missing)
                if effective_total > 0:
                    effective_ratio = len(matched_skills) / effective_total
                    effective_skill_score = min(100, effective_ratio * 100)
                    # Use whichever gives a higher skill component
                    original_skill_score = (len(matched_skills) / len(job_skills)) * 100
                    skill_improvement = effective_skill_score - original_skill_score
                    # Skill is 60% of total score
                    bonus += skill_improvement * 0.60

            # Degree signal
            has_degree = bool(re.search(
                r'(bsc|b\.sc|bachelor|master|mba|phd|m\.sc|hons|honours|'
                r'first\s+class|second\s+class|university|college)',
                resume_lower
            ))
            if has_degree:
                bonus += 5.0
                # Extra credit for a domain-relevant degree — a CS degree
                # applied to a CS role is the strongest signal an
                # early-career candidate can carry.
                if degree_relevant:
                    bonus += 3.0
                elif degree_mismatch:
                    # Wrong domain: dilute the generic +5 to +2 net.
                    bonus -= 3.0

            # Internship / placement signal
            has_internship = bool(re.search(
                r'\b(intern|placement|co.op|apprentice|trainee)\b',
                resume_lower
            ))
            if has_internship:
                bonus += 4.0

            calibrated = raw_score + int(round(min(bonus, 18.0)))
            return min(100, calibrated)

        elif role_level == 'mid':
            # Small bonus for degree + internship combo
            has_degree = bool(re.search(r'(bachelor|master|mba|phd|bsc|hons)', resume_lower))
            has_internship = bool(re.search(r'\b(intern|placement)\b', resume_lower))
            bonus = 0
            if has_degree and has_internship:
                bonus += 3
            if degree_relevant:
                bonus += 2
            elif degree_mismatch:
                # Wrong-domain degree at mid level: small penalty so a
                # business graduate applying for a software engineer role
                # doesn't get the same +3 combo bonus as a CS graduate.
                bonus -= 2
            if bonus:
                return min(100, raw_score + bonus)

        # Senior: no calibration — experience evidence carries it
        return raw_score

    def generate_full_analysis(self, resume_text, job_description):
        """Generate comprehensive analysis with structured AI insight."""
        # 1. Extract explicitly listed skills
        resume_skills = self.extract_skills(resume_text)

        # 2. Infer implicitly demonstrated skills via the implication graph
        inferred_skills = self._infer_implicit_skills(resume_text)
        inferred_lower = {s.lower() for s in inferred_skills}
        explicit_lower = {s.lower() for s in resume_skills}
        # Add inferred skills that aren't already in the explicit list
        new_inferred = [s for s in inferred_skills if s.lower() not in explicit_lower]
        effective_resume_skills = resume_skills + new_inferred

        # 3. ML safety pass over the resume — bi-encoder scans the prose for
        # skills the keyword matcher and the implication graph both missed.
        # Conservative threshold (0.32) and capped at 8 recoveries per resume
        # so the rule layer remains the primary signal. Any failure of the
        # ML pass returns an empty list, leaving rule-based recall unchanged.
        try:
            from .ml_matcher import recover_skills_from_resume as _ml_recover_resume
            ml_resume_recovered = _ml_recover_resume(
                resume_text, effective_resume_skills,
            )
            if ml_resume_recovered:
                _existing = {s.lower() for s in effective_resume_skills}
                effective_resume_skills = effective_resume_skills + [
                    s for s in ml_resume_recovered
                    if s.lower() not in _existing
                ]
        except Exception:
            ml_resume_recovered = []

        # ── JD required / preferred split ────────────────────────────────────
        # parse_jd_tiers splits the JD into required, preferred, and unclassified
        # buckets.  Required + unclassified = the normal job_skills list used for
        # scoring.  Preferred skills give a small bonus when matched but carry no
        # penalty when missing — they are surfaced separately in weaknesses.
        jd_tier_result = parse_jd_tiers(job_description)
        _jd_preferred_raw = jd_tier_result['preferred']

        # Build job_skills: use existing pipeline (filters generic words, adds
        # role-inferred fallbacks) — this covers required + unclassified together.
        job_skills = self.extract_keywords_from_job_description(job_description)

        # Preferred skills: filter generics, then REMOVE them from job_skills so
        # they don't get penalised in the main scoring formula.
        _GENERIC_JD = {
            'experience', 'knowledge', 'skills', 'ability', 'understanding',
            'familiarity', 'proficiency', 'background', 'expertise',
        }
        preferred_job_skills = [
            s for s in _jd_preferred_raw
            if s.lower() not in _GENERIC_JD
            and not self.job_analyzer.is_generic_word(s.lower())
        ]

        # Strip preferred skills from the main job_skills list so they are never
        # counted as "missing required" skills in the score or weakness messages.
        if preferred_job_skills:
            _pref_lower = {s.lower() for s in preferred_job_skills}
            job_skills = [s for s in job_skills if s.lower() not in _pref_lower]

        # ── Raw JD token extraction — catches "invisible" skills ─────────────
        # Picks up acronyms (AWS, GDPR), CamelCase (ReactJS), special-char
        # tokens (C++, .NET), and title-case tool names in tech contexts
        # (Figma, Airtable, Retool) — skills not in SKILL_DICTIONARY.
        # Tokens are routed to required vs preferred based on which bucket of
        # the parsed JD they came from, then checked against the resume text.
        _known_for_raw = set(s.lower() for s in job_skills) | \
                         set(s.lower() for s in preferred_job_skills)
        _pref_text  = jd_tier_result.get('preferred_text', '') or ''
        _raw_from_pref = set(
            t.lower() for t in extract_raw_jd_tokens(_pref_text, known_skills=None)
        )
        _raw_all = extract_raw_jd_tokens(job_description, known_skills=None)

        _NOISE_RAW: set[str] = {
            # Noise specific to this integration path (things that look skill-like
            # but are always fluff in a JD context)
            'saas', 'paas', 'iaas', 'b2b', 'b2c', 'sme', 'smb', 'mvp',
            'kpi', 'kpis', 'okr', 'okrs', 'roi', 'usp',
            'full-time', 'part-time', 'fte', 'eoe', 'phd', 'mba', 'bsc', 'msc',
            'us', 'uk', 'eu', 'uae', 'usa', 'emea', 'apac', 'latam',
        }

        _raw_required_added: list[str] = []
        _raw_preferred_added: list[str] = []

        for tok in _raw_all:
            k = tok.lower()
            if k in _known_for_raw:
                continue
            if k in _NOISE_RAW:
                continue
            # Skip if this is the same base as a known skill with different
            # formatting (e.g. raw "NET" when dictionary has "asp.net").
            if any(k == s.lower() or k in s.lower().split() for s in job_skills):
                continue
            if k in _raw_from_pref:
                _raw_preferred_added.append(tok)
            else:
                _raw_required_added.append(tok)

        # Cap to avoid run-away additions from noisy JDs
        _raw_required_added  = _raw_required_added[:10]
        _raw_preferred_added = _raw_preferred_added[:10]

        # Check each raw token against the resume text with a word-boundary
        # regex. Present-in-resume tokens get promoted to effective_resume_skills
        # so they match; absent tokens flow through as missing.
        if _raw_required_added or _raw_preferred_added:
            _resume_lower = resume_text or ''
            for tok in _raw_required_added:
                job_skills.append(tok)
                if re.search(r'\b' + re.escape(tok) + r'\b', _resume_lower, re.IGNORECASE):
                    if tok.lower() not in {s.lower() for s in effective_resume_skills}:
                        effective_resume_skills.append(tok)
            for tok in _raw_preferred_added:
                preferred_job_skills.append(tok)
                if re.search(r'\b' + re.escape(tok) + r'\b', _resume_lower, re.IGNORECASE):
                    if tok.lower() not in {s.lower() for s in effective_resume_skills}:
                        effective_resume_skills.append(tok)

        # Analyse job for role context
        job_analysis = self.job_analyzer.analyze_job(job_description)
        role_type = job_analysis.get('role_type')
        industry = job_analysis.get('industry')

        # ── Centralised role detection (used throughout this method) ──────
        role_text = (job_description + ' ' + (role_type or '')).lower()
        is_ai_role = any(kw in role_text for kw in [
            'artificial intelligence', 'machine learning', 'ai ', 'deep learning',
            'data scien', 'computer vision', 'nlp',
        ])
        is_dev_role = any(kw in role_text for kw in [
            'software', 'developer', 'engineer', 'full stack', 'backend',
            'frontend', 'web develop', 'devops', 'programmer',
        ])
        is_pm_role = any(kw in role_text for kw in [
            'product manag', 'project manag', 'program manag', 'scrum master',
            'business analyst', 'operations manag', 'pmo',
        ])
        is_marketing_role = any(kw in role_text for kw in [
            'marketing', 'digital marketing', 'seo ', 'content strateg',
            'social media', 'brand manag', 'campaign manag', 'copywriter',
            'growth market', 'advertising',
        ])
        is_hr_role = any(kw in role_text for kw in [
            'human resource', ' hr ', 'people ops', 'talent acqui', 'recruiter',
            'recruiting', 'people partner', 'hrbp', 'learning and development',
            'l&d ', 'compensation', 'hris', 'people manag',
        ])
        is_finance_role = any(kw in role_text for kw in [
            'financ', 'accounting', 'accountant', 'auditor', 'treasury',
            ' tax ', 'bookkeeper', ' cfo', 'controller', 'financial analyst',
        ])
        is_sales_role = any(kw in role_text for kw in [
            ' sales', 'account executive', 'business development', 'account manager',
            'sales development', ' sdr', ' bdr', 'revenue', 'commercial',
        ])
        is_customer_service_role = any(kw in role_text for kw in [
            'customer service', 'customer support', 'customer success',
            'client support', 'helpdesk', 'service desk', 'support agent',
        ])
        is_business_role = (is_pm_role or is_marketing_role or is_hr_role or
                            is_finance_role or is_sales_role or
                            any(kw in role_text for kw in [
                                'consult', 'analyst', 'strategist', 'coordinator',
                                'director', 'executive', 'administrat',
                            ]))

        # Hybrid scoring using effective (explicit + inferred) resume skills
        match_results = self.ml_matcher.calculate_hybrid_match_score(
            resume_text, job_description,
            effective_resume_skills, job_skills,
            preferred_job_skills=preferred_job_skills or None,
        )

        raw_score = int(match_results['total_score'])
        found_skills = match_results['matched_skills']
        # Include partial (synonym) matches in found skills for display
        partial_skills = match_results.get('partial_skills', [])
        found_skills = found_skills + partial_skills
        missing_skills = match_results['missing_skills']

        # ── Filter role-inappropriate skills from missing list ────────────
        jd_lower = job_description.lower()
        resume_lower = resume_text.lower()
        _is_dev_or_ai = any(kw in jd_lower for kw in [
            'software', 'developer', 'engineer', 'programmer',
            'full stack', 'backend', 'frontend', 'devops',
            'artificial intelligence', 'machine learning', 'data scien',
        ])
        if _is_dev_or_ai:
            missing_skills = [
                s for s in missing_skills
                if s.lower() not in self._DEV_ROLE_IRRELEVANT_SKILLS
            ]
            match_results['missing_skills'] = missing_skills

        # ── Filter standalone generic words from missing/found lists ──────
        # e.g. "Analysis", "Management", "Development" by themselves add no value
        _GENERIC_STANDALONE = {
            'analysis', 'management', 'development', 'experience', 'knowledge',
            'skills', 'ability', 'design', 'strategy', 'support', 'services',
            'operations', 'systems', 'solutions', 'process', 'planning',
            'deployment', 'implementation', 'execution', 'delivery', 'coordination',
            # Too generic as standalone — meaningful only in compound phrases
            'marketing', 'advertising', 'consulting', 'engineering',
        }
        missing_skills = [s for s in missing_skills if s.lower() not in _GENERIC_STANDALONE]
        found_skills   = [s for s in found_skills   if s.lower() not in _GENERIC_STANDALONE]
        match_results['missing_skills'] = missing_skills

        # ── Domain-relevant degree detection ──────────────────────────────
        # Check whether the candidate's degree subject aligns with the role's
        # domain. This is a stronger signal for early-career candidates than
        # just having "a degree", and feeds both the calibrator (a small
        # score bump) and the strengths section (a more specific message).
        # The same map is used downstream to pick which strength to surface.
        _DEGREE_DOMAIN_MAP = {
            'computer science': r'(computer\s+sci|computer\s+eng|software\s+eng|'
                                r'\bcs\b|comp\s*sci|informatics|information\s+tech|'
                                r'computing|software\s+develop)',
            'data science':     r'(data\s+sci|computer\s+sci|statistics|'
                                r'mathematics|machine\s+learning|\bcs\b)',
            'machine learning': r'(computer\s+sci|machine\s+learning|\bai\b|'
                                r'mathematics|statistics|data\s+sci)',
            'engineering':      r'(engineer|computer\s+sci|mathematics|physics)',
            'finance':          r'(finance|accounting|economics|business|mba)',
            'marketing':        r'(marketing|business|communication|media)',
            'design':           r'(design|fine\s+art|architecture|graphic)',
            'medical':          r'(medic|nurs|pharma|biolog|biomed)',
            'legal':            r'(\blaw\b|llb|\bjd\b|legal)',
        }
        _has_degree_resume = bool(re.search(
            r'(bsc|b\.sc|b\.s\b|bachelor|master|mba|m\.sc|m\.s\b|phd|hons)',
            resume_lower,
        ))
        _degree_relevant = False
        _degree_domain   = None     # JD's expected domain (set when role family is known)
        _degree_mismatch = False    # candidate has a degree but it's in the wrong domain
        _degree_subject  = None     # extracted subject phrase from the resume

        # Identify the JD's expected domain (the first domain key whose
        # role-family keyword appears in the JD). This is used both to bless
        # a matching degree and to call out a mismatched one.
        _expected_domain = None
        for domain_kw in _DEGREE_DOMAIN_MAP:
            if domain_kw in role_text:
                _expected_domain = domain_kw
                break
        if _expected_domain is None and (is_dev_role or is_ai_role):
            _expected_domain = 'computer science'
        elif _expected_domain is None and is_finance_role:
            _expected_domain = 'finance'
        elif _expected_domain is None and is_marketing_role:
            _expected_domain = 'marketing'

        if _has_degree_resume:
            # Pass 1: positive — does the resume's degree match an expected
            # domain that the JD makes clear?
            for domain_kw, subject_pat in _DEGREE_DOMAIN_MAP.items():
                if domain_kw in role_text and re.search(subject_pat, resume_lower):
                    _degree_relevant = True
                    _degree_domain = domain_kw
                    break
            if not _degree_relevant and (is_dev_role or is_ai_role) and \
               re.search(_DEGREE_DOMAIN_MAP['computer science'], resume_lower):
                _degree_relevant = True
                _degree_domain = 'computer science'

            # Pass 2: negative — the JD has a clear expected domain, the
            # candidate has a degree, but the degree's subject doesn't match.
            # This is the "wrong degree" signal that drives a weakness
            # message and a tempered score (see _apply_role_calibration).
            if not _degree_relevant and _expected_domain:
                _degree_mismatch = True
                # Try to lift the degree's subject out of the resume so the
                # weakness message can name it ("Business and Management
                # degree doesn't match the Computer Science requirement").
                _subject_match = re.search(
                    r'(?:bsc|b\.sc|b\.s|bachelor(?:\'s)?|master(?:\'s)?|m\.sc|m\.s|mba|phd|hons|honours)'
                    r'(?:\s+(?:of|in))?'
                    r'\s+([a-z][a-z\s,&\-]{2,60}?)'
                    r'(?:\s*[,.\n(]|$|\s+(?:from|university|college|school))',
                    resume_lower,
                    flags=re.IGNORECASE,
                )
                if _subject_match:
                    raw_subject = _subject_match.group(1).strip(' ,.-')
                    # Title-case for display, drop trailing connective words
                    _degree_subject = re.sub(
                        r'\s+(predicted|projected|expected|class|honours|hons)\b.*$',
                        '', raw_subject, flags=re.IGNORECASE,
                    ).strip().title()

        # ── Role-level score calibration ─────────────────────────────────
        role_level = match_results.get('role_level', 'mid')
        match_score = self._apply_role_calibration(
            raw_score=raw_score,
            missing_skills=missing_skills,
            resume_lower=resume_lower,
            role_level=role_level,
            job_skills=job_skills,
            matched_skills=found_skills,
            degree_relevant=_degree_relevant,
            degree_mismatch=_degree_mismatch,
        )

        # ── Evidence classification (section-based) ───────────────────────
        # Split the resume into labelled sections and classify each matched
        # skill by the strongest section it appears in.  Skills shown in
        # Experience / Projects count as demonstrated evidence; skills that
        # appear only in the Skills list are "claimed but unverified".
        resume_sections = parse_resume_sections(resume_text or '')
        evidence_map = classify_skill_evidence(
            resume_text or '', found_skills, sections=resume_sections,
        )
        evidence_summary = compute_evidence_summary(evidence_map)
        _ev_delta = evidence_score_delta(evidence_summary)
        if _ev_delta:
            match_score = int(max(0, min(100, match_score + _ev_delta)))

        # ── Cross-encoder semantic recovery ───────────────────────────────
        # For each missing JD skill, check whether the resume prose
        # semantically demonstrates it (paraphrases the keyword matcher
        # couldn't bridge).  Moves recovered skills from missing → found,
        # applies a small capped bonus, and surfaces them as a strength.
        # The cross-encoder load + scoring happens behind a fail-soft
        # boundary inside rerank_missing_skills — any error → empty set.
        _semantic_recovered: list[str] = []
        try:
            from .ml_matcher import rerank_missing_skills as _rerank
            # Pass explicit resume skills so the kindred-skill guard fires:
            # a technical missing skill (Python, SQL, Git) is only paraphrase-
            # recovered when the resume shows at least one explicit member
            # of the same family. Without this guard, the bi-encoder
            # hallucinates technical matches into non-technical CVs.
            _recovered_scores = _rerank(
                missing_skills,
                resume_text or '',
                explicit_skills=resume_skills,
            )
            if _recovered_scores:
                _recovered_lower = {s.lower() for s in _recovered_scores}
                # Move recovered skills: missing → found.
                _kept_missing = [
                    s for s in missing_skills if s.lower() not in _recovered_lower
                ]
                _promoted = [
                    s for s in missing_skills if s.lower() in _recovered_lower
                ]
                if _promoted:
                    missing_skills = _kept_missing
                    found_skills = list(dict.fromkeys(found_skills + _promoted))
                    _semantic_recovered = _promoted
                    # Capped bonus: +1pp per recovery, max +3pp.  Same
                    # pattern as the trending-skill bonus so no single
                    # neural component can swamp the rule-based prior.
                    _sem_delta = min(3, len(_promoted))
                    match_score = int(max(0, min(100, match_score + _sem_delta)))
        except Exception:
            _semantic_recovered = []

        # ── Learned calibrator correction ────────────────────────────────
        # The calibrator is a small regressor trained on synthetic bootstrap
        # pairs + real user feedback.  It predicts a correction delta in
        # percentage points (capped at ±5pp inside the calibrator itself)
        # so a bad model can never swamp the rule-based score.  Returns 0
        # when no trained model is available — fully fail-soft.
        try:
            from .calibration_features import build_features as _build_feat
            from .score_calibrator import predict_correction as _predict_correction
            _cal_ctx = {
                'match_results':        match_results,
                'evidence_summary':     evidence_summary,
                'raw_score':            raw_score,
                'n_semantic_recovered': len(_semantic_recovered),
            }
            _scoring_features = _build_feat(_cal_ctx)
            _cal_delta = _predict_correction(_cal_ctx)
            if _cal_delta:
                match_score = int(max(0, min(100, match_score + _cal_delta)))
        except Exception:
            _scoring_features = None
            _cal_delta = 0.0

        # ── Tier data from profile (empty lists when no profile detected) ──
        core_missing     = match_results.get('core_missing', [])
        expected_missing = match_results.get('expected_missing', [])
        advanced_missing = match_results.get('advanced_missing', [])
        has_profile      = match_results.get('has_role_profile', False)

        # ── Preferred-skills gap (no-penalty nice-to-have) ────────────────
        preferred_missing = [
            s for s in match_results.get('preferred_missing', [])
            if s.lower() not in _GENERIC_STANDALONE
        ]

        # ── Helper sets for richer analysis ──────────────────────────────
        # Use effective skills (explicit + inferred) so strength detection
        # reflects what the candidate actually demonstrates
        resume_skill_set = set(s.lower() for s in effective_resume_skills)
        found_lower = set(s.lower() for s in found_skills)
        missing_lower_set = set(s.lower() for s in missing_skills)

        # Categorise resume skills for richer feedback
        _tech_skills = {"python", "javascript", "java", "typescript", "c++",
                        "c#", "php", "ruby", "go", "rust", "swift", "kotlin",
                        "html", "css", "sql", "react", "angular", "vue",
                        "node.js", "django", "flask", "docker", "git",
                        "aws", "azure", "linux", "rest api", "graphql"}
        _soft_skills = {"communication", "leadership", "teamwork",
                        "collaboration", "problem solving", "critical thinking",
                        "time management", "presentation", "negotiation",
                        "mentoring", "training", "adaptability", "creativity",
                        "attention to detail", "multitasking",
                        "organizational skills", "interpersonal skills"}
        _tool_skills = {"excel", "word", "powerpoint", "microsoft office",
                        "teams", "jira", "confluence", "slack", "tableau",
                        "power bi", "salesforce", "figma", "canva"}
        _lang_skills = {"french", "spanish", "german", "italian", "portuguese",
                        "chinese", "mandarin", "japanese", "korean", "arabic",
                        "hindi", "russian"}

        resume_tech = resume_skill_set & _tech_skills
        resume_soft = resume_skill_set & _soft_skills
        resume_tools = resume_skill_set & _tool_skills
        resume_langs = resume_skill_set & _lang_skills

        missing_tech = missing_lower_set & _tech_skills
        missing_soft = missing_lower_set & _soft_skills

        # ── Trending-skill bonus (active use of emerging-skills tracker) ──
        # A token that shows up in many recent JDs and also appears in both
        # THIS job's raw tokens AND this candidate's resume is a real in-demand
        # skill the curated dictionary hasn't caught up to yet (Bun, Cursor,
        # LangChain, pgvector, Zod, …).  Give a small capped bonus (+1pp per
        # match, +3pp max) and surface it as a strength so the candidate sees
        # why they were rewarded.  Fail-soft: any error → zero bonus.
        _trending_hits: list[str] = []
        try:
            from .emerging_skills import get_trending_token_set
            _trending = get_trending_token_set(min_mentions=3, within_days=30)
            if _trending:
                # Trending tokens are themselves well-formed skill names
                # (they made it into the tracker by being raw-token extracted
                # at least once).  Match them against JD and resume TEXT with
                # word boundaries — the raw-token extractor is too strict
                # (case-sensitive) to use here directly.
                _jd_lc     = (job_description or '').lower()
                _resume_lc = (resume_text or '').lower()
                for tok in _trending:
                    if len(tok) < 3:
                        continue
                    _pat = r'(?<![a-z0-9])' + re.escape(tok) + r'(?![a-z0-9])'
                    if re.search(_pat, _jd_lc) and (
                        tok in resume_skill_set
                        or tok in found_lower
                        or re.search(_pat, _resume_lc)
                    ):
                        _trending_hits.append(tok)
                if _trending_hits:
                    _trending_delta = min(3, len(_trending_hits))
                    match_score = int(max(0, min(100, match_score + _trending_delta)))
        except Exception:
            _trending_hits = []

        # ── Strengths ─────────────────────────────────────────────────────
        strengths = []
        if match_score >= 75:
            strengths.append("Excellent alignment with job requirements")
        elif match_score >= 60:
            strengths.append("Strong alignment with job requirements")

        if len(found_skills) >= 5:
            strengths.append(f"Strong skill set with {len(found_skills)} matching skills")
        elif len(found_skills) >= 3:
            strengths.append("Good foundational skills for this role")
        elif len(found_skills) >= 1:
            top_found = ', '.join(found_skills[:3])
            strengths.append(f"Transferable skills identified: {top_found}")

        if resume_tech:
            strengths.append(
                f"Technical proficiency demonstrated ({', '.join(s.title() for s in sorted(resume_tech)[:4])})"
            )

        if resume_soft:
            names = ', '.join(s.title() for s in sorted(resume_soft)[:4])
            strengths.append(f"Strong soft skills: {names}")

        if resume_tools:
            names = ', '.join(s.title() for s in sorted(resume_tools)[:4])
            strengths.append(f"Proficient with key tools: {names}")

        if resume_langs:
            names = ', '.join(s.title() for s in sorted(resume_langs))
            strengths.append(f"Multilingual advantage: {names}")

        if re.search(r'\d+%|\d+\s*(years?|months?)|increased|improved|reduced|managed|led',
                     resume_lower):
            strengths.append("Quantifiable achievements and metrics included")

        # ── Degree-strength messaging ─────────────────────────────────────
        # _degree_relevant + _degree_domain were computed earlier (before
        # calibration). Use them here to emit a specific or generic strength.
        _has_degree_str = re.search(
            r'(bsc|bac|b\.sc|bachelor|master|mba|phd|m\.sc|hons|honours|'
            r'degree|diploma|certif)',
            resume_lower,
        )
        if _has_degree_str:
            if _degree_relevant and _degree_domain:
                strengths.insert(0,
                    f"Degree directly aligned with this role's "
                    f"{_degree_domain} domain"
                )
            elif not _degree_mismatch:
                # Suppress the generic "academic qualifications listed"
                # strength when we know the degree is in the wrong field
                # — the weakness section already calls this out, and
                # claiming it as a strength would contradict that.
                strengths.append("Relevant academic qualifications listed")

        if re.search(r'(volunteer|community|society|club|captain|prefect|ambassador)',
                     resume_lower):
            strengths.append("Extracurricular involvement and initiative shown")

        # ── Evidence-based strengths ─────────────────────────────────────
        # Reward resumes where matched skills are actually demonstrated in
        # Experience / Projects, not just listed in a skills block.  Inserted
        # near the top of strengths so it survives the 6-item cap.
        _well_evidenced = evidence_summary.get('well_evidenced', [])
        if len(_well_evidenced) >= 3:
            _top_we = ', '.join(s.title() for s in _well_evidenced[:4])
            strengths.insert(
                min(1, len(strengths)),
                f"Strong evidence of {len(_well_evidenced)} skills demonstrated in your experience: {_top_we}"
            )
        elif len(_well_evidenced) >= 1 and match_score >= 60:
            _top_we = ', '.join(s.title() for s in _well_evidenced[:3])
            strengths.insert(
                min(1, len(strengths)),
                f"Demonstrated hands-on use of: {_top_we}"
            )

        # ── Trending-skill strength ───────────────────────────────────────
        # Surface the trending hits we rewarded above.  Inserted near the top
        # so it survives the 6-item cap.  Only fires at ≥2 hits to avoid
        # noisy one-off messages on weak signal.
        if len(_trending_hits) >= 2:
            _top_trend = ', '.join(t.title() for t in sorted(_trending_hits)[:4])
            strengths.insert(
                min(2, len(strengths)),
                f"Demonstrates in-demand skills trending in recent postings: {_top_trend}"
            )

        # ── Semantic-recovery strength ───────────────────────────────────
        # When the cross-encoder bridges paraphrased JD skills to resume
        # prose, surface it so the user sees WHY they got credit for a
        # skill they didn't literally list.  Gated at ≥1 hit (unlike the
        # trending gate at ≥2) because these are already high-confidence:
        # they passed an MS-MARCO cross-encoder threshold.
        if _semantic_recovered:
            _top_sem = ', '.join(
                s.title() for s in _semantic_recovered[:4]
            )
            strengths.insert(
                min(2, len(strengths)),
                f"Paraphrase-matched JD skills found in your experience: {_top_sem}"
            )

        if not strengths:
            strengths.append("Resume submitted for review")

        # Cap at 6 for clean UI
        strengths = strengths[:6]

        # ── Weaknesses ────────────────────────────────────────────────────
        weaknesses = []

        # Wrong-domain degree: prepended FIRST because it's the single most
        # decisive signal for an early-career application. A business
        # graduate applying for a software-engineer role needs to see
        # this BEFORE the skill-gap details — otherwise the report reads
        # like "you're missing Python and JavaScript" when the real
        # message is "your degree is in the wrong field".
        if _degree_mismatch and _expected_domain:
            if _degree_subject:
                weaknesses.append(
                    f"Your {_degree_subject} degree is in a different field "
                    f"to this {_expected_domain.title()} role — most "
                    f"applicants for this position will hold a "
                    f"{_expected_domain.title()}-related degree, which "
                    f"materially affects shortlisting"
                )
            else:
                weaknesses.append(
                    f"Your degree subject does not align with this "
                    f"{_expected_domain.title()} role — most applicants "
                    f"will hold a {_expected_domain.title()}-related "
                    f"degree, which materially affects shortlisting"
                )

        # Skip generic tech message when role profile is active — tier messages are more precise
        if not has_profile:
            if missing_tech and len(missing_tech) >= 3:
                top_tech = ', '.join(s.title() for s in sorted(missing_tech)[:4])
                weaknesses.append(
                    f"Key technical skills not found in your resume: {top_tech}"
                )
            elif missing_tech:
                top_tech = ', '.join(s.title() for s in sorted(missing_tech))
                weaknesses.append(
                    f"Missing technical skill(s): {top_tech}"
                )

        if missing_soft and len(missing_soft) >= 2:
            top_soft = ', '.join(s.title() for s in sorted(missing_soft)[:3])
            weaknesses.append(
                f"These soft skills aren't clearly demonstrated: {top_soft}"
            )

        # Soft skills that shouldn't appear in a "will disqualify you" hard-skills warning
        _SOFT_SKILL_SET = {
            "creativity", "attention to detail", "communication", "teamwork",
            "problem solving", "leadership", "adaptability", "collaboration",
            "critical thinking", "time management", "interpersonal skills",
            "organisational skills", "organizational skills", "multitasking",
        }

        if has_profile:
            # Tier-aware messages replace generic score-gap messages.
            # Only include hard/technical skills in the warning — soft
            # skills have their own message above.
            core_hard_missing = [s for s in core_missing if s.lower() not in _SOFT_SKILL_SET]
            if core_hard_missing:
                top_core = ', '.join(core_hard_missing[:3])
                # Tone shifts with seniority. For an intern role the same
                # gap is a *learning target*, not a disqualifier — most
                # internships exist precisely to teach these skills. For
                # a junior role they're skills the candidate should pick
                # up early. For mid/senior they remain non-negotiable.
                if role_level == 'intern':
                    weaknesses.append(
                        f"Skill{'s' if len(core_hard_missing) > 1 else ''} to develop "
                        f"before or during the internship: {top_core} — "
                        f"learning {'these' if len(core_hard_missing) > 1 else 'this'} "
                        f"will significantly strengthen your application"
                    )
                elif role_level == 'junior':
                    weaknesses.append(
                        f"Foundational skill{'s' if len(core_hard_missing) > 1 else ''} expected "
                        f"early in this role: {top_core} — "
                        f"hands-on projects or coursework demonstrating "
                        f"{'these' if len(core_hard_missing) > 1 else 'this'} would close the gap"
                    )
                else:
                    weaknesses.append(
                        f"Missing core skill{'s' if len(core_hard_missing) > 1 else ''} for this role: "
                        f"{top_core} — {'these are' if len(core_hard_missing) > 1 else 'this is'} "
                        f"non-negotiable and will likely disqualify your application"
                    )
        else:
            # Generic score-gap messages only when no role profile is detected
            if match_score < 35 and missing_skills:
                weaknesses.append(
                    f"Overall skill gap is significant — {len(missing_skills)} of "
                    f"{len(missing_skills) + len(found_skills)} required skills are missing"
                )
            elif match_score < 50 and missing_skills:
                weaknesses.append(
                    f"Your resume is missing {len(missing_skills)} skills required by this role"
                )
            elif match_score < 70 and len(missing_skills) >= 3:
                weaknesses.append(
                    f"{len(missing_skills)} required skill(s) are not clearly shown in your resume"
                )

        if has_profile and expected_missing and len(weaknesses) < 5:
            top_exp = ', '.join(expected_missing[:3])
            weaknesses.append(
                f"Expected skill{'s' if len(expected_missing) > 1 else ''} not shown: "
                f"{top_exp} — most candidates for this role have "
                f"{'these' if len(expected_missing) > 1 else 'this'}"
            )

        # ── Preferred / nice-to-have gaps ─────────────────────────────────
        # These don't penalise the score — shown as "would strengthen" hints
        if preferred_missing and len(weaknesses) < 5:
            top_pref = ', '.join(s.title() for s in preferred_missing[:3])
            n = len(preferred_missing)
            weaknesses.append(
                f"Nice-to-have skill{'s' if n > 1 else ''} not shown: {top_pref}"
                f"{f' (+{n - 3} more)' if n > 3 else ''}"
                f" — {'these aren\'t required but would strengthen your application'}"
            )

        # When a profile is detected, still surface JD-required skills that fall outside the profile tiers
        if has_profile and missing_skills and len(weaknesses) < 5:
            _tier_flagged = {s.lower() for s in core_missing + expected_missing + advanced_missing}
            _uncovered_missing = [s for s in missing_skills if s.lower() not in _tier_flagged]
            if _uncovered_missing and len(_uncovered_missing) >= 2:
                top_unc = ', '.join(_uncovered_missing[:4])
                weaknesses.append(
                    f"This role also requires: {top_unc} — not clearly shown in your resume"
                )

        # Only flag missing tech skills for roles that genuinely require technical skills
        _is_tech_role = is_dev_role or is_ai_role or is_pm_role
        if not resume_tech and _tech_skills & missing_lower_set and _is_tech_role:
            weaknesses.append(
                "No programming or technical skills detected — "
                "this role expects a technical background"
            )

        if len(resume_text) < 500:
            weaknesses.append("Resume may be too brief — add more detail about projects and experience")

        if not found_skills and not missing_skills:
            # Both lists empty means the JD itself failed to yield any
            # extractable skills (after the role-keyword fallback in
            # extract_keywords_from_job_description). The fault lies with
            # the JD's brevity, not with the candidate's resume — so the
            # message must point at the JD, never tell the candidate their
            # resume "lists no relevant technologies" when in fact the
            # strengths section above shows it does.
            weaknesses.append(
                "Job description is too brief to identify required skills — "
                "add more detail about the role's expectations to get a "
                "reliable match analysis"
            )

        # ── Context-aware weaknesses when missing list is small ──────
        # Even if the explicit missing list is short, provide useful feedback
        # based on what the role typically requires vs what the resume shows.
        _ai_ml_skills = {"machine learning", "deep learning", "tensorflow",
                         "pytorch", "computer vision", "nlp", "data science",
                         "scikit-learn", "opencv", "keras", "numpy", "pandas"}
        _devops_skills = {"docker", "kubernetes", "aws", "azure", "gcp",
                          "ci/cd", "terraform", "linux", "jenkins"}
        _web_skills = {"html", "css", "javascript", "typescript", "react",
                       "angular", "vue", "node.js"}

        if len(weaknesses) < 5:
            # role_text / is_*_role already defined at top of method

            # ── AI/ML role weaknesses ─────────────────────────────
            if is_ai_role:
                # Only flag AI skills that are explicitly required by this JD or inferred missing
                _jd_lower = set(s.lower() for s in job_skills)
                missing_ai = (_ai_ml_skills & (missing_lower_set | _jd_lower)) - resume_skill_set - found_lower
                if missing_ai and len(missing_ai) >= 2:
                    top = ', '.join(s.title() for s in sorted(missing_ai)[:4])
                    weaknesses.append(
                        f"Key AI/ML skills not evident in resume: {top}"
                    )
                if not (resume_skill_set | found_lower) & {"pytorch", "tensorflow", "keras"}:
                    weaknesses.append(
                        "No deep learning frameworks (TensorFlow/PyTorch) listed — "
                        "these are essential for AI developer roles"
                    )
                if "research" not in resume_skill_set and "writing" not in resume_skill_set:
                    weaknesses.append(
                        "AI roles often value research skills and technical writing"
                    )

            # ── Product/Project Management role weaknesses ────────
            if is_pm_role and len(weaknesses) < 5:
                _pm_skills = {"project management", "stakeholder management",
                              "strategic planning", "data analysis",
                              "presentation", "budgeting", "risk management"}
                _already_flagged = {s.lower() for s in core_missing + expected_missing}
                # Exclude skills found via synonym match as well
                missing_pm = _pm_skills - resume_skill_set - found_lower - _already_flagged
                if missing_pm and len(missing_pm) >= 2:
                    top = ', '.join(s.title() for s in sorted(missing_pm)[:4])
                    weaknesses.append(
                        f"Core management skills missing: {top}"
                    )
                if not (resume_skill_set | found_lower) & {"data analysis", "excel", "tableau",
                                                            "power bi", "sql"}:
                    weaknesses.append(
                        "No data analysis or reporting skills — product/project "
                        "managers need to make data-driven decisions"
                    )
                if not (resume_skill_set | found_lower) & {"stakeholder management",
                                                            "client relations", "negotiation"}:
                    weaknesses.append(
                        "Stakeholder engagement skills not demonstrated — "
                        "this is critical for management roles"
                    )
                if not re.search(r'(roadmap|backlog|okr|kpi|metric|sprint)',
                                 resume_lower):
                    weaknesses.append(
                        "No evidence of product/project artifacts (roadmaps, "
                        "OKRs, KPIs, backlogs) — highlight these in your experience"
                    )

            # ── Marketing role weaknesses ─────────────────────────
            if is_marketing_role and not is_dev_role and len(weaknesses) < 5:
                _mkt_skills = {"digital marketing", "seo", "google analytics",
                               "social media", "content marketing", "email marketing",
                               "data analysis", "crm"}
                _already_flagged = {s.lower() for s in core_missing + expected_missing}
                missing_mkt = _mkt_skills - resume_skill_set - found_lower - _already_flagged
                if missing_mkt and len(missing_mkt) >= 3:
                    top = ', '.join(s.title() for s in sorted(missing_mkt)[:4])
                    weaknesses.append(
                        f"Key marketing skills not evident in resume: {top}"
                    )
                if not (resume_skill_set | found_lower) & {"google analytics", "data analysis",
                                                            "tableau", "power bi", "excel"}:
                    weaknesses.append(
                        "No analytics or data tools found — marketing roles require "
                        "performance tracking (Google Analytics, Excel, Tableau)"
                    )
                if not (resume_skill_set | found_lower) & {"seo", "sem", "ppc", "digital marketing"}:
                    weaknesses.append(
                        "No digital marketing channels evident — "
                        "SEO, SEM, or paid media experience is expected"
                    )
                if not re.search(
                    r'(campaign|kpi|conversion|engagement|click.through|open rate|follower)',
                    resume_lower
                ):
                    weaknesses.append(
                        "No campaign results or marketing KPIs mentioned — "
                        "quantify your impact (open rates, CTR, follower growth)"
                    )

            # ── HR role weaknesses ────────────────────────────────
            if is_hr_role and len(weaknesses) < 5:
                _hr_skills = {"recruiting", "talent acquisition", "employee relations",
                              "onboarding", "hris", "training", "communication"}
                _already_flagged = {s.lower() for s in core_missing + expected_missing}
                missing_hr = _hr_skills - resume_skill_set - found_lower - _already_flagged
                if missing_hr and len(missing_hr) >= 2:
                    top = ', '.join(s.title() for s in sorted(missing_hr)[:4])
                    weaknesses.append(
                        f"Core HR competencies not clearly shown: {top}"
                    )
                if not (resume_skill_set | found_lower) & {"hris", "workday", "bamboohr", "sap"}:
                    weaknesses.append(
                        "No HRIS platform experience mentioned — "
                        "most HR roles require Workday, BambooHR, or SAP"
                    )
                if not re.search(r'(recruit|hire|interview|screen|onboard)', resume_lower):
                    weaknesses.append(
                        "No recruitment or talent acquisition activities demonstrated "
                        "— these are core to most HR roles"
                    )
                if not re.search(
                    r'(employment law|labour law|gdpr|right to work|compliance)',
                    resume_lower
                ):
                    weaknesses.append(
                        "No employment law or HR compliance knowledge mentioned — "
                        "this is important for HR roles"
                    )

            # ── Finance / Accounting role weaknesses ─────────────
            if is_finance_role and len(weaknesses) < 5:
                _fin_skills = {"financial analysis", "excel", "accounting",
                               "budgeting", "data analysis", "forecasting"}
                # Exclude skills already flagged by tier-aware core/expected messages or found via synonym
                _already_flagged = {s.lower() for s in core_missing + expected_missing}
                missing_fin = _fin_skills - resume_skill_set - found_lower - _already_flagged
                if missing_fin and len(missing_fin) >= 2:
                    top = ', '.join(s.title() for s in sorted(missing_fin)[:4])
                    weaknesses.append(
                        f"Core finance skills not clearly shown: {top}"
                    )
                if not (resume_skill_set | found_lower) & {"excel", "power bi", "tableau", "sql"}:
                    weaknesses.append(
                        "No financial modelling or reporting tools found — "
                        "Excel, Power BI, or SQL proficiency is expected"
                    )
                if not re.search(
                    r'(p&l|profit|budget|forecast|variance|reconcil|balance sheet|income statement)',
                    resume_lower
                ):
                    weaknesses.append(
                        "No financial documents or processes mentioned — "
                        "reference P&L, budgeting, or forecasting experience"
                    )
                if not resume_skill_set & {"accounting", "quickbooks", "xero",
                                           "sap", "oracle"}:
                    weaknesses.append(
                        "No accounting software mentioned — "
                        "experience with QuickBooks, Xero, or SAP is typically required"
                    )

            # ── Sales role weaknesses ─────────────────────────────
            if is_sales_role and len(weaknesses) < 5:
                _sales_skills = {"sales", "crm", "communication",
                                 "negotiation", "business development", "customer service"}
                _already_flagged = {s.lower() for s in core_missing + expected_missing}
                missing_sales = _sales_skills - resume_skill_set - found_lower - _already_flagged
                if missing_sales and len(missing_sales) >= 2:
                    top = ', '.join(s.title() for s in sorted(missing_sales)[:4])
                    weaknesses.append(
                        f"Core sales competencies not clearly shown: {top}"
                    )
                if not (resume_skill_set | found_lower) & {"salesforce", "hubspot", "zoho", "crm"}:
                    weaknesses.append(
                        "No CRM platform experience — Salesforce or HubSpot "
                        "knowledge is expected in most sales roles"
                    )
                if not re.search(
                    r'(quota|target|revenue|pipeline|deal|close|won|conversion)',
                    resume_lower
                ):
                    weaknesses.append(
                        "No sales results or quota attainment mentioned — "
                        "add deal sizes, win rates, or revenue generated"
                    )
                if not (resume_skill_set | found_lower) & {"communication", "negotiation", "presentation"}:
                    weaknesses.append(
                        "Client communication and negotiation skills not demonstrated"
                    )

            # ── Customer Service role weaknesses ──────────────────
            if is_customer_service_role and not is_sales_role and len(weaknesses) < 5:
                if not resume_skill_set & {"customer service", "communication",
                                           "problem solving"}:
                    weaknesses.append(
                        "Core customer service skills (communication, empathy, "
                        "problem solving) not clearly demonstrated"
                    )
                if not resume_skill_set & {"zendesk", "freshdesk", "salesforce", "crm"}:
                    weaknesses.append(
                        "No ticketing/CRM platform mentioned — "
                        "Zendesk or Freshdesk experience is common in support roles"
                    )
                if not re.search(
                    r'(resolv|satisf|nps|csat|escalat|ticket|sla)',
                    resume_lower
                ):
                    weaknesses.append(
                        "No customer satisfaction metrics or KPIs mentioned — "
                        "add resolution rates, CSAT scores, or SLA adherence"
                    )

            # ── Developer role weaknesses ─────────────────────────
            if is_dev_role and len(weaknesses) < 5:
                resume_devops = resume_skill_set & _devops_skills
                if not resume_devops:
                    weaknesses.append(
                        "No DevOps/cloud skills detected — consider adding "
                        "Docker, CI/CD, or cloud platform experience"
                    )

            # ── General resume quality checks ─────────────────────
            if len(weaknesses) < 5:
                has_degree = re.search(
                    r'(bsc|b\.sc|b\.s\.|bachelor|master|mba|phd|m\.sc|m\.s\.|'
                    r'doctorate|hons|honours|first class|second class|university|college)',
                    resume_lower
                )
                if not has_degree and not re.search(r'(certif|credential|licensed|accredited)', resume_lower):
                    weaknesses.append(
                        "No certifications mentioned — relevant certifications "
                        "can strengthen your application"
                    )
            if len(weaknesses) < 5:
                if is_dev_role or is_ai_role:
                    # Only flag missing repo if they don't mention GitHub/GitLab at all
                    if not re.search(r'(portfolio|github|gitlab|bitbucket)', resume_lower):
                        weaknesses.append(
                            "No portfolio or code repository links — "
                            "showcasing projects online adds credibility"
                        )
                elif not re.search(r'(portfolio|website|blog|linkedin)', resume_lower):
                    weaknesses.append(
                        "No professional portfolio or online presence mentioned — "
                        "a LinkedIn profile or personal website adds visibility"
                    )

        # ── Evidence-based weakness: skills claimed but not demonstrated ──
        # A skill that appears only in the "Skills" list (not in Experience /
        # Projects) is a weaker signal than one backed by role bullets.
        _claimed_only = evidence_summary.get('claimed_only', [])
        if _claimed_only and len(weaknesses) < 5:
            # Surface up to 3 skills that the JD cares about but that live only
            # in the skills list — those are the most useful to strengthen.
            _found_lower_list = [s.lower() for s in found_skills]
            _claimed_in_found = [
                s for s in _claimed_only if s.lower() in _found_lower_list
            ][:3]
            if _claimed_in_found:
                _top_claimed = ', '.join(s.title() for s in _claimed_in_found)
                weaknesses.append(
                    f"Listed but not demonstrated: {_top_claimed} — "
                    "add a project or role bullet showing how you used these"
                )

        if not weaknesses:
            weaknesses.append("No significant weaknesses identified")

        weaknesses = weaknesses[:5]

        # ── Recommendations ───────────────────────────────────────────────
        filtered_missing = [
            s for s in missing_skills
            if not self.job_analyzer.is_generic_word(s.lower())
            and not any(self.job_analyzer.is_generic_word(w)
                        for w in s.lower().split())
        ]

        # Start with the most specific / actionable items first
        recommendations = []

        # ── Wrong-domain degree: suggest concrete bridges ─────────────────
        # When the candidate's degree is in a different field, generic
        # "learn JavaScript" advice misses the bigger issue. Surface a
        # focused recommendation that names the gap and points at concrete
        # bridges (conversion course, bootcamp, transferable framing).
        if _degree_mismatch and _expected_domain:
            _bridges = {
                'computer science': (
                    "consider a computer science conversion course (MSc CS "
                    "Conversion at most UK universities — designed for "
                    "non-CS graduates), a structured bootcamp (Founders & "
                    "Coders, Codecademy CS Career Path), or completing a "
                    "verified portfolio project on GitHub before applying"
                ),
                'data science': (
                    "consider an MSc Data Science conversion programme or a "
                    "verified pipeline of online certificates (Google Data "
                    "Analytics, IBM Data Science Professional Certificate) "
                    "alongside a public Kaggle profile"
                ),
                'finance': (
                    "consider a CFA Level I, ACA / ACCA professional "
                    "qualification, or a postgraduate diploma in finance "
                    "to bridge the credential gap"
                ),
                'marketing': (
                    "consider Google Analytics + Meta Blueprint "
                    "certifications, or a CIM diploma, plus a portfolio of "
                    "campaigns you have run end-to-end"
                ),
                'medical':  "this role typically requires a medical degree — "
                            "alternative healthcare-adjacent roles (admin, "
                            "data, project management) may be more accessible",
                'legal':    "this role typically requires a law degree (LLB) "
                            "or conversion (GDL/PGDL) — consider those before "
                            "applying for legal roles",
            }
            bridge = _bridges.get(_expected_domain)
            if bridge:
                if _degree_subject:
                    recommendations.insert(0,
                        f"Bridge the credential gap: your {_degree_subject} "
                        f"background is in a different field — {bridge}"
                    )
                else:
                    recommendations.insert(0,
                        f"Bridge the credential gap to a "
                        f"{_expected_domain.title()} role: {bridge}"
                    )

        # ── CV-aware: detect abbreviations already in the resume that map to missing skills ──
        _CV_ALIASES = {
            'js': 'JavaScript', 'ts': 'TypeScript', 'py': 'Python',
            'ml': 'Machine Learning', 'dl': 'Deep Learning',
            'oop': 'Object-Oriented Programming', 'rest': 'REST API',
            'k8s': 'Kubernetes', 'tf': 'TensorFlow', 'ci/cd': 'CI/CD',
        }
        missing_lower_for_recs = {s.lower() for s in filtered_missing}
        alias_fixes = []
        for alias, full_name in _CV_ALIASES.items():
            if re.search(r'\b' + re.escape(alias) + r'\b', resume_lower):
                if full_name.lower() in missing_lower_for_recs:
                    alias_fixes.append(f"'{alias.upper()}' → '{full_name}'")
        if alias_fixes:
            recommendations.append(
                f"Your resume uses shorthand that ATS systems may not recognise — "
                f"spell these out explicitly: {', '.join(alias_fixes)}"
            )

        # ── Rephrase-focused: for skills the resume implicitly demonstrates ──
        _IMPLICIT_SKILL_MAP = {
            # ── Technical ────────────────────────────────────────────────
            'rest api':          [r'api', r'endpoint', r'http', r'fetch', r'axios',
                                  r'postman', r'flask', r'django', r'express'],
            'problem solving':   [r'debug', r'resolv', r'troubleshoot', r'optim',
                                  r'improv', r'achiev', r'solution'],
            'research':          [r'analys', r'investigat', r'evaluat', r'explor',
                                  r'study', r'experiment'],
            'writing':           [r'report', r'document', r'deck', r'proposal',
                                  r'present', r'stakeholder'],
            'testing':           [r'test', r'unit test', r'qa', r'debug', r'assert'],
            # ── Business-wide ────────────────────────────────────────────
            'data analysis':     [r'excel', r'pivot', r'dashboard', r'kpi', r'metric',
                                  r'analys', r'trend', r'tableau', r'power bi', r'report'],
            'communication':     [r'present', r'client', r'verbal', r'written',
                                  r'brief', r'correspond', r'liaise', r'report'],
            'teamwork':          [r'team', r'collaborat', r'cross.functional',
                                  r'work(ed)? with'],
            'leadership':        [r'led\b', r'manag\w+\s+\w*(team|staff|people)',
                                  r'mentor', r'supervis', r'direct\w'],
            'presentation':      [r'present\w', r'deck', r'slide', r'pitch', r'demo'],
            'project management': [r'coordinat', r'deadlines?', r'milestone', r'jira',
                                   r'gantt', r'roadmap', r'deliverable', r'timeline'],
            'stakeholder management': [r'stakeholder', r'cross.functional',
                                       r'execut', r'present.*to', r'client.*meet'],
            'analytical skills': [r'analys', r'evaluat', r'research', r'data',
                                  r'insight', r'trend', r'metric'],
            # ── Marketing ────────────────────────────────────────────────
            'digital marketing': [r'google analytics', r'social media', r'campaign',
                                  r'email marketing', r'seo', r'sem', r'ppc', r'hubspot'],
            'seo':               [r'search engine', r'keyword', r'organic', r'rank',
                                  r'backlink', r'on.page'],
            'social media':      [r'instagram', r'facebook', r'twitter', r'linkedin',
                                  r'tiktok', r'post', r'content calendar'],
            'content marketing': [r'blog', r'article', r'content', r'copy',
                                  r'editorial', r'content calendar'],
            'email marketing':   [r'newsletter', r'mailchimp', r'hubspot', r'campaign',
                                  r'open rate', r'click.through'],
            # ── HR ───────────────────────────────────────────────────────
            'recruiting':        [r'hire', r'recruit', r'interview', r'candidate',
                                  r'job description', r'shortlist'],
            'talent acquisition': [r'recruit', r'onboard', r'hire', r'talent pool',
                                   r'headhunt'],
            'employee relations': [r'performance review', r'appraisal', r'grievance',
                                   r'disciplinary', r'engagement'],
            'training':          [r'train', r'workshop', r'onboard', r'develop',
                                  r'coaching', r'mentoring'],
            # ── Finance ──────────────────────────────────────────────────
            'financial analysis': [r'budget', r'p[&/]l', r'forecast', r'revenue',
                                   r'cost', r'variance', r'financial model',
                                   r'balance sheet'],
            'budgeting':         [r'budget', r'forecast', r'spend', r'cost centre',
                                  r'allocat'],
            'accounting':        [r'reconciliation', r'accounts payable',
                                  r'accounts receivable', r'month.end',
                                  r'quickbooks', r'xero'],
            # ── Sales ────────────────────────────────────────────────────
            'sales':             [r'pipeline', r'quota', r'prospect', r'lead',
                                  r'deal', r'upsell', r'account', r'revenue target'],
            'business development': [r'prospect', r'lead gen', r'partner', r'pitch',
                                     r'deal', r'outreach'],
            'crm':               [r'salesforce', r'hubspot', r'zoho', r'pipeline',
                                  r'account', r'opportunity'],
            'negotiation':       [r'negotiat', r'close\w+\s+(deal|sale)',
                                  r'contract', r'agreement', r'terms'],
            # ── Customer Service ─────────────────────────────────────────
            'customer service':  [r'customer', r'client', r'resolv', r'support',
                                  r'ticket', r'query', r'complaint', r'satisfaction'],
        }
        rephrase_suggestions = []
        for skill, patterns in _IMPLICIT_SKILL_MAP.items():
            if skill in missing_lower_for_recs:
                if any(re.search(p, resume_lower) for p in patterns):
                    rephrase_suggestions.append(skill.title())
        if rephrase_suggestions:
            recommendations.append(
                f"Your experience already demonstrates these skills — "
                f"add them explicitly to your Technical/Skills section: "
                f"{', '.join(rephrase_suggestions)}"
            )
            # Remove from "prioritize learning" since they already have them
            filtered_missing = [s for s in filtered_missing if s.lower() not in {r.lower() for r in rephrase_suggestions}]

        # Add skill-specific actionable recommendations first (only for skills they don't already demonstrate)
        missing_for_recs = [s for s in filtered_missing if s.lower() not in _soft_skills]
        if missing_for_recs:
            top = missing_for_recs[:4]
            recommendations.append(
                f"Prioritize learning these skills: {', '.join(top)}"
            )

        # ── Course map ─────────────────────────────────────────────────────
        _course_map = {
            # Technical
            "python":            "Complete Python Bootcamp (Udemy) or Python for Everybody (Coursera)",
            "javascript":        "The Complete JavaScript Course (Udemy) or freeCodeCamp JavaScript",
            "java":              "Java Programming Masterclass (Udemy) or Java Fundamentals (Pluralsight)",
            "sql":               "SQL for Data Science (Coursera) or Complete SQL Bootcamp (Udemy)",
            "react":             "React — The Complete Guide (Udemy) or Full-Stack Open (University of Helsinki)",
            "git":               "Git & GitHub Crash Course (Udemy) or Version Control with Git (Coursera)",
            "docker":            "Docker Mastery (Udemy) or Introduction to Containers (Coursera)",
            "aws":               "AWS Cloud Practitioner Essentials (AWS free) or AWS Solutions Architect (Udemy)",
            "rest api":          "RESTful Web Services (Pluralsight) or API Design (Coursera)",
            "agile":             "Agile with Atlassian Jira (Coursera) or Scrum Master Certification prep",
            "data analysis":     "Google Data Analytics Certificate (Coursera)",
            "machine learning":  "Machine Learning by Andrew Ng (Coursera)",
            "deep learning":     "Deep Learning Specialization by Andrew Ng (Coursera)",
            "tensorflow":        "TensorFlow Developer Certificate (Google) or TensorFlow in Practice (Coursera)",
            "pytorch":           "PyTorch for Deep Learning (Udemy) or Intro to Deep Learning with PyTorch (Udacity)",
            "computer vision":   "CS231n (Stanford) or OpenCV Python Course (freeCodeCamp)",
            "nlp":               "NLP Specialization (Coursera) or Hugging Face Course (free)",
            "opencv":            "OpenCV Python Course (freeCodeCamp) or Computer Vision with OpenCV (Udemy)",
            "scikit-learn":      "Machine Learning with scikit-learn (DataCamp) or Hands-On ML (O'Reilly)",
            "numpy":             "NumPy for Data Science (DataCamp) or Python Data Science Handbook (free)",
            "pandas":            "Pandas for Data Analysis (DataCamp) or Python Data Science Handbook (free)",
            "tableau":           "Tableau Desktop Specialist Certification prep (Coursera)",
            "power bi":          "Microsoft Power BI Data Analyst (Microsoft Learn — free)",
            "excel":             "Microsoft Excel — Advanced (LinkedIn Learning) or MOS Certification",
            "figma":             "Figma UI/UX Design Essentials (Udemy)",
            "kubernetes":        "Kubernetes for Beginners (KodeKloud) or CKA Certification prep",
            "linux":             "Linux Foundation Certified SysAdmin (LF) or Linux Basics (Coursera)",
            # PM / Business
            "project management":    "Google Project Management Certificate (Coursera) or PMP Certification prep",
            "stakeholder management": "Stakeholder Engagement Strategies (LinkedIn Learning)",
            "strategic planning":    "Strategic Planning and Execution (Coursera)",
            "presentation":          "Presentation Skills: Speechwriting and Storytelling (Coursera)",
            "budgeting":             "Budgeting and Finance for Non-Financial Managers (Coursera)",
            "risk management":       "Risk Management Professional Certificate (PMI)",
            "leadership":            "Leadership and Management Specialization (Coursera)",
            "communication":         "Business Communication Skills (Coursera)",
            "negotiation":           "Successful Negotiation (Coursera, University of Michigan)",
            # Marketing
            "digital marketing":     "Google Digital Marketing & E-commerce Certificate (Coursera — free audit)",
            "seo":                   "SEO Fundamentals (SEMrush Academy — free) or Moz SEO Learning Center",
            "sem":                   "Google Ads Search Certification (Google — free)",
            "ppc":                   "Google Ads Certification (Google — free) or Facebook Blueprint",
            "social media":          "Social Media Marketing Specialization (Coursera) or HubSpot Social Media",
            "content marketing":     "HubSpot Content Marketing Certification (HubSpot Academy — free)",
            "email marketing":       "Email Marketing Certification (HubSpot Academy — free)",
            "google analytics":      "Google Analytics Certification (Google — free)",
            "marketing automation":  "HubSpot Marketing Hub Certification (free)",
            "copywriting":           "The Complete Copywriting Course (Udemy) or CopyHackers resources",
            "branding":              "Brand Management (Coursera, University of London)",
            "crm":                   "HubSpot CRM Certification (free) or Salesforce Trailhead (free)",
            # HR
            "recruiting":            "Recruiting, Hiring, and Onboarding Employees (Coursera)",
            "talent acquisition":    "LinkedIn Talent Solutions courses or CIPD HR Fundamentals",
            "employee relations":    "Employee Relations (LinkedIn Learning) or CIPD Level 3 Foundation",
            "hris":                  "Workday HCM Training (Workday Learning) or HRIS Fundamentals (Udemy)",
            "training":              "Training and Development (ATD) or L&D Essentials (LinkedIn Learning)",
            "learning and development": "L&D Essentials (LinkedIn Learning) or ATD Certificate Programme",
            "performance management": "Performance Management (LinkedIn Learning) or CIPD resources",
            "hr":                    "CIPD Foundation Level 3 or SHRM-CP Certification prep",
            # Finance / Accounting
            "financial analysis":    "Financial Analysis Fundamentals (CFI — free) or CFA Level 1 prep",
            "financial modelling":   "Financial Modelling & Valuation Analyst (CFI) or Excel Modelling (Udemy)",
            "accounting":            "Accounting Fundamentals (CFI — free) or AAT Level 2 Certificate",
            "forecasting":           "Financial Forecasting and Planning (Coursera)",
            "quickbooks":            "QuickBooks Online Certification (Intuit — free)",
            "xero":                  "Xero Advisor Certification (Xero — free)",
            "tax":                   "Tax Basics (Coursera) or ATT Certificate in Taxation",
            # Sales
            "sales":                 "Sales Training: Practical Sales Techniques (Udemy) or HubSpot Sales Certification",
            "business development":  "Business Development Fundamentals (LinkedIn Learning)",
            "account management":    "Key Account Management (LinkedIn Learning) or SPIN Selling (Udemy)",
            "salesforce":            "Salesforce Trailhead — Salesforce Admin Trail (free)",
            "hubspot":               "HubSpot Sales Hub Certification (HubSpot Academy — free)",
            # Customer Service
            "customer service":      "Customer Service Fundamentals (LinkedIn Learning) or Zendesk Training",
        }

        # ── Role-aware recommendations ─────────────────────────────────
        # role_text / is_*_role already defined at top of method

        if is_ai_role:
            ai_course_skills = ["machine learning", "deep learning", "tensorflow",
                                "pytorch", "computer vision", "nlp", "opencv",
                                "scikit-learn", "numpy", "pandas"]
            ai_courses = [
                f"{sk.title()}: {_course_map[sk]}"
                for sk in ai_course_skills
                if sk not in resume_skill_set and sk in _course_map
            ]
            if ai_courses:
                recommendations.append(
                    "Recommended AI/ML courses: " + "; ".join(ai_courses[:4])
                )
            if "pytorch" not in resume_skill_set and "tensorflow" not in resume_skill_set:
                recommendations.append(
                    "Learn TensorFlow or PyTorch — these are the two dominant "
                    "deep learning frameworks required for AI developer roles"
                )
            if not re.search(r'(kaggle|research paper|publication|arxiv)', resume_lower):
                recommendations.append(
                    "Participate in Kaggle competitions or contribute to open-source "
                    "AI projects to demonstrate practical ML experience"
                )
            if not re.search(r'(portfolio|github|gitlab)', resume_lower):
                recommendations.append(
                    "Create a GitHub portfolio showcasing AI/ML projects — "
                    "include model training notebooks, datasets, and results"
                )

        elif is_pm_role:
            pm_course_skills = ["project management", "stakeholder management",
                                "strategic planning", "data analysis", "presentation",
                                "budgeting", "risk management", "leadership"]
            pm_courses = [
                f"{sk.title()}: {_course_map[sk]}"
                for sk in pm_course_skills
                if sk not in resume_skill_set and sk in _course_map
            ]
            if pm_courses:
                recommendations.append(
                    "Recommended courses: " + "; ".join(pm_courses[:4])
                )
            if not resume_skill_set & {"agile", "scrum", "kanban"}:
                recommendations.append(
                    "Learn Agile/Scrum methodology — most product and project "
                    "management roles require this. Consider PSM I or CSM certification"
                )
            if not re.search(r'(roadmap|backlog|okr|kpi|sprint|user stor)', resume_lower):
                recommendations.append(
                    "Reframe your experience using PM language — mention "
                    "roadmaps, backlogs, user stories, KPIs, or sprint planning "
                    "where applicable"
                )
            if not re.search(r'(stakeholder|cross.functional|cross functional)', resume_lower):
                recommendations.append(
                    "Highlight cross-functional collaboration and stakeholder "
                    "management experience from your internships"
                )

        elif is_marketing_role:
            mkt_course_skills = ["digital marketing", "seo", "google analytics",
                                 "social media", "content marketing", "email marketing",
                                 "ppc", "marketing automation", "crm"]
            mkt_courses = [
                f"{sk.title()}: {_course_map[sk]}"
                for sk in mkt_course_skills
                if sk not in resume_skill_set and sk in _course_map
            ]
            if mkt_courses:
                recommendations.append(
                    "Recommended marketing courses: " + "; ".join(mkt_courses[:4])
                )
            if not resume_skill_set & {"google analytics", "data analysis"}:
                recommendations.append(
                    "Get Google Analytics certified (free via Google) — it's a "
                    "baseline requirement for almost every digital marketing role"
                )
            if not re.search(r'(campaign|kpi|conversion|ctr|open rate|impression|reach)', resume_lower):
                recommendations.append(
                    "Reframe your experience with marketing metrics — mention "
                    "campaign KPIs, conversion rates, CTR, or engagement figures"
                )
            if not resume_skill_set & {"hubspot", "mailchimp", "salesforce", "crm"}:
                recommendations.append(
                    "Complete the free HubSpot certifications (CRM, Email Marketing, "
                    "Content Marketing) — widely recognised by employers"
                )

        elif is_hr_role:
            hr_course_skills = ["recruiting", "talent acquisition", "employee relations",
                                "hris", "training", "learning and development",
                                "performance management"]
            hr_courses = [
                f"{sk.title()}: {_course_map[sk]}"
                for sk in hr_course_skills
                if sk not in resume_skill_set and sk in _course_map
            ]
            if hr_courses:
                recommendations.append(
                    "Recommended HR courses: " + "; ".join(hr_courses[:4])
                )
            if not re.search(r'(cipd|shrm|hrci|people cert)', resume_lower):
                recommendations.append(
                    "Consider a CIPD Level 3 Foundation Certificate or SHRM-CP — "
                    "these are the benchmark HR qualifications for employers"
                )
            if not resume_skill_set & {"hris", "workday", "bamboohr"}:
                recommendations.append(
                    "Learn an HRIS platform — Workday offers free training on "
                    "Workday Learning; BambooHR has free product tutorials"
                )
            if not re.search(r'(recruit|interview|onboard|talent)', resume_lower):
                recommendations.append(
                    "Highlight any recruitment or onboarding activities from "
                    "internships, volunteering, or university roles — even informal "
                    "involvement counts in early HR careers"
                )

        elif is_finance_role:
            fin_course_skills = ["financial analysis", "financial modelling",
                                 "excel", "accounting", "budgeting", "forecasting",
                                 "data analysis", "power bi"]
            fin_courses = [
                f"{sk.title()}: {_course_map[sk]}"
                for sk in fin_course_skills
                if sk not in resume_skill_set and sk in _course_map
            ]
            if fin_courses:
                recommendations.append(
                    "Recommended finance courses: " + "; ".join(fin_courses[:4])
                )
            if not re.search(r'(cfa|acca|cima|aca|cpa|aat)', resume_lower):
                recommendations.append(
                    "Consider a professional finance qualification — AAT (entry-level), "
                    "ACCA, CIMA, or CFA are well-regarded by finance employers"
                )
            if not resume_skill_set & {"excel", "power bi", "sql"}:
                recommendations.append(
                    "Build Excel proficiency (pivot tables, VLOOKUP, financial models) "
                    "— it is the most commonly tested skill in finance interviews"
                )
            if not re.search(r'(p&l|budget|forecast|variance|reconcil|balance sheet)', resume_lower):
                recommendations.append(
                    "Reframe your experience using finance language — reference "
                    "budgets managed, P&L ownership, or reconciliation activities"
                )

        elif is_sales_role:
            sales_course_skills = ["sales", "crm", "negotiation",
                                   "business development", "salesforce", "hubspot"]
            sales_courses = [
                f"{sk.title()}: {_course_map[sk]}"
                for sk in sales_course_skills
                if sk not in resume_skill_set and sk in _course_map
            ]
            if sales_courses:
                recommendations.append(
                    "Recommended sales courses: " + "; ".join(sales_courses[:4])
                )
            if not resume_skill_set & {"salesforce", "hubspot", "crm"}:
                recommendations.append(
                    "Complete Salesforce Trailhead (free) or HubSpot Sales "
                    "Certification — CRM proficiency is expected in all sales roles"
                )
            if not re.search(r'(quota|target|revenue|pipeline|deal|won|closed)', resume_lower):
                recommendations.append(
                    "Add measurable sales results — quota attainment %, revenue "
                    "generated, deals closed, or pipeline value managed"
                )
            if not resume_skill_set & {"negotiation", "communication"}:
                recommendations.append(
                    "Highlight negotiation and client communication examples "
                    "from internships or customer-facing roles"
                )

        elif is_customer_service_role:
            cs_courses = [
                f"{sk.title()}: {_course_map[sk]}"
                for sk in ["customer service", "communication", "crm"]
                if sk not in resume_skill_set and sk in _course_map
            ]
            if cs_courses:
                recommendations.append(
                    "Recommended courses: " + "; ".join(cs_courses[:3])
                )
            if not resume_skill_set & {"zendesk", "freshdesk", "salesforce", "crm"}:
                recommendations.append(
                    "Learn a support platform — Zendesk offers free training "
                    "at its Zendesk Training site"
                )
            if not re.search(r'(csat|nps|sla|resolv|ticket|satisfaction)', resume_lower):
                recommendations.append(
                    "Quantify your customer service impact — add CSAT scores, "
                    "resolution times, or ticket volumes handled"
                )

        else:
            # Generic: suggest courses for any missing skills with a known mapping
            course_suggestions = []
            for skill in filtered_missing[:4]:
                course = _course_map.get(skill.lower())
                if course:
                    course_suggestions.append(f"{skill}: {course}")
            if course_suggestions:
                recommendations.append(
                    "Recommended courses: " + "; ".join(course_suggestions)
                )

        # Suggest building projects for technical roles only
        if (is_dev_role or is_ai_role) and missing_tech and len(missing_tech) >= 2:
            recommendations.append(
                "Build portfolio projects using the missing technologies — "
                "personal projects and GitHub contributions are valued by employers"
            )

        if filtered_missing:
            top = filtered_missing[:5]
            recommendations.append(
                f"Add these keywords to your resume where applicable: {', '.join(top)}"
            )

        if not re.search(r'\d+%|\d+\s*(years?|months?)', resume_lower):
            recommendations.append(
                "Quantify achievements with specific metrics "
                "(e.g., 'increased sales by 20%', 'managed a team of 8')"
            )

        # Tailor advice for career changers (low score + transferable skills)
        if match_score < 40 and resume_soft and len(found_skills) <= 3:
            recommendations.append(
                "Highlight your transferable skills (communication, teamwork, "
                "problem-solving) and frame past experience in terms relevant "
                "to the target role"
            )

        # Append generic recommendations from the recommendation generator (at the end)
        generic_recs = self.recommendation_generator.get_recommendations(
            filtered_missing,
            role_type=role_type,
            industry=industry,
        )
        for rec in generic_recs:
            if rec not in recommendations:
                recommendations.append(rec)

        # ── AI Insight (3-part structure) ─────────────────────────────────
        # Pass calibrated score so the insight text matches what the UI shows
        match_results_for_insight = dict(match_results)
        match_results_for_insight['total_score'] = match_score
        ai_insight = self.ml_matcher.generate_ai_insight(
            match_results_for_insight,
            role_type=role_type,
            industry=industry,
        )

        # ── Rolling emerging-skills tracker ────────────────────────────────
        # Bump counters for JD tokens not yet in the curated dictionary.
        # Fail-soft — telemetry must never break analysis.
        try:
            from .emerging_skills import record_jd_tokens
            record_jd_tokens(job_description)
        except Exception:
            pass

        return {
            'matchScore': match_score,
            'foundSkills': found_skills[:15],
            'missingSkills': missing_skills[:15],
            'strengths': strengths,
            'weaknesses': weaknesses,
            'recommendations': recommendations[:6],
            'aiInsight': ai_insight,
            'resumeSkills': resume_skills[:30],
            'experienceLevel': match_results.get('role_level', 'mid'),
            # Calibrator diagnostics — surfaced so the feedback widget can
            # echo the feature vector back on submit, feeding the next
            # retraining cycle.  Also used by the bootstrap training script
            # to collect synthetic labeled rows.
            'scoringFeatures': _scoring_features,
            'calibratorDelta': float(_cal_delta) if _cal_delta else 0.0,
        }
