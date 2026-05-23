"""
Rolling emerging-skills tracker.

After each analysis, we feed the JD through the raw-token extractor and
bump a counter for any token that ISN'T already a known skill.  Tokens that
appear in many recent JDs bubble up as "trending" — a signal that the
curated SKILL_DICTIONARY is lagging behind the market (e.g. Bun, Cursor,
LangChain, pgvector, Retool, Zod…).

Intentionally lightweight:
  * No per-user / per-analysis attribution — aggregates only.
  * `record_jd_tokens()` is fail-soft — any DB error is swallowed so a
    telemetry hiccup never breaks analysis for the user.
  * A token is considered "known" if it matches any value in
    ``SKILL_DICTIONARY`` OR any tier of any profile in
    ``ROLE_SKILL_PROFILES`` OR any entry in ``ROLE_SKILL_TEMPLATES``.
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Iterable, List, Optional

from django.db import transaction
from django.db.models import F
from django.utils import timezone

logger = logging.getLogger(__name__)

# Tokens too short or too generic to be meaningful new skills.  Keep this
# list small — the raw-token extractor already filters a large noise set
# upstream; this is a secondary sieve specific to the persistence layer.
_PERSIST_NOISE: frozenset = frozenset({
    # Geo / market codes
    'us', 'uk', 'eu', 'na', 'uae', 'usa', 'emea', 'apac', 'latam',
    # C-suite and degree shorthand
    'ceo', 'cto', 'cfo', 'coo', 'cio', 'cmo',
    'phd', 'bsc', 'msc', 'mba', 'ba', 'bs', 'ms',
    # Abstract concepts that match the acronym pattern but aren't skills
    'oop', 'solid', 'dry', 'kiss',
    # Ops metrics
    'eta', 'sla', 'slo', 'sli', 'mttr',
    # Timing shorthand
    'eod', 'eob', 'asap', 'tbd', 'tba',
    # Over-broad two-letter matches ("AI", "IT", "HR", "PR", "QA")
    # — real skills like "AI/ML" still get captured via compound tokens.
    'ai', 'it', 'hr', 'pr', 'qa',
    # Meta-mentions of work type
    'fte', 'eoe', 'dei',
})

# Characters to strip from raw-token tails.  The upstream raw-token regex
# sometimes captures trailing sentence punctuation (e.g. "Bun." or
# "Next.js.") because '.' is a valid inner character for tokens like
# "Node.js" — we can't tighten the regex without losing those.  Stripping
# a trailing dot in the persistence layer is the safe fix.
_STRIP_TAIL = '.,;:)]'

# Persisted tokens are capped at 64 chars by the model; this is a safety trim.
_MAX_TOKEN_LEN = 64


def _collect_known_skills() -> set[str]:
    """Build the lowercase set of all currently-curated skill names.

    A token counts as "known" if it appears in:
      - any domain value list in SKILL_DICTIONARY
      - any tier of any profile in ROLE_SKILL_PROFILES
      - any flat template in ROLE_SKILL_TEMPLATES

    Cached via function-local import so we rebuild once per process start.
    """
    from .ml_matcher import SKILL_DICTIONARY, ROLE_SKILL_TEMPLATES
    from .trained_skills import ROLE_SKILL_PROFILES

    known: set[str] = set()
    for skills in SKILL_DICTIONARY.values():
        known.update(s.lower() for s in skills)
    for profile in ROLE_SKILL_PROFILES.values():
        for tier_skills in profile.values():
            known.update(s.lower() for s in tier_skills)
    for skills in ROLE_SKILL_TEMPLATES.values():
        known.update(s.lower() for s in skills)
    return known


_KNOWN_CACHE: Optional[set[str]] = None


def _known_skills_cached() -> set[str]:
    """Memoised view of the known-skill set (rebuilt once per process)."""
    global _KNOWN_CACHE
    if _KNOWN_CACHE is None:
        _KNOWN_CACHE = _collect_known_skills()
    return _KNOWN_CACHE


def record_jd_tokens(jd_text: str) -> List[str]:
    """Bump the EmergingSkill counter for any novel tokens in ``jd_text``.

    Fail-soft: any exception (DB down, table missing, etc.) is logged at
    warning level and swallowed.  Telemetry must never break analysis.

    Returns:
        The list of tokens that were recorded (lowercased), for tests and
        log inspection.  Empty list on any failure.
    """
    if not jd_text or len(jd_text.strip()) < 20:
        return []

    try:
        from .ml_matcher import extract_raw_jd_tokens
        from ..models import EmergingSkill
    except Exception as e:           # pragma: no cover
        logger.warning("emerging_skills: import failed: %s", e)
        return []

    known = _known_skills_cached()
    raw_tokens = extract_raw_jd_tokens(jd_text, known_skills=None)

    novel: list[str] = []
    for tok in raw_tokens:
        k = tok.lower().strip().rstrip(_STRIP_TAIL)
        if not k or len(k) < 2 or len(k) > _MAX_TOKEN_LEN:
            continue
        # Re-check the known set after stripping — "bun." → "bun" might be
        # a false positive once trailing punctuation is removed.
        if k in known or k in _PERSIST_NOISE:
            continue
        novel.append(k)

    if not novel:
        return []

    try:
        with transaction.atomic():
            for k in novel:
                # Upsert: increment existing row OR create a new one with
                # mentions=1.  update_or_create is concise but does a fresh
                # insert if missing, which is what we want.
                obj, created = EmergingSkill.objects.get_or_create(
                    token=k, defaults={'mentions': 1},
                )
                if not created:
                    EmergingSkill.objects.filter(pk=obj.pk).update(
                        mentions=F('mentions') + 1,
                        last_seen=timezone.now(),
                    )
    except Exception as e:           # pragma: no cover
        logger.warning("emerging_skills: record failed: %s", e)
        return []

    return novel


def get_trending_token_set(
    min_mentions: int = 3,
    within_days: int = 30,
) -> set[str]:
    """Return lowercase set of tokens currently considered "trending".

    Cached briefly at the call-site level — the scoring pipeline calls this
    once per analysis, and the set is small, so we don't bother with a
    process-wide TTL cache.  If the trending list ever grows large, wrap
    this in functools.lru_cache with a time-based key.

    Fail-soft: any DB / import error returns an empty set, so the scoring
    pipeline treats "no trending data available" as "no bonus to give",
    never as "crash the analysis".
    """
    try:
        from ..models import EmergingSkill
    except Exception as e:           # pragma: no cover
        logger.warning("emerging_skills: import failed: %s", e)
        return set()

    try:
        cutoff = timezone.now() - timedelta(days=within_days)
        rows = EmergingSkill.objects.filter(
            mentions__gte=min_mentions,
            last_seen__gte=cutoff,
            is_promoted=False,
        ).values_list('token', flat=True)
        return {t.lower() for t in rows}
    except Exception as e:           # pragma: no cover
        logger.warning("emerging_skills: trending set query failed: %s", e)
        return set()


def get_trending_skills(
    min_mentions: int = 3,
    within_days: int = 30,
    limit: int = 20,
    include_promoted: bool = False,
) -> List[dict]:
    """Return top trending skills by recent mention count.

    Args:
        min_mentions:     Minimum cumulative mentions to qualify.
        within_days:      Only consider tokens last seen in this window.
        limit:            Cap on returned rows.
        include_promoted: If False (default), skip rows that have already
                          been promoted into the curated dictionary.

    Returns:
        List of dicts: {token, mentions, first_seen, last_seen}.
    """
    try:
        from ..models import EmergingSkill
    except Exception as e:           # pragma: no cover
        logger.warning("emerging_skills: import failed: %s", e)
        return []

    cutoff = timezone.now() - timedelta(days=within_days)
    qs = EmergingSkill.objects.filter(
        mentions__gte=min_mentions,
        last_seen__gte=cutoff,
    )
    if not include_promoted:
        qs = qs.filter(is_promoted=False)
    qs = qs.order_by('-mentions', '-last_seen')[:limit]

    return [
        {
            'token':       row.token,
            'mentions':    row.mentions,
            'first_seen':  row.first_seen.isoformat(),
            'last_seen':   row.last_seen.isoformat(),
        }
        for row in qs
    ]


def purge_stale(older_than_days: int = 90, max_mentions: int = 2) -> int:
    """Delete low-frequency tokens that haven't been seen in a while.

    Keeps the table from growing unboundedly on noisy / one-off JDs.  A
    token mentioned ≥3 times is never purged regardless of age, since it
    represents a real signal that has just gone cold.

    Args:
        older_than_days: Tokens with last_seen older than this are eligible.
        max_mentions:    Only purge tokens with mentions ≤ this value.

    Returns:
        Number of rows deleted.
    """
    try:
        from ..models import EmergingSkill
    except Exception as e:           # pragma: no cover
        logger.warning("emerging_skills: import failed: %s", e)
        return 0

    cutoff = timezone.now() - timedelta(days=older_than_days)
    deleted, _ = EmergingSkill.objects.filter(
        last_seen__lt=cutoff,
        mentions__lte=max_mentions,
        is_promoted=False,
    ).delete()
    return deleted
