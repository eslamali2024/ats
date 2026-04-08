"""
Personal information extraction from CV text
Extracts: name, email, phone, age, birth date, location, etc.
"""
import re
from typing import Dict, Optional
from datetime import datetime


class PersonalInfoExtractor:
    """Extract personal information from CV text."""

    def __init__(self):
        # Patterns for email detection
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Patterns for phone detection
        self.phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International format
            r'\(\d{3}\)\s?\d{3}-\d{4}',  # (123) 456-7890
            r'\d{3}[-.]?\d{3}[-.]?\d{4}',  # 123-456-7890
        ]
        
        # Age patterns
        self.age_patterns = [
            r'age[:\s]+(\d{1,2})',  # age: 25
            r'age\s+(\d{1,2})',     # age 25
            r'(\d{1,2})\s+years?\s+old',  # 25 years old
        ]
        
        # Birth date patterns
        self.birth_patterns = [
            r'date\s+of\s+birth[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'dob[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'born[:\s]+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            r'b\.?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ]

    def extract_personal_info(self, text: str) -> Dict:
        """
        Extract personal information from CV text.
        
        Args:
            text: CV text content
            
        Returns:
            Dictionary containing extracted personal information
        """
        if not text or not isinstance(text, str):
            return self._empty_response()
        
        try:
            # Extract each field
            fullname = self._extract_name(text)
            email = self._extract_email(text)
            phone = self._extract_phone(text)
            age = self._extract_age(text)
            birth_date = self._extract_birth_date(text)
            location = self._extract_location(text)
            summary = self._extract_summary(text)
            education = self._extract_education(text)
            work_experience = self._extract_work_experience(text)
            
            return {
                "fullname": fullname,
                "email": email,
                "phone": phone,
                "age": age,
                "birth_date": birth_date,
                "location": location,
                "summary": summary,
                "education": education,
                "work_experience": work_experience,
                "extraction_confidence": self._calculate_confidence(
                    fullname, email, phone, age, birth_date, education, work_experience
                ),
                "expertise_years": self._calculate_expertise_years(work_experience, text)
            }
        except Exception as e:
            print(f"Error extracting personal info: {str(e)}")
            return self._empty_response()

    def _extract_name(self, text: str) -> str:
        """
        Extract full name from CV text.
        Usually appears at the beginning or after 'Name:' label.
        """
        try:
            lines = text.split('\n')
            
            # Look for explicit name field
            for line in lines[:20]:  # Check first 20 lines
                line_lower = line.lower()
                if line_lower.startswith('name:'):
                    name = line.split(':', 1)[1].strip()
                    if name and len(name) > 2:
                        return name
                elif line_lower.startswith('full name:'):
                    name = line.split(':', 1)[1].strip()
                    if name and len(name) > 2:
                        return name
            
            # Look for name pattern in first line or top lines
            for line in lines[:5]:
                line = line.strip()
                # Name should have capitals and no numbers/symbols (mostly)
                if line and len(line) > 2 and len(line) < 100:
                    # Check if it looks like a name (has spaces, capitals, no numbers)
                    if self._looks_like_name(line):
                        return line
            
            # Fallback: get first substantial line
            for line in lines:
                line = line.strip()
                if line and len(line) > 3 and len(line) < 100:
                    if self._looks_like_name(line):
                        return line
            
            return ""
        except Exception:
            return ""

    def _looks_like_name(self, text: str) -> bool:
        """Check if text looks like a name."""
        if not text or len(text) < 2:
            return False
        
        # Should have at least one capital letter
        if not any(c.isupper() for c in text):
            return False
        
        # Should not have too many numbers
        if sum(c.isdigit() for c in text) > 3:
            return False
        
        # Should have mostly letters and spaces
        letters_and_spaces = sum(1 for c in text if c.isalpha() or c.isspace())
        if letters_and_spaces < len(text) * 0.7:
            return False
        
        return True

    def _extract_email(self, text: str) -> str:
        """Extract email address from CV text."""
        try:
            matches = re.findall(self.email_pattern, text, re.IGNORECASE)
            if matches:
                # Return the most legitimate looking email (typically .com, .org, etc)
                return matches[0]
            return ""
        except Exception:
            return ""

    def _extract_phone(self, text: str) -> str:
        """Extract phone number from CV text."""
        try:
            for pattern in self.phone_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    return matches[0]
            return ""
        except Exception:
            return ""

    def _extract_age(self, text: str) -> Optional[int]:
        """Extract age from CV text."""
        try:
            text_lower = text.lower()
            for pattern in self.age_patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    age = int(matches[0])
                    # Validate age is reasonable (18-80)
                    if 18 <= age <= 80:
                        return age
            return None
        except Exception:
            return None

    def _extract_birth_date(self, text: str) -> str:
        """Extract birth date from CV text."""
        try:
            text_lower = text.lower()
            for pattern in self.birth_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    date_str = matches[0]
                    # Validate date format
                    if self._validate_date(date_str):
                        return date_str
            return ""
        except Exception:
            return ""

    def _validate_date(self, date_str: str) -> bool:
        """Validate if string is a valid date."""
        try:
            date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%y', '%d-%m-%y']
            for fmt in date_formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False

    def _extract_location(self, text: str) -> str:
        """
        Extract location/city information from CV text.
        Looks for common location indicators.
        """
        try:
            text_lower = text.lower()
            lines = text.split('\n')
            
            # Common location keywords
            location_keywords = ['location:', 'city:', 'based in', 'based at', 'residency', 'residence']
            
            for line in lines[:30]:  # Check first 30 lines
                line_lower = line.lower()
                for keyword in location_keywords:
                    if keyword in line_lower:
                        # Extract after the keyword
                        parts = line_lower.split(keyword, 1)
                        if len(parts) > 1:
                            location = parts[1].strip()
                            # Clean up and limit length
                            location = re.sub(r'[,.]$', '', location).strip()
                            if location and len(location) < 100:
                                return location
            
            return ""
        except Exception:
            return ""

    def _extract_summary(self, text: str) -> str:
        """
        Extract professional summary or objective from CV text.
        Usually appears after name/contact info.
        """
        try:
            lines = text.split('\n')
            
            # Keywords that indicate summary section
            summary_keywords = ['summary', 'objective', 'professional objective', 'profile', 'about', 'career summary', 'professional summary']
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Look for summary header
                for keyword in summary_keywords:
                    if keyword in line_lower:
                        # Found the summary header, collect next non-empty lines
                        summary_lines = []
                        j = i + 1
                        
                        while j < len(lines) and len(summary_lines) < 4:
                            next_line = lines[j].strip()
                            
                            # Skip empty lines
                            if not next_line:
                                j += 1
                                continue
                            
                            # Check if it's a section header
                            next_lower = next_line.lower()
                            
                            # If line is all caps and relatively short, it's likely a header
                            if next_line.isupper() and len(next_line) > 3 and len(next_line) < 50:
                                break
                            
                            # Section keywords must be at the start of the line or after whitespace
                            section_markers = ['^experience', '^education', '^skills', '^projects', '^certifications', '^awards', '^languages', '^technical']
                            if any(next_lower.startswith(marker.replace('^', '')) for marker in section_markers):
                                break
                            
                            # Add this line to summary
                            summary_lines.append(next_line)
                            j += 1
                        
                        summary = ' '.join(summary_lines).strip()
                        if len(summary) > 10:  # Minimum length
                            return summary[:500]
                        
            return ""
        except Exception as e:
            return ""

    def _calculate_confidence(self, name: str, email: str, phone: str, age: Optional[int], birth_date: str, education: list, work_experience: list) -> float:
        """Calculate confidence score (0-1) based on extracted fields."""
        confidence = 0.0
        max_score = 9.0
        
        if name:
            confidence += 1.0
        if email:
            confidence += 1.0
        if phone:
            confidence += 1.0
        if age is not None:
            confidence += 1.0
        if birth_date:
            confidence += 1.0
        if education and len(education) > 0:
            confidence += 1.5
        if work_experience and len(work_experience) > 0:
            confidence += 1.5
        
        return round(confidence / max_score, 2)

    def _empty_response(self) -> Dict:
        """Return empty response structure."""
        return {
            "fullname": "",
            "email": "",
            "phone": "",
            "age": None,
            "birth_date": "",
            "location": "",
            "summary": "",
            "education": [],
            "work_experience": [],
            "extraction_confidence": 0.0,
            "expertise_years": None
        }

    def _calculate_expertise_years(self, work_experience: list, text: str):
        """
        Estimate years of professional experience.
        Strategy:
        1. Look for explicit "X years of experience" patterns in text.
        2. If not found, infer from work_experience date ranges by computing span from earliest start to latest end.
        Returns float (years) or None.
        """
        try:
            # 1) explicit patterns
            text_lower = text.lower()
            # common patterns like "5 years of experience", "5+ years experience"
            m = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)\s*(?:of\s*)?experience", text_lower)
            if m:
                try:
                    return float(m.group(1))
                except Exception:
                    pass

            # patterns like "experience: 5 years" or "5 years experience"
            m2 = re.search(r"experience[:\s]*([0-9]{1,2}(?:\.[0-9])?)\s*(?:years|yrs)", text_lower)
            if m2:
                try:
                    return float(m2.group(1))
                except Exception:
                    pass

            # 2) infer from work_experience date ranges
            years = []
            current_year = datetime.now().year
            for exp in work_experience:
                duration = exp.get("duration", "") if isinstance(exp, dict) else str(exp)
                if not duration:
                    continue

                # Normalize common separators
                duration_clean = duration.replace('\u2013', '-').replace('\u2014', '-').replace('–', '-').strip()

                # Look for ranges like 2019-2022 or 2019 - Present
                m_range = re.search(r"(19|20)\d{2}\s*[-–—]\s*(present|current|(19|20)\d{2})", duration_clean, re.IGNORECASE)
                if m_range:
                    start_year_match = re.search(r"(19|20)\d{2}", duration_clean)
                    if start_year_match:
                        start_year = int(start_year_match.group(0))
                    else:
                        continue
                    end_match = re.search(r"(present|current)", duration_clean, re.IGNORECASE)
                    if end_match:
                        end_year = current_year
                    else:
                        end_year_search = re.findall(r"(19|20)\d{2}", duration_clean)
                        end_year = int(end_year_search[-1]) if end_year_search else start_year
                    years.append((start_year, end_year))
                    continue

                # Single year entries
                m_year = re.search(r"\b(19|20)\d{2}\b", duration_clean)
                if m_year:
                    y = int(m_year.group(0))
                    years.append((y, y))

            if years:
                starts = [s for s, e in years]
                ends = [e for s, e in years]
                min_start = min(starts)
                max_end = max(ends)
                span = max_end - min_start
                # Return at least 1 year if span is 0
                return float(span if span > 0 else 1)

            return None
        except Exception:
            return None

    def _extract_education(self, text: str) -> list:
        """
        Extract education information from CV text.
        Returns list of education entries with degree, institution, date.
        """
        try:
            education_list = []
            lines = text.split('\n')
            
            # Keywords that indicate education section
            education_keywords = ['education', 'academic', 'qualification', 'degree', 'certification', 'academic background']
            
            in_education_section = False
            section_start_idx = -1
            
            # Find education section
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if this is education section header
                for keyword in education_keywords:
                    if keyword in line_lower and line_lower.startswith(keyword):
                        in_education_section = True
                        section_start_idx = i
                        break
                
                # Check if we've hit another section while in education
                if in_education_section and i > section_start_idx + 1:
                    if line_lower and line_lower.isupper() and len(line_lower) > 3:
                        # This is likely another section header
                        if any(sec in line_lower for sec in ['experience', 'skills', 'projects']):
                            break
                
                # Extract education entries (look for degree keywords)
                if in_education_section and i > section_start_idx:
                    line = line.strip()
                    if not line or line.isupper():
                        continue
                    
                    # Look for degree keywords
                    degree_keywords = ['bachelor', 'master', 'phd', 'diploma', 'associate', 'b.s', 'b.a', 'm.s', 'm.a', 'b.tech', 'm.tech', 'degree']
                    line_lower = line.lower()
                    
                    if any(deg in line_lower for deg in degree_keywords) and len(line) < 150:
                        education_entry = {
                            "degree": line,
                            "institution": "",
                            "year": ""
                        }
                        
                        # Extract year from degree line first
                        year_match = re.search(r'\b(19|20)\d{2}\b', line)
                        if year_match:
                            education_entry["year"] = year_match.group(0)
                        
                        # Try to find institution on next line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if next_line and not next_line.isupper() and len(next_line) < 150:
                                if not any(deg in next_line.lower() for deg in degree_keywords):
                                    education_entry["institution"] = next_line
                                    # Check next line for year if not found yet
                                    if not education_entry["year"] and i + 2 < len(lines):
                                        year_line = lines[i + 2].strip()
                                        year_match = re.search(r'\b(19|20)\d{2}\b', year_line)
                                        if year_match:
                                            education_entry["year"] = year_match.group(0)
                        
                        education_list.append(education_entry)
            
            return education_list[:3]  # Return max 3 education entries
        except Exception:
            return []

    def _extract_work_experience(self, text: str) -> list:
        """
        Extract work experience information from CV text.
        Returns list of work experience with job title, company, duration.
        """
        try:
            experience_list = []
            lines = text.split('\n')
            
            # Keywords that indicate experience section
            experience_keywords = ['experience', 'professional experience', 'work history', 'employment', 'career', 'work background']
            
            in_experience_section = False
            section_start_idx = -1
            
            # Find experience section
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                
                # Check if this is experience section header
                for keyword in experience_keywords:
                    if keyword in line_lower and (line_lower.startswith(keyword) or ':' in line):
                        in_experience_section = True
                        section_start_idx = i
                        break
                
                # Check if we've hit another section
                if in_experience_section and i > section_start_idx + 1:
                    other_sections = ['education', 'skills', 'projects', 'certifications', 'languages', 'technical', 'summary', 'objective', 'certifications']
                    if line_lower and any(sec in line_lower for sec in other_sections):
                        if line_lower.isupper() or ':' in line:
                            break
                
                # Extract job entries
                if in_experience_section and i > section_start_idx:
                    line = line.strip()
                    if not line or line.isupper():
                        continue
                    
                    # Look for job title indicators (contains position keywords)
                    job_keywords = ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'architect', 'lead', 'director', 'officer', 'coordinator', 'assistant', 'consultant', 'designer', 'trainer', 'administrator']
                    line_lower = line.lower()
                    
                    # Avoid degree keywords
                    degree_keywords = ['bachelor', 'master', 'phd', 'diploma', 'associate', 'b.s', 'b.a', 'm.s', 'm.a']
                    has_degree_keyword = any(deg in line_lower for deg in degree_keywords)
                    
                    # Job title usually has a job keyword, doesn't have degree keyword, and is not too long
                    if any(job in line_lower for job in job_keywords) and not has_degree_keyword and len(line) < 100:
                        # Skip if line looks like education (e.g., "Master of Science")
                        if 'of' in line_lower and len(line_lower.split()) <= 4:
                            continue
                            
                        experience_entry = {
                            "job_title": line,
                            "company": "",
                            "duration": ""
                        }
                        
                        # Try to find company on next line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            # Company name usually different from job title
                            if next_line and not any(job in next_line.lower() for job in job_keywords) and len(next_line) < 100:
                                # Check if it's a date line (contains years or "present")
                                if re.search(r'\d{4}|present|current', next_line.lower()):
                                    experience_entry["duration"] = next_line
                                else:
                                    experience_entry["company"] = next_line
                        
                        # Look for dates in job title line
                        years = re.findall(r'\b(19|20)\d{2}\b', line)
                        if len(years) >= 2:
                            experience_entry["duration"] = f"{years[0]}-{years[1]}"
                        elif len(years) == 1:
                            # Check for "present" or range
                            if 'present' in line_lower or 'current' in line_lower:
                                experience_entry["duration"] = f"{years[0]}-Present"
                        
                        # Only add if we have at least job title
                        if experience_entry["job_title"]:
                            experience_list.append(experience_entry)
            
            return experience_list[:5]  # Return max 5 work experiences
        except Exception:
            return []


def extract_personal_info(text: str) -> Dict:
    """Convenience function to extract personal info from text."""
    extractor = PersonalInfoExtractor()
    return extractor.extract_personal_info(text)
