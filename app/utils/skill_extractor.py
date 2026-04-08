"""
Skill extraction from CV text using NLP and pattern matching.

Skills are now fetched live from the Laravel database via db_client.get_skills_db()
instead of being hardcoded. Job requisition skills are passed dynamically
per-request for scoring/matching.
"""
import re
from typing import List, Dict, Tuple
from .db_client import (
    get_skills_db,
    get_skill_category,
    is_desired_skill,
    build_dynamic_desired_skills,
)


class SkillExtractor:
    """Extract skills from CV text using the database-driven skills dictionary."""

    def __init__(self):
        self.min_word_length = 2

    @property
    def skills_db(self) -> Dict[str, Dict]:
        """Lazily return the live skills dictionary from the DB (cached internally)."""
        return get_skills_db()

    def extract_skills(self, text: str, job_requisition_skills: list = None) -> Dict:
        """
        Extract skills from CV text and score them against job requisition skills.

        Args:
            text: CV text content.
            job_requisition_skills: List of skill name strings from the job requisition
                                    (fetched from the database and passed at request time).

        Returns:
            Dictionary containing extracted skills categorised by type, plus match score.
        """
        desired_skills = build_dynamic_desired_skills(job_requisition_skills or [])
        normalized_text = self._normalize_text(text)
        found_skills = self._find_skills(normalized_text)
        categorized_skills = self._categorize_skills(found_skills, desired_skills)

        technical_skills = categorized_skills.get("technical", [])
        language_skills  = categorized_skills.get("language", [])
        framework_skills = categorized_skills.get("framework", [])

        match_score = self._calculate_match_score(
            technical_skills, language_skills, framework_skills, desired_skills
        )

        has_desired = any(
            is_desired_skill(s["skill"] if isinstance(s, dict) else s, desired_skills)
            for s in technical_skills
        )

        matched_requisition_skills = [
            s["skill"] if isinstance(s, dict) else s
            for s in technical_skills
            if is_desired_skill(s["skill"] if isinstance(s, dict) else s, desired_skills)
        ]

        return {
            "skills_found":               found_skills,
            "technical_skills":           technical_skills,
            "language_skills":            language_skills,
            "framework_skills":           framework_skills,
            "total_skills_count":         len(found_skills),
            "has_desired_skills":         has_desired,
            "match_score":                round(match_score, 2),
            "job_requisition_skills":     desired_skills,
            "matched_requisition_skills": matched_requisition_skills,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalize_text(self, text: str) -> str:
        """Normalise CV text for processing."""
        if not text or not isinstance(text, str):
            return ""
        try:
            text = text.lower()
            text = re.sub(r'\s+', ' ', text)
            # Keep dots and slashes for framework names (node.js, ci/cd, etc.)
            text = re.sub(r'[^\w\s./+#-]', ' ', text)
            return text.strip()
        except Exception as e:
            print(f"Error normalizing text: {str(e)}")
            return ""

    def _find_skills(self, text: str) -> List[Tuple[str, float]]:
        """
        Find skills in CV text using word-boundary matching against the DB skills dict.

        Returns:
            List of (skill_name, confidence) tuples, sorted by confidence desc.
        """
        found_skills    = []
        found_skill_set = set()
        db              = self.skills_db   # single cache read per call

        if not text or not db:
            return found_skills

        for skill in db.keys():
            try:
                if not isinstance(skill, str) or not skill.strip():
                    continue

                pattern = r'\b' + re.escape(skill) + r'\b'
                matches = re.findall(pattern, text)

                if matches:
                    confidence = min(0.95, 0.7 + (len(matches) * 0.05))
                    if skill not in found_skill_set:
                        found_skills.append((skill, confidence))
                        found_skill_set.add(skill)
            except Exception:
                continue

        found_skills.sort(key=lambda x: x[1], reverse=True)
        return found_skills

    def _categorize_skills(
        self,
        skills: List[Tuple[str, float]],
        desired_skills: list = None,
    ) -> Dict[str, List[Dict]]:
        """Categorise found skills. Category comes from the DB via db_client."""
        desired_skills = desired_skills or []

        # Map DB category names → bucket names
        _BUCKET = {
            "technical": "technical",
            "language":  "language",
            "soft":      "soft",
            "other":     "other",
            "unknown":   "other",
        }

        categories: Dict[str, List] = {
            "technical": [],
            "language":  [],
            "soft":      [],
            "other":     [],
        }

        if not skills:
            return {"technical": [], "language": [], "framework": []}

        for skill, confidence in skills:
            try:
                if not skill or not isinstance(skill, str) or confidence is None:
                    continue

                raw_category = get_skill_category(skill)          # from db_client
                bucket       = _BUCKET.get(raw_category, "other")

                skill_obj = {
                    "skill":      skill.strip(),
                    "confidence": round(float(confidence), 2),
                    "category":   raw_category,
                    "is_desired": is_desired_skill(skill, desired_skills),
                }

                categories[bucket].append(skill_obj)
            except Exception:
                continue

        # Build response structure: technical bucket includes language too so
        # callers get a single "all hard skills" list alongside the split views.
        return {
            "technical": categories["technical"] + categories["language"],
            "language":  categories["language"],
            "framework": [],  # framework sub-category not stored in DB; kept for API compat
        }

    def _calculate_match_score(
        self,
        technical: List,
        languages: List,
        frameworks: List,
        desired_skills: list = None,
    ) -> float:
        """
        Calculate overall match score (0-100).

        • When job requisition skills are provided → score = % of required skills found (0-80)
          + bonus points for extra breadth (0-20).
        • Without requisition skills → general skill-count heuristic.
        """
        try:
            desired_skills = desired_skills or []

            if not isinstance(technical,  (list, tuple)): technical  = []
            if not isinstance(languages,  (list, tuple)): languages  = []
            if not isinstance(frameworks, (list, tuple)): frameworks = []

            # --- Requisition-aware scoring ---
            if desired_skills:
                all_candidate = set(
                    (s["skill"] if isinstance(s, dict) else str(s)).lower().strip()
                    for s in technical
                )
                matched       = [sk for sk in desired_skills if sk in all_candidate]
                total_req     = len(desired_skills)
                req_score     = (len(matched) / total_req) * 80 if total_req > 0 else 0
                extra_bonus   = min(20, (len(technical) - len(matched)) * 2)
                return round(min(100, max(0, req_score + extra_bonus)), 2)

            # --- Fallback: general heuristic ---
            base = 0.0
            if languages: base += min(30, len(languages) * 10)
            if technical: base += min(30, len(technical) * 5)
            return round(min(100, max(0, base)), 2)

        except Exception as e:
            print(f"Error calculating match score: {str(e)}")
            return 0.0


def extract_skills_from_text(text: str, job_requisition_skills: list = None) -> Dict:
    """Convenience function to extract skills from text."""
    extractor = SkillExtractor()
    return extractor.extract_skills(text, job_requisition_skills or [])
