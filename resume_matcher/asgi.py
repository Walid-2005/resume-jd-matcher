"""
ASGI config for resume_matcher project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_matcher.settings')

application = get_asgi_application()

