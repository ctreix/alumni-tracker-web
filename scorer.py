import re
from typing import Dict, Any, List, Tuple
try:
    from thefuzz import fuzz
except ImportError:
    from rapidfuzz import fuzz


class AlumniScorer:
    """Scoring and Disambiguation Logic for Alumni Profiling"""
    
    # Scoring weights - adjusted for better accuracy
    SCORE_NAME_MATCH_HIGH = 40      # >80% fuzzy match
    SCORE_NAME_MATCH_MEDIUM = 25    # 60-80% fuzzy match
    SCORE_NAME_MATCH_LOW = 10       # 40-60% fuzzy match
    SCORE_UMM_MENTION = 30
    SCORE_UMM_LINKEDIN = 35         # Extra bonus for LinkedIn + UMM
    SCORE_PRODI_KEYWORD = 20
    SCORE_CAREER_KEYWORD = 15       # Related career keywords
    
    # Thresholds - adjusted for 100 max realistic score
    THRESHOLD_STRONG = 75           # ≥75: Strong identification
    THRESHOLD_VERIFY = 45           # 45-74: Needs verification
    THRESHOLD_WEAK = 20             # 20-44: Weak match
    
    def __init__(self):
        self.umm_keywords = [
            'umm', 'universitas muhammadiyah malang', 
            'muhammadiyah malang', 'university of muhammadiyah malang',
            'kampus umm', 'alumni umm', 'lulusan umm'
        ]
        self.prodi_aliases = {
            'akuntansi': ['accounting', 'accountant', 'akuntan', 'finance', 'auditor'],
            'manajemen': ['management', 'manager', 'business', 'marketing', 'mba'],
            'informatika': ['informatics', 'computer science', 'programming', 'software', 'developer', 'it'],
            'sistem informasi': ['information system', 'system analyst', 'business analyst'],
            'teknik': ['engineering', 'engineer'],
            'hukum': ['law', 'legal', 'lawyer', 'attorney'],
            'psikologi': ['psychology', 'psychologist', 'hr', 'human resources'],
            'komunikasi': ['communication', 'journalism', 'media', 'pr'],
            'ekonomi': ['economics', 'economist', 'finance', 'banking'],
        }
    
    def calculate_confidence(
        self, 
        nama: str, 
        prodi: str, 
        serper_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate confidence score based on Serper search results
        
        Args:
            nama: Nama alumni yang dicari
            prodi: Program studi alumni
            serper_results: List hasil pencarian dari search_engine
            
        Returns:
            Dictionary dengan skor, status, dan detail analisis
        """
        if not serper_results:
            return {
                'confidence_score': 0,
                'status': 'Tidak Cocok',
                'matched_result': None,
                'analysis': 'Tidak ada hasil pencarian ditemukan'
            }
        
        best_score = 0
        best_result = None
        all_scores = []
        
        for result_group in serper_results:
            query = result_group.get('query', '')
            extracted_results = result_group.get('extracted_results', [])
            
            for result in extracted_results:
                score, analysis = self._score_single_result(nama, prodi, result)
                
                scored_result = {
                    'query': query,
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'link': result.get('link', ''),
                    'score': score,
                    'analysis': analysis
                }
                
                all_scores.append(scored_result)
                
                if score > best_score:
                    best_score = score
                    best_result = scored_result
        
        # Sort by score descending
        all_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # Determine status with new thresholds
        if best_score >= self.THRESHOLD_STRONG:
            status = 'Teridentifikasi Kuat'
        elif best_score >= self.THRESHOLD_VERIFY:
            status = 'Perlu Verifikasi'
        elif best_score >= self.THRESHOLD_WEAK:
            status = 'Tidak Ditemukan'
        else:
            status = 'Tidak Ditemukan'
        
        return {
            'confidence_score': best_score,
            'status': status,
            'matched_result': best_result,
            'all_scored_results': all_scores[:5],  # Top 5 results
            'analysis': self._generate_analysis(best_score, best_result)
        }
    
    def _score_single_result(
        self, 
        nama: str, 
        prodi: str, 
        result: Dict[str, str]
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Score a single search result
        
        Returns:
            Tuple of (score, analysis_dict)
        """
        score = 0
        analysis = {
            'name_match': False,
            'umm_mention': False,
            'prodi_keyword': False,
            'details': []
        }
        
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        combined_text = f"{title} {snippet}".lower()
        
        # 1. Name match scoring with tiered approach
        name_score_title = fuzz.partial_ratio(nama.lower(), title.lower())
        name_score_snippet = fuzz.partial_ratio(nama.lower(), snippet.lower())
        name_score_full_title = fuzz.ratio(nama.lower(), title.lower())
        name_score = max(name_score_title, name_score_snippet, name_score_full_title)
        
        # High confidence name match (>80%)
        if name_score >= 80:
            score += self.SCORE_NAME_MATCH_HIGH
            analysis['name_match'] = True
            analysis['name_confidence'] = 'high'
            analysis['details'].append(f'✓ Nama match kuat: {name_score}%')
        # Medium confidence (60-79%)
        elif name_score >= 60:
            score += self.SCORE_NAME_MATCH_MEDIUM
            analysis['name_match'] = True
            analysis['name_confidence'] = 'medium'
            analysis['details'].append(f'~ Nama match medium: {name_score}%')
        # Low confidence (40-59%)
        elif name_score >= 40:
            score += self.SCORE_NAME_MATCH_LOW
            analysis['name_confidence'] = 'low'
            analysis['details'].append(f'? Nama match lemah: {name_score}%')
        
        # 2. UMM mention scoring
        umm_found = any(keyword in combined_text for keyword in self.umm_keywords)
        if umm_found:
            score += self.SCORE_UMM_MENTION
            analysis['umm_mention'] = True
            analysis['details'].append('UMM/Universitas Muhammadiyah Malang ditemukan')
        
        # 3. Prodi/Career keyword scoring
        prodi_keywords = self._extract_prodi_keywords(prodi)
        keyword_matches = []
        
        for keyword in prodi_keywords:
            if keyword.lower() in combined_text:
                keyword_matches.append(keyword)
        
        if keyword_matches:
            score += self.SCORE_PRODI_KEYWORD
            analysis['prodi_keyword'] = True
            analysis['details'].append(f'Keyword prodi: {", ".join(keyword_matches)}')
        
            # Platform-specific bonuses
        link = result.get('link', '').lower()
        
        if 'linkedin.com' in link:
            score += 15
            analysis['details'].append('LinkedIn profile (+15) - Professional')
        elif 'instagram.com' in link:
            score += 8
            analysis['details'].append('Instagram profile (+8)')
        elif 'facebook.com' in link or 'fb.com' in link:
            score += 5
            analysis['details'].append('Facebook profile (+5)')
        elif 'twitter.com' in link or 'x.com' in link:
            score += 5
            analysis['details'].append('Twitter/X profile (+5)')
        elif 'tiktok.com' in link:
            score += 3
            analysis['details'].append('TikTok profile (+3)')
        elif 'about.me' in link:
            score += 10
            analysis['details'].append('About.me page (+10) - Contains contact info')
        elif 'github.com' in link:
            score += 8
            analysis['details'].append('GitHub profile (+8) - Developer')
        
        # Contact info detection (email/phone in snippet)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_patterns = [
            r'\+62[\s\d-]{8,13}',  # Indonesia format
            r'08[\d\s-]{9,12}',     # Mobile format
            r'\(\d{2,4}\)[\s\d-]{6,12}',  # Area code format
        ]
        
        snippet_text = result.get('snippet', '')
        if re.search(email_pattern, snippet_text):
            score += 5
            analysis['details'].append('Email detected in snippet (+5)')
        
        for pattern in phone_patterns:
            if re.search(pattern, snippet_text):
                score += 5
                analysis['details'].append('Phone number detected in snippet (+5)')
                break
        
        return score, analysis
    
    def _extract_prodi_keywords(self, prodi: str) -> List[str]:
        """Extract relevant keywords from program studi"""
        prodi_lower = prodi.lower()
        keywords = [prodi_lower]
        
        # Add common variations
        keyword_map = {
            'akuntansi': ['accountant', 'akuntan', 'accounting', 'finance', 'auditor', 'tax'],
            'manajemen': ['manager', 'management', 'business', 'marketing', 'operations'],
            'ekonomi': ['economist', 'economic', 'finance', 'banking', 'investment'],
            'informatika': ['programmer', 'developer', 'software', 'IT', 'technology', 'data'],
            'sistem informasi': ['system analyst', 'IT consultant', 'business analyst'],
            'teknik': ['engineer', 'engineering', 'technical'],
            'teknik industri': ['industrial engineer', 'supply chain', 'operations'],
            'teknik mesin': ['mechanical engineer', 'mechanical'],
            'teknik elektro': ['electrical engineer', 'electronic'],
            'teknik sipil': ['civil engineer', 'construction'],
            'hukum': ['lawyer', 'attorney', 'legal', 'law', 'advocate'],
            'kedokteran': ['doctor', 'physician', 'medical', 'health'],
            'psikologi': ['psychologist', 'psychology', 'HR', 'counselor'],
            'komunikasi': ['communication', 'PR', 'media', 'journalist', 'broadcasting'],
            'pendidikan': ['teacher', 'education', 'lecturer', 'academic'],
        }
        
        for key, related in keyword_map.items():
            if key in prodi_lower:
                keywords.extend(related)
                break
        
        return keywords
    
    def _generate_analysis(self, score: int, result: Dict[str, Any]) -> str:
        """Generate human-readable analysis"""
        if not result:
            return "Tidak ada hasil yang cocok ditemukan"
        
        analysis_parts = []
        
        if score >= self.THRESHOLD_STRONG:
            analysis_parts.append(f"✓ Skor tinggi ({score}/100): Profil alumni teridentifikasi dengan kuat")
        elif score >= self.THRESHOLD_VERIFY:
            analysis_parts.append(f"~ Skor menengah ({score}/100): Perlu verifikasi manual")
        elif score >= self.THRESHOLD_WEAK:
            analysis_parts.append(f"? Skor rendah ({score}/100): Match lemah, butuh verifikasi")
        else:
            analysis_parts.append(f"✗ Skor sangat rendah ({score}/100): Profil tidak ditemukan")
        
        if result.get('analysis', {}).get('details'):
            analysis_parts.append("Faktor: " + "; ".join(result['analysis']['details'][:3]))
        
        return " | ".join(analysis_parts)
    
    def extract_profile_data(self, result: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract profile data from best matching result across all platforms
        
        Args:
            result: Best scored result
            
        Returns:
            Dictionary with extracted profile fields
        """
        if not result:
            return {}
        
        profile = {
            'linkedin': '',
            'instagram': '',
            'facebook': '',
            'twitter_x': '',
            'tiktok': '',
            'website_personal': '',
            'email': '',
            'no_hp': '',
            'tempat_kerja': '',
            'alamat_kerja': '',
            'posisi': '',
            'kategori': '',
            'sosmed_kantor': ''
        }
        
        link = result.get('link', '')
        title = result.get('title', '')
        snippet = result.get('snippet', '')
        
        # === EXTRACT SOCIAL MEDIA LINKS ===
        if 'linkedin.com' in link.lower():
            profile['linkedin'] = link
            # Extract from LinkedIn
            profile.update(self._extract_linkedin_data(title, snippet))
            
        elif 'instagram.com' in link.lower():
            profile['instagram'] = link
            
        elif 'facebook.com' in link.lower() or 'fb.com' in link.lower():
            profile['facebook'] = link
            
        elif 'twitter.com' in link.lower() or 'x.com' in link.lower():
            profile['twitter_x'] = link
            
        elif 'tiktok.com' in link.lower():
            profile['tiktok'] = link
            
        elif 'about.me' in link.lower():
            profile['website_personal'] = link
            # About.me often has contact info
            profile.update(self._extract_contact_from_snippet(snippet))
            
        elif 'github.com' in link.lower():
            profile['website_personal'] = link
            if not profile['kategori']:
                profile['kategori'] = 'Teknik/Teknologi'
        
        # === EXTRACT CONTACT INFO FROM SNIPPET ===
        contact_data = self._extract_contact_from_snippet(snippet)
        if contact_data.get('email') and not profile['email']:
            profile['email'] = contact_data['email']
        if contact_data.get('no_hp') and not profile['no_hp']:
            profile['no_hp'] = contact_data['no_hp']
        
        # === EXTRACT WORK INFO FROM ANY PLATFORM ===
        if not profile['tempat_kerja']:
            profile.update(self._extract_work_info(title, snippet))
        
        # === DETERMINE KATEGORI ===
        if not profile['kategori']:
            profile['kategori'] = self._infer_kategori(profile['posisi'], profile['tempat_kerja'])
        
        return profile
    
    def extract_data_from_all_results(self, all_scored_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Extract profile data by aggregating from ALL search results
        This catches data that might be in lower-ranked results
        
        Args:
            all_scored_results: List of all scored results from search
            
        Returns:
            Dictionary with merged profile fields from all sources
        """
        merged_profile = {
            'linkedin': '',
            'instagram': '',
            'facebook': '',
            'twitter_x': '',
            'tiktok': '',
            'website_personal': '',
            'email': '',
            'no_hp': '',
            'tempat_kerja': '',
            'alamat_kerja': '',
            'posisi': '',
            'kategori': '',
            'sosmed_kantor': ''
        }
        
        # Collect data from all results (even lower scored ones might have useful info)
        for result in all_scored_results:
            # Skip very low scores (< 20)
            if result.get('score', 0) < 20:
                continue
                
            single_profile = self.extract_profile_data(result)
            
            # Merge data - prefer non-empty values
            for key in merged_profile:
                if single_profile.get(key) and not merged_profile[key]:
                    merged_profile[key] = single_profile[key]
        
        return merged_profile
    
    def _extract_linkedin_data(self, title: str, snippet: str) -> Dict[str, str]:
        """Extract work data from LinkedIn title/snippet with improved patterns"""
        data = {'tempat_kerja': '', 'posisi': ''}
        
        # Clean title for processing
        clean_title = title.replace(' | LinkedIn', '').replace(' | linkedin', '').strip()
        
        # Pattern 1: "Name - Position - Company" (most common)
        if ' - ' in clean_title:
            parts = clean_title.split(' - ')
            if len(parts) >= 2:
                data['posisi'] = parts[1].strip()
            if len(parts) >= 3:
                data['tempat_kerja'] = parts[2].strip()
            return data
        
        # Pattern 2: "Name at Company" or "Name @ Company"
        for sep in [' at ', ' @ ', ' di ', ' - ', ' – ']:
            if sep in clean_title.lower():
                parts = clean_title.split(sep)
                if len(parts) >= 2:
                    company_part = parts[1].strip()
                    # Remove common suffixes
                    for suffix in [' | LinkedIn', ' - LinkedIn', ' | Profile', ' - Profile']:
                        company_part = company_part.split(suffix)[0].strip()
                    data['tempat_kerja'] = company_part
                    break
        
        # Pattern 3: Look for job title keywords in title
        job_titles = ['Manager', 'Director', 'Supervisor', 'Officer', 'Specialist',
                     'Engineer', 'Developer', 'Analyst', 'Consultant', 'Accountant',
                     'Executive', 'Coordinator', 'Head', 'Lead', 'Senior', 'Junior',
                     'Staff', 'Admin', 'Marketing', 'Sales', 'HR', 'IT', 'Finance']
        
        for job in job_titles:
            if job.lower() in clean_title.lower():
                # Try to extract full job title
                pattern = re.compile(rf'\b{job}\w*\b', re.IGNORECASE)
                match = pattern.search(clean_title)
                if match:
                    # Get surrounding context (e.g., "Senior Developer")
                    start = max(0, match.start() - 10)
                    end = min(len(clean_title), match.end() + 20)
                    context = clean_title[start:end]
                    # Clean up
                    data['posisi'] = context.strip(' -|@')
                    break
        
        return data
    
    def _extract_contact_from_snippet(self, snippet: str) -> Dict[str, str]:
        """Extract email and phone from snippet text"""
        data = {'email': '', 'no_hp': ''}
        
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_match = re.search(email_pattern, snippet)
        if email_match:
            data['email'] = email_match.group(0)
        
        # Phone patterns (Indonesia focus)
        phone_patterns = [
            (r'\+62[\s\d-]{8,13}', 'international'),
            (r'08[\d\s-]{9,12}', 'mobile'),
        ]
        
        for pattern, ptype in phone_patterns:
            match = re.search(pattern, snippet)
            if match:
                data['no_hp'] = match.group(0).replace(' ', '').replace('-', '')
                break
        
        return data
    
    def _extract_work_info(self, title: str, snippet: str) -> Dict[str, str]:
        """Extract work info from any platform with improved patterns"""
        data = {'tempat_kerja': '', 'posisi': '', 'alamat_kerja': ''}
        combined = f"{title} {snippet}"
        combined_lower = combined.lower()
        
        # Expanded job title list with common Indonesian/English titles
        job_indicators = [
            'manager', 'director', 'supervisor', 'officer', 'specialist', 
            'engineer', 'developer', 'analyst', 'consultant', 'accountant',
            'teacher', 'lecturer', 'doctor', 'nurse', 'lawyer', 'executive',
            'coordinator', 'head', 'lead', 'senior', 'junior', 'staff',
            'admin', 'marketing', 'sales', 'hr', 'it', 'finance', 'accounting',
            'operations', 'project', 'product', 'business', 'data', 'software',
            'network', 'system', 'web', 'frontend', 'backend', 'fullstack',
            'manajer', 'direktur', 'staf', 'guru', 'dosen', 'dokter', 'perawat',
            'pengacara', 'akuntan', 'marketing', 'penjualan', 'operasional'
        ]
        
        # Pattern 1: "Job Title at Company" or "Job Title @ Company"
        for job in job_indicators:
            if job in combined_lower:
                # Pattern: Job at Company
                at_patterns = [
                    rf'\b{job}\w*\s+(?:at|@|di)\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[\|\-\–\,]|\s+on\s+|\s+in\s+|\s+and\s+|\s+\(|$)',
                    rf'\b{job}\w*\s+(?:at|@|di)\s+([A-Z][A-Za-z0-9\s&.,]+)',
                ]
                for pattern in at_patterns:
                    match = re.search(pattern, combined, re.IGNORECASE)
                    if match:
                        data['posisi'] = job.title()
                        company = match.group(1).strip()
                        # Clean up company name
                        company = re.sub(r'\s+(?:LinkedIn|Facebook|Instagram|Twitter|Profile|\d{4}).*$', '', company, flags=re.IGNORECASE)
                        data['tempat_kerja'] = company
                        break
                
                if data['tempat_kerja']:
                    break
                
                # Pattern 2: Just get the job title if no company found
                if not data['posisi']:
                    data['posisi'] = job.title()
        
        # Pattern 3: Look for company indicators in snippet
        company_indicators = ['company', 'perusahaan', 'kantor', 'instansi', 'universitas', 'bank']
        for indicator in company_indicators:
            if indicator in combined_lower and not data['tempat_kerja']:
                # Try to find company name near indicator
                pattern = rf'{indicator}\s*:?\s*([A-Z][A-Za-z0-9\s&.,]+?)(?:\s*[\.,]|$)'
                match = re.search(pattern, combined, re.IGNORECASE)
                if match:
                    data['tempat_kerja'] = match.group(1).strip()
                    break
        
        return data
    
    def _infer_kategori(self, posisi: str, tempat_kerja: str) -> str:
        """Infer job category from position and company"""
        posisi_lower = posisi.lower()
        company_lower = tempat_kerja.lower()
        
        if any(word in posisi_lower for word in ['manager', 'director', 'head', 'lead', 'chief', 'supervisor']):
            return 'Manajemen'
        elif any(word in posisi_lower for word in ['developer', 'programmer', 'engineer', 'analyst', 'IT', 'data']):
            return 'Teknik/Teknologi'
        elif any(word in posisi_lower for word in ['consultant', 'advisor', 'specialist']):
            return 'Konsultan'
        elif any(word in posisi_lower for word in ['teacher', 'lecturer', 'dosen', 'guru', 'academic']):
            return 'Akademisi'
        elif any(word in company_lower for word in ['university', 'universitas', 'sekolah', 'institute', 'academy']):
            return 'Akademisi'
        elif any(word in posisi_lower for word in ['doctor', 'physician', 'medical', 'nurse']):
            return 'Kesehatan'
        elif any(word in posisi_lower for word in ['lawyer', 'attorney', 'advocate', 'legal']):
            return 'Hukum'
        elif any(word in posisi_lower for word in ['accountant', 'finance', 'accounting', 'auditor']):
            return 'Akuntansi/Keuangan'
        elif tempat_kerja:
            return 'Industri/Swasta'
        
        return ''
