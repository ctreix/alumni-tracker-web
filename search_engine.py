import requests
import os
from typing import List, Dict, Any, Optional
from urllib.parse import quote


class SerperSearchEngine:
    """Search Engine Integration using Serper.dev API"""
    
    API_URL = "https://google.serper.dev/search"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper Search Engine
        
        Args:
            api_key: Serper.dev API key. If not provided, reads from SERPER_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get('SERPER_API_KEY')
        if not self.api_key:
            raise ValueError("Serper API key is required. Set SERPER_API_KEY environment variable.")
    
    def generate_queries(self, nama: str, prodi: str, platform: str = 'all') -> List[str]:
        """
        Generate dorking queries for alumni search across multiple platforms
        
        Args:
            nama: Nama alumni
            prodi: Program studi alumni
            platform: 'all', 'linkedin', 'instagram', 'facebook', 'twitter', 'tiktok', 'email', 'web'
            
        Returns:
            List of search queries
        """
        queries = []
        
        # === LINKEDIN QUERIES (Professional Profile) ===
        if platform in ['all', 'linkedin']:
            queries.append(f'site:linkedin.com/in "{nama}" "Universitas Muhammadiyah Malang" OR "UMM"')
            queries.append(f'site:linkedin.com/in "{nama}" "{prodi}"')
            queries.append(f'"{nama}" "Universitas Muhammadiyah Malang" OR "UMM" linkedin')
        
        # === INSTAGRAM QUERIES (Profile only: instagram.com/username) ===
        if platform in ['all', 'instagram']:
            queries.append(f'site:instagram.com "{nama}" "Universitas Muhammadiyah Malang" OR "UMM"')
            queries.append(f'"{nama}" site:instagram.com inurl:/ alumni UMM')
        
        # === FACEBOOK QUERIES (Profile only: facebook.com/username) ===
        if platform in ['all', 'facebook']:
            queries.append(f'site:facebook.com "{nama}" "Universitas Muhammadiyah Malang" UMM alumni')
            queries.append(f'site:facebook.com "{nama}" UMM "{prodi}"')
        
        # === TWITTER/X QUERIES (Profile only: twitter.com/username or x.com/username) ===
        if platform in ['all', 'twitter']:
            queries.append(f'site:twitter.com OR site:x.com "{nama}" "Universitas Muhammadiyah Malang" alumni')
            queries.append(f'inurl:twitter.com "{nama}" UMM "{prodi}"')
        
        # === TIKTOK QUERIES ===
        if platform in ['all', 'tiktok']:
            queries.append(f'site:tiktok.com/@ "{nama}" UMM')
            queries.append(f'site:tiktok.com "{nama}" alumni Muhammadiyah Malang')
        
        # === EMAIL & CONTACT QUERIES ===
        if platform in ['all', 'email']:
            queries.append(f'"{nama}" "{prodi}" email contact UMM')
            queries.append(f'site:about.me "{nama}" UMM')
            queries.append(f'"{nama}" inurl:contact UMM alumni')
        
        # === PERSONAL WEBSITE/PORTFOLIO ===
        if platform in ['all', 'web']:
            queries.append(f'"{nama}" "{prodi}" portfolio OR cv OR resume UMM')
            queries.append(f'"{nama}" site:github.com UMM')
            queries.append(f'"{nama}" site:gitlab.com OR site:bitbucket.org')
        
        # === GENERAL ALUMNI SEARCH ===
        if platform in ['all']:
            career_keywords = self._get_career_keywords(prodi)
            for keyword in career_keywords[:2]:
                queries.append(f'"{nama}" "{prodi}" "{keyword}"')
            queries.append(f'alumni UMM "{nama}" "{prodi}"')
        
        return queries
    
    def _get_career_keywords(self, prodi: str) -> List[str]:
        """Get career keywords related to program studi"""
        prodi_lower = prodi.lower()
        
        keyword_map = {
            'akuntansi': ['accountant', 'akuntan', 'finance', 'keuangan', 'auditor'],
            'manajemen': ['manager', 'management', 'business', 'bisnis', 'marketing'],
            'ekonomi': ['economist', 'economic', 'finance', 'banking', 'perbankan'],
            'informatika': ['programmer', 'developer', 'software', 'IT', 'teknologi'],
            'teknik': ['engineer', 'engineering', 'technical', 'teknik'],
            'hukum': ['lawyer', 'attorney', 'legal', 'advokat', 'hukum'],
            'kedokteran': ['doctor', 'medical', 'physician', 'dokter', 'kesehatan'],
            'psikologi': ['psychologist', 'HR', 'human resources', 'psikolog'],
            'komunikasi': ['communication', 'PR', 'public relations', 'media', 'journalist'],
            'pendidikan': ['teacher', 'education', 'lecturer', 'guru', 'dosen'],
        }
        
        for key, keywords in keyword_map.items():
            if key in prodi_lower:
                return keywords
        
        return ['professional', 'karir', 'pekerjaan']
    
    def fetch_serper_data(self, query: str) -> Dict[str, Any]:
        """
        Fetch search data from Serper.dev API
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary containing search results with title, snippet, and link
        """
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'q': query,
            'num': 10  # Number of results
        }
        
        try:
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': True,
                'message': str(e),
                'organic': []
            }
    
    def extract_results(self, serper_response: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract relevant fields from Serper response
        
        Args:
            serper_response: Raw JSON response from Serper API
            
        Returns:
            List of dictionaries with title, snippet, and link
        """
        results = []
        
        if 'error' in serper_response:
            return results
        
        # Extract organic results
        organic_results = serper_response.get('organic', [])
        
        for result in organic_results:
            extracted = {
                'title': result.get('title', ''),
                'snippet': result.get('snippet', ''),
                'link': result.get('link', ''),
                'position': result.get('position', 0)
            }
            results.append(extracted)
        
        # Also check knowledge graph if available
        knowledge_graph = serper_response.get('knowledgeGraph', {})
        if knowledge_graph:
            kg_result = {
                'title': knowledge_graph.get('title', ''),
                'snippet': knowledge_graph.get('description', ''),
                'link': knowledge_graph.get('website', ''),
                'position': 0,
                'type': 'knowledge_graph'
            }
            if kg_result['title'] or kg_result['snippet']:
                results.append(kg_result)
        
        return results
    
    def search_alumni(self, nama: str, prodi: str, platform: str = 'all') -> Dict[str, Any]:
        """
        Full search pipeline for alumni across multiple platforms
        
        Args:
            nama: Nama alumni
            prodi: Program studi
            platform: 'all' or specific platform
            
        Returns:
            Dictionary with all search results and metadata
        """
        queries = self.generate_queries(nama, prodi, platform)
        all_results = []
        
        for query in queries:
            response = self.fetch_serper_data(query)
            results = self.extract_results(response)
            
            # Detect platform from query
            detected_platform = 'general'
            if 'linkedin.com' in query:
                detected_platform = 'linkedin'
            elif 'instagram.com' in query:
                detected_platform = 'instagram'
            elif 'facebook.com' in query or 'fb.com' in query:
                detected_platform = 'facebook'
            elif 'twitter.com' in query or 'x.com' in query:
                detected_platform = 'twitter'
            elif 'tiktok.com' in query:
                detected_platform = 'tiktok'
            elif 'about.me' in query or 'email' in query:
                detected_platform = 'email'
            elif 'github.com' in query or 'portfolio' in query:
                detected_platform = 'website'
            
            all_results.append({
                'query': query,
                'platform': detected_platform,
                'raw_response': response,
                'extracted_results': results,
                'result_count': len(results)
            })
        
        return {
            'nama': nama,
            'prodi': prodi,
            'queries_used': queries,
            'search_results': all_results,
            'total_results': sum(r['result_count'] for r in all_results),
            'platforms_searched': list(set(r['platform'] for r in all_results))
        }
