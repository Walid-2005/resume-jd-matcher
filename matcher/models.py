import json

from django.db import models
from django.contrib.auth.models import User


class AnalysisFeedback(models.Model):
    """User-submitted feedback on an analysis result.

    Attached to an AnalysisHistory record when the submitter is authenticated
    and a history id is available.  Anonymous / history-less submissions are
    still accepted — the 'snapshot' field captures enough context (score,
    found/missing skills, JD excerpt) to treat the row as self-contained.
    """

    SCORE_RATING_CHOICES = [
        ('too_high', 'Too high'),
        ('accurate', 'Accurate'),
        ('too_low',  'Too low'),
    ]

    analysis = models.ForeignKey(
        'AnalysisHistory',
        on_delete=models.SET_NULL,
        related_name='feedback',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='submitted_feedback',
        null=True,
        blank=True,
    )

    # Primary signal: is the computed score accurate, too high, or too low?
    score_rating = models.CharField(
        max_length=16,
        choices=SCORE_RATING_CHOICES,
        null=True,
        blank=True,
    )
    # Secondary signal: overall usefulness rating, 1 (poor) to 5 (excellent).
    usefulness = models.PositiveSmallIntegerField(null=True, blank=True)
    # Optional freeform comment.
    comment = models.TextField(blank=True, default='')

    # Context snapshot — captured at submission time so the row remains
    # self-contained even if the history entry is deleted later.
    match_score    = models.IntegerField(null=True, blank=True)
    snapshot       = models.JSONField(default=dict, blank=True)
    jd_excerpt     = models.TextField(blank=True, default='')

    # Light client metadata for abuse / duplicate detection
    user_agent = models.CharField(max_length=255, blank=True, default='')
    ip_hash    = models.CharField(max_length=64, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['score_rating']),
        ]

    def __str__(self) -> str:
        who = self.user.username if self.user_id else 'anonymous'
        return f"Feedback #{self.pk} by {who} ({self.score_rating or '—'})"


class EmergingSkill(models.Model):
    """Rolling aggregation of JD tokens NOT yet in the skill dictionary.

    Populated opportunistically after each analysis: the raw-token extractor
    surfaces candidate skills (acronyms, CamelCase, .NET-style) from the JD
    text, we compare against the known skill set, and anything novel bumps
    a counter here.  Over time, tokens that appear in many JDs bubble up as
    "trending" — a signal for the maintainers to promote them into the
    curated skill dictionary (and for scoring to give them a modest weight
    bump in the meantime).

    Intentionally anonymous — no user / analysis FK — since we only want
    aggregate frequency, not per-user traceability.
    """
    token       = models.CharField(max_length=64, unique=True, db_index=True)
    mentions    = models.PositiveIntegerField(default=1)
    first_seen  = models.DateTimeField(auto_now_add=True)
    last_seen   = models.DateTimeField(auto_now=True)

    # Set to True by maintainers once the token has been promoted into the
    # curated SKILL_DICTIONARY.  Promoted rows are kept for history but
    # excluded from the "trending" query.
    is_promoted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-mentions', '-last_seen']
        indexes = [
            models.Index(fields=['-mentions']),
            models.Index(fields=['-last_seen']),
            models.Index(fields=['is_promoted']),
        ]

    def __str__(self) -> str:
        return f"{self.token} ×{self.mentions}"


class UserProfile(models.Model):
    """Extended user profile."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class AnalysisHistory(models.Model):
    """Stores a resume-job analysis result linked to a user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_history')
    match_score = models.IntegerField()
    found_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    ai_insight = models.TextField(blank=True, default='')
    job_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Analysis histories'

    def __str__(self):
        return f"{self.user.username} — {self.match_score}% ({self.created_at:%Y-%m-%d %H:%M})"

    def to_dict(self):
        """Serialize to a dict matching the frontend AnalysisHistory shape."""
        return {
            'id': self.id,
            'matchScore': self.match_score,
            'foundSkills': self.found_skills,
            'missingSkills': self.missing_skills,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'recommendations': self.recommendations,
            'aiInsight': self.ai_insight,
            'jobDescription': self.job_description,
            'createdAt': self.created_at.isoformat(),
        }

