"""
Database client for fetching skills from the Laravel application.

Replaces the hardcoded skills_database.py by pulling live data from the
`skills` table via the Laravel API endpoint:
    GET {LARAVEL_APP_URL}/api/hr/cv-analyzer/skills

Skills are cached in-process for CACHE_TTL_SECONDS to avoid hitting the DB
on every CV analysis request.
"""
import os
import time
import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (reads from environment – set LARAVEL_APP_URL in .env)
# ---------------------------------------------------------------------------
LARAVEL_APP_URL: str = os.getenv("LARAVEL_APP_URL", "http://SmarttelErpSystem.test")
CACHE_TTL_SECONDS: int = int(os.getenv("SKILLS_CACHE_TTL", "300"))   # 5 minutes default
REQUEST_TIMEOUT: int = int(os.getenv("LARAVEL_REQUEST_TIMEOUT", "10"))

# category enum names from Laravel → simple string label used internally
_CATEGORY_MAP: Dict[str, str] = {
    "TECHNICAL": "technical",
    "SOFT":      "soft",
    "LANGUAGE":  "language",
    "OTHER":     "other",
}

# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------
_skills_cache: Optional[Dict[str, Dict]] = None  # {skill_name_lower: {"category": str}}
_cache_fetched_at: float = 0.0


def _is_cache_valid() -> bool:
    """Return True if the in-memory cache is still fresh."""
    return _skills_cache is not None and (time.time() - _cache_fetched_at) < CACHE_TTL_SECONDS


def _fetch_from_api() -> Dict[str, Dict]:
    """
    Call the Laravel API and return skills as a dict keyed by lowercase skill name.

    Format: { "php": {"category": "technical"}, "laravel": {"category": "technical"}, ... }
    """
    url = f"{LARAVEL_APP_URL.rstrip('/')}/api/hr/cv-analyzer/skills"
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()

        skills: Dict[str, Dict] = {}
        for item in payload.get("data", []):
            name = (item.get("name") or "").strip()
            if not name:
                continue
            category_raw = item.get("category", "TECHNICAL")
            category = _CATEGORY_MAP.get(category_raw.upper(), "technical")
            skills[name.lower()] = {"category": category}

        logger.info(f"Fetched {len(skills)} skills from Laravel API ({url})")
        return skills

    except Exception as exc:
        logger.warning(
            f"Could not fetch skills from Laravel API ({url}): {exc}. "
            "Returning empty skill set – CV extraction will still work but pattern matching will be limited."
        )
        return {}


def get_skills_db() -> Dict[str, Dict]:
    """
    Return cached skills dict, refreshing from the API when the cache expires.

    Thread-safety: For a single-worker Uvicorn process this is fine.
    For multi-worker deployments consider replacing with Redis or a shared cache.
    """
    global _skills_cache, _cache_fetched_at

    if not _is_cache_valid():
        _skills_cache = _fetch_from_api()
        _cache_fetched_at = time.time()

    return _skills_cache or {}


def invalidate_cache() -> None:
    """Force the next call to re-fetch from the API."""
    global _cache_fetched_at
    _cache_fetched_at = 0.0


# ---------------------------------------------------------------------------
# Helper functions (previously lived in skills_database.py)
# ---------------------------------------------------------------------------

def get_skill_category(skill: str) -> str:
    """Return the category string for a skill name."""
    if not skill or not isinstance(skill, str):
        return "unknown"
    db = get_skills_db()
    return db.get(skill.lower().strip(), {}).get("category", "unknown")


def build_dynamic_desired_skills(job_requisition_skills: list) -> list:
    """
    Normalise job requisition skill names (from the DB) into lowercase list
    ready for comparison against CV-extracted skills.
    """
    if not job_requisition_skills or not isinstance(job_requisition_skills, list):
        return []
    return [s.lower().strip() for s in job_requisition_skills if isinstance(s, str) and s.strip()]


def is_desired_skill(skill: str, desired_skills: list = None) -> bool:
    """Return True if the skill is in the provided required-skills list."""
    if not skill or not isinstance(skill, str):
        return False
    if not desired_skills:
        return False
    try:
        return skill.lower().strip() in desired_skills
    except Exception:
        return False
