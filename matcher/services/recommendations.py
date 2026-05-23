"""
Generate specific course and certification recommendations based on missing skills.
"""
import re


class RecommendationGenerator:
    """Generate actionable recommendations including courses and certifications."""

    def __init__(self):
        self.course_recommendations = {
            'customer service': [
                'Customer Service Excellence Certificate (Coursera/edX)',
                'Hospitality and Customer Service Training (LinkedIn Learning)',
                'Customer Relationship Management (CRM) Fundamentals',
            ],
            'communication': [
                'Business Communication Skills (Coursera)',
                'Professional Writing and Communication (edX)',
                'Effective Communication in the Workplace (Udemy)',
            ],
            'hospitality': [
                'Hospitality Management Certificate (Coursera)',
                'Hotel Operations and Management (edX)',
                'Front Office Operations Course (AHLEI)',
            ],
            'front desk': [
                'Front Desk Receptionist Training (Udemy)',
                'Hotel Front Office Operations (Coursera)',
                'Property Management System (PMS) Training',
            ],
            'reservation systems': [
                'Hotel Reservation Systems Training',
                'Opera PMS Certification (Oracle)',
                'Property Management Software Fundamentals',
            ],
            'cash handling': [
                'Cash Handling and Payment Processing',
                'Point of Sale (POS) Systems Training',
                'Financial Transactions and Accounting Basics',
            ],
            'microsoft office': [
                'Microsoft Office Specialist (MOS) Certification',
                'Excel for Business (Coursera/edX)',
                'Advanced Microsoft Office Suite (LinkedIn Learning)',
            ],
            'problem solving': [
                'Critical Thinking and Problem Solving (Coursera)',
                'Business Analysis Fundamentals',
                'Decision Making and Problem Solving (LinkedIn Learning)',
            ],
            'multitasking': [
                'Time Management and Productivity',
                'Effective Multitasking in Professional Environments',
                'Organizational Skills and Task Prioritization',
            ],
            'attention to detail': [
                'Quality Assurance and Accuracy Training',
                'Data Entry and Verification Skills',
                'Precision and Detail-Oriented Work Practices',
            ],
            'languages': [
                'Language Proficiency Certification (DELF, DELE, etc.)',
                'Business Language Skills Training',
                'Professional Communication in Multiple Languages',
            ],
            'project management': [
                'Google Project Management Certificate (Coursera)',
                'PMP Certification Prep (PMI)',
                'Agile Project Management (LinkedIn Learning)',
            ],
            'data analysis': [
                'Google Data Analytics Professional Certificate (Coursera)',
                'Data Analysis with Python (freeCodeCamp)',
                'Excel for Data Analysis (LinkedIn Learning)',
            ],
            'stakeholder management': [
                'Stakeholder Engagement Strategies (LinkedIn Learning)',
                'Business Relationship Management (Coursera)',
            ],
            'strategic planning': [
                'Strategic Planning and Execution (Coursera)',
                'Business Strategy Specialization (Coursera)',
            ],
            'presentation': [
                'Presentation Skills: Speechwriting and Storytelling (Coursera)',
                'PowerPoint Masterclass (Udemy)',
                'Public Speaking and Presentations (LinkedIn Learning)',
            ],
            'leadership': [
                'Leadership and Management Specialization (Coursera)',
                'Developing Leadership Skills (LinkedIn Learning)',
            ],
        }

        self.certification_recommendations = {
            'hospitality': [
                'Certified Hospitality Professional (CHP)',
                'Certified Guest Service Professional (CGSP)',
                'AHLEI certifications',
            ],
            'customer service': [
                'Customer Service Excellence Certification',
                'Professional Customer Service Certificate (ICS)',
            ],
            'microsoft office': [
                'Microsoft Office Specialist (MOS)',
                'Microsoft 365 Fundamentals',
            ],
            'project management': [
                'PMP (Project Management Professional)',
                'CAPM (Certified Associate in Project Management)',
                'PSM I (Professional Scrum Master)',
            ],
            'data analysis': [
                'Google Data Analytics Certificate',
                'IBM Data Analyst Professional Certificate',
            ],
        }

    def get_recommendations(self, missing_skills, role_type=None, industry=None):
        """
        Generate specific course and certification recommendations.

        Returns each recommendation as a single, self-contained string
        (no orphaned headers or sub-bullets).
        """
        recommended_courses = set()
        recommended_certs = set()

        missing_lower = [s.lower() for s in missing_skills]

        # Role-specific recommendations
        if role_type == 'front_desk' and industry == 'hospitality':
            for course in self.course_recommendations.get('front desk', []):
                recommended_courses.add(course)
            for cert in self.certification_recommendations.get('hospitality', []):
                recommended_certs.add(cert)
            for course in self.course_recommendations.get('reservation systems', []):
                recommended_courses.add(course)

        # Skill-specific lookups
        _skill_mapping = {
            'customer service': ['customer service', 'client service'],
            'communication': ['communication'],
            'hospitality': ['hospitality', 'hotel', 'resort'],
            'reservation systems': ['reservation', 'booking', 'pms'],
            'cash handling': ['cash', 'payment', 'pos'],
            'microsoft office': ['microsoft', 'office'],
            'problem solving': ['problem', 'solving'],
            'multitasking': ['multitask'],
            'attention to detail': ['attention', 'detail'],
            'project management': ['project management'],
            'data analysis': ['data analysis', 'analytics'],
            'stakeholder management': ['stakeholder'],
            'strategic planning': ['strategic'],
            'presentation': ['presentation', 'public speaking'],
            'leadership': ['leadership'],
        }

        for category, triggers in _skill_mapping.items():
            if any(any(t in skill for t in triggers) for skill in missing_lower):
                for course in self.course_recommendations.get(category, []):
                    recommended_courses.add(course)
                for cert in self.certification_recommendations.get(category, []):
                    recommended_certs.add(cert)

        # ── Build self-contained recommendation strings ───────────
        recommendations = []

        if recommended_courses:
            courses_list = list(recommended_courses)[:4]
            recommendations.append(
                "Recommended training: " + "; ".join(courses_list)
            )

        if recommended_certs:
            certs_list = list(recommended_certs)[:3]
            recommendations.append(
                "Relevant certifications to pursue: " + "; ".join(certs_list)
            )

        return recommendations
