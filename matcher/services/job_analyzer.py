"""
Job description analyzer to extract role type, key requirements, and context.
"""
import re


class JobAnalyzer:
    """Analyze job descriptions to extract role information and requirements."""
    
    def __init__(self):
        # Role type patterns
        self.role_patterns = {
            'front_desk': [
                r'front\s+desk', r'receptionist', r'front\s+office', r'guest\s+services',
                r'concierge', r'hotel\s+reception', r'lobby\s+attendant'
            ],
            'hospitality': [
                r'hospitality', r'hotel', r'resort', r'hospitality\s+industry',
                r'luxury\s+hotel', r'five\s+star', r'five-star', r'boutique\s+hotel'
            ],
            'customer_service': [
                r'customer\s+service', r'client\s+service', r'guest\s+service',
                r'customer\s+support', r'guest\s+relations'
            ],
            'retail': [
                r'retail', r'sales\s+associate', r'store\s+assistant', r'cashier'
            ],
            'developer': [
                r'developer', r'programmer', r'engineer', r'software\s+engineer'
            ],
            'analyst': [
                r'analyst', r'data\s+analyst', r'business\s+analyst'
            ]
        }
        
        # Generic words to filter out (not skills)
        self.generic_words = {
            'desk', 'guest', 'resort', 'hotel', 'star', 'five', 'maintain', 'process',
            'manage', 'handle', 'ensure', 'provide', 'coordinate', 'respond', 'welcome',
            'greet', 'responsibilities', 'qualifications', 'requirements', 'key',
            'skills', 'ability', 'experience', 'previous', 'preferred', 'required',
            'essential', 'must', 'should', 'duties', 'role', 'position', 'job',
            'looking', 'seeking', 'hiring', 'ideal', 'candidate', 'team', 'department',
            'attention', 'professional', 'customer', 'service', 'receptionist', 'detail',
            'appearance', 'demeanor', 'manner', 'environment', 'software', 'system',
            'systems', 'record', 'records', 'information', 'local', 'attractions',
            'facilities', 'clean', 'organized', 'area', 'payment', 'payments', 'cash',
            'transaction', 'transactions', 'booking', 'reservation', 'reservations',
            'check-in', 'check-out', 'inquiry', 'inquiries', 'complaint', 'complaints',
            'issue', 'issues', 'department', 'housekeeping', 'phone', 'call', 'calls',
            'email', 'emails', 'flexible', 'hours', 'evening', 'evenings', 'weekend',
            'weekends', 'holiday', 'holidays', 'multilingual', 'plus'
        }
    
    def analyze_job(self, job_description):
        """
        Analyze job description to extract role type, key requirements, and context.
        
        Returns:
            dict with keys: role_type, industry, key_requirements, context_phrases
        """
        job_lower = job_description.lower()
        
        # Detect role type
        role_type = None
        industry = None
        
        for role, patterns in self.role_patterns.items():
            for pattern in patterns:
                if re.search(pattern, job_lower):
                    if role == 'hospitality':
                        industry = 'hospitality'
                    elif role_type is None:  # Don't override more specific roles
                        role_type = role
                    break
        
        # Extract key requirements/skills mentioned
        requirement_patterns = [
            r'(required|essential|must have|should have)[:;]?\s*([^\.\n]+)',
            r'(qualifications|requirements|skills)[:;]?\s*([^\.\n]+)',
            r'key\s+(responsibilities|requirements)[:;]?\s*([^\.\n]+)',
        ]
        
        key_requirements = []
        for pattern in requirement_patterns:
            matches = re.findall(pattern, job_lower, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    req_text = match[-1] if len(match) > 1 else match[0]
                else:
                    req_text = match
                # Extract skill-like phrases (2-4 words)
                words = req_text.split()
                if 2 <= len(words) <= 4:
                    key_requirements.append(req_text.strip())
        
        # Extract context phrases (luxury, five-star, fast-paced, etc.)
        context_patterns = [
            r'(luxury|five-star|five star|boutique|premium)',
            r'(fast-paced|fast paced|dynamic|high-volume)',
            r'(professional|polished|excellent|strong)',
        ]
        
        context_phrases = []
        for pattern in context_patterns:
            matches = re.findall(pattern, job_lower, re.IGNORECASE)
            context_phrases.extend(matches)
        
        return {
            'role_type': role_type,
            'industry': industry,
            'key_requirements': key_requirements[:5],  # Top 5
            'context_phrases': list(set(context_phrases))[:5]
        }
    
    def is_generic_word(self, word):
        """Check if a word is generic and should be filtered out."""
        return word.lower() in self.generic_words
    
    def get_role_specific_requirements(self, role_type, industry):
        """
        Get typical requirements for a specific role type.
        Returns a list of expected skills/requirements.
        """
        requirements = {
            'front_desk': [
                'customer service', 'communication', 'multitasking', 'problem solving',
                'microsoft office', 'phone etiquette', 'reservation systems',
                'cash handling', 'attention to detail', 'professional appearance'
            ],
            'hospitality': [
                'hospitality experience', 'guest relations', 'customer service',
                'communication', 'multitasking', 'flexible schedule'
            ],
            'customer_service': [
                'customer service', 'communication', 'problem solving',
                'patience', 'empathy', 'active listening'
            ]
        }
        
        req_list = []
        if role_type and role_type in requirements:
            req_list.extend(requirements[role_type])
        if industry and industry in requirements:
            req_list.extend(requirements[industry])
        
        return list(set(req_list))

