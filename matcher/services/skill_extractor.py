"""
Enhanced skill extraction that recognizes skills from experience descriptions.
"""
import re


class SkillExtractor:
    """Extract skills from text, including from experience descriptions."""
    
    def __init__(self, common_skills):
        self.common_skills = common_skills
        
        # Skill indicators in experience descriptions
        self.skill_indicators = {
            'customer service': [
                'customer service', 'client service', 'guest service', 'customer relations',
                'customer inquiries', 'customer complaints', 'customer enquiries',
                'serving customers', 'client-facing', 'guest relations'
            ],
            'communication': [
                'presented', 'presentation', 'communicated', 'communication',
                'answered queries', 'dealt with', 'liaised', 'corresponded',
                'written', 'verbal', 'email', 'phone', 'telephone'
            ],
            'multitasking': [
                'multitasking', 'multi-tasking', 'multiple tasks', 'simultaneously',
                'at the same time', 'while also', 'in addition to'
            ],
            'problem solving': [
                'resolved', 'resolving', 'problem solving', 'problem-solving',
                'solved', 'troubleshooting', 'addressed issues', 'handled complaints'
            ],
            'cash handling': [
                'cash', 'cash management', 'cash up', 'cash handling', 'tills',
                'point of sale', 'pos', 'payment processing', 'transactions'
            ],
            'training': [
                'trained', 'training', 'mentored', 'mentoring', 'supported new',
                'taught', 'onboarded', 'inducted'
            ],
            'leadership': [
                'deputised', 'deputized', 'led', 'managed', 'supervised',
                'coordinated', 'organized', 'organised'
            ],
            'attention to detail': [
                'attention to detail', 'detail-oriented', 'precise', 'accuracy',
                'accurate', 'ensured', 'verified', 'checked'
            ],
            'microsoft office': [
                'microsoft office', 'ms office', 'word', 'excel', 'powerpoint',
                'outlook', 'teams', 'planner', 'office suite'
            ]
        }
    
    def extract_skills_from_experience(self, text):
        """
        Extract skills from experience descriptions, not just skills sections.
        Returns a set of skills found.
        """
        text_lower = text.lower()
        found_skills = set()
        
        # Check for skill indicators
        for skill_name, indicators in self.skill_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    # Check if this skill is in our common_skills list
                    skill_normalized = skill_name.replace(' ', '').replace('-', '')
                    for common_skill in self.common_skills:
                        if len(common_skill) < 2:
                            continue
                        if skill_normalized in common_skill.lower().replace(' ', '').replace('-', ''):
                            found_skills.add(common_skill.title())
                            break
                    # Also add the skill name itself if it matches our format
                    if any(skill_name in s.lower() for s in self.common_skills if len(s) >= 2):
                        for s in self.common_skills:
                            if len(s) >= 2 and skill_name in s.lower():
                                found_skills.add(s.title())
                                break
        
        # Also extract from explicit skill mentions in text
        # Look for patterns like "skills in X", "proficient in Y", "experience with Z"
        skill_patterns = [
            r'skills?\s+in\s+([a-z\s]+?)(?:\.|,|\n|$)',
            r'proficient\s+in\s+([a-z\s]+?)(?:\.|,|\n|$)',
            r'experience\s+with\s+([a-z\s]+?)(?:\.|,|\n|$)',
            r'knowledge\s+of\s+([a-z\s]+?)(?:\.|,|\n|$)',
            r'competent\s+in\s+([a-z\s]+?)(?:\.|,|\n|$)',
            r'highly\s+competent\s+user\s+of\s+([a-z\s]+?)(?:\.|,|\n|$)',
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Extract skills from the match
                words = match.strip().split()
                if len(words) <= 3:  # Reasonable skill phrase
                    potential_skill = ' '.join(words)
                    # Check if it matches any common skill
                    for common_skill in self.common_skills:
                        # Skip single-character entries (e.g. 'r') — they
                        # produce false positives by matching as substrings
                        # inside unrelated words like "docker" or "required".
                        if len(common_skill) < 2:
                            continue
                        cs_lower = common_skill.lower()
                        # For single-word skills, require a whole-word match to
                        # avoid 'go' matching inside "knowledge", 'r' in "docker", etc.
                        if ' ' not in cs_lower:
                            if re.search(r'\b' + re.escape(cs_lower) + r'\b', potential_skill.lower()):
                                found_skills.add(common_skill.title())
                        else:
                            # Multi-word skills: substring match is fine
                            if potential_skill.lower() in cs_lower or cs_lower in potential_skill.lower():
                                found_skills.add(common_skill.title())
        
        return list(found_skills)



