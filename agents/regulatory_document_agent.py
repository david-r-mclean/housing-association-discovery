"""
Regulatory Document Discovery Agent
Discovers, downloads, and analyzes government and regulatory documentation
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from urllib.parse import urljoin, urlparse
import hashlib
import mimetypes

from vertex_agents.real_vertex_agent import ProductionVertexAIAgent

logger = logging.getLogger(__name__)

class RegulatoryDocumentAgent:
    """Agent for discovering and analyzing regulatory documents"""
    
    def __init__(self):
        self.vertex_ai = ProductionVertexAIAgent()
        self.session = None
        self.discovered_documents = []
        self.processed_documents = []
        
        # Government and regulatory domains by country
        self.regulatory_domains = {
            'uk': [
                'gov.uk',
                'legislation.gov.uk',
                'parliament.uk',
                'fca.org.uk',
                'cqc.org.uk',
                'ofsted.gov.uk',
                'scottishhousinregulator.gov.uk',
                'charitycommission.gov.uk',
                'oscr.org.uk',
                'hse.gov.uk',
                'environment-agency.gov.uk',
                'naturalengland.org.uk',
                'sepa.org.uk',
                'nhsengland.nhs.uk',
                'nice.org.uk'
            ],
            'eu': [
                'europa.eu',
                'eur-lex.europa.eu',
                'europarl.europa.eu',
                'consilium.europa.eu',
                'ema.europa.eu',
                'eiopa.europa.eu',
                'esma.europa.eu'
            ],
            'us': [
                'sec.gov',
                'cdc.gov',
                'fda.gov',
                'epa.gov',
                'hud.gov',
                'cms.gov',
                'treasury.gov',
                'federalregister.gov'
            ]
        }
        
        # Document type patterns
        self.document_patterns = {
            'legislation': [
                r'act\s+\d{4}',
                r'regulation\s+\d+',
                r'statutory\s+instrument',
                r'directive\s+\d+',
                r'law\s+\d+'
            ],
            'guidance': [
                r'guidance',
                r'guidelines',
                r'best\s+practice',
                r'code\s+of\s+practice',
                r'handbook'
            ],
            'policy': [
                r'policy',
                r'strategy',
                r'framework',
                r'white\s+paper',
                r'green\s+paper'
            ],
            'standards': [
                r'standard',
                r'specification',
                r'technical\s+requirements',
                r'compliance\s+requirements'
            ],
            'reports': [
                r'annual\s+report',
                r'inspection\s+report',
                r'review',
                r'assessment',
                r'evaluation'
            ]
        }
        
        logger.info("Regulatory Document Agent initialized")
    
    async def discover_regulatory_documents(self, 
                                          industry: str,
                                          document_types: List[str] = None,
                                          regions: List[str] = None,
                                          date_range: Tuple[datetime, datetime] = None,
                                          keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        Discover regulatory documents for a specific industry
        """
        
        logger.info(f"Starting regulatory document discovery for {industry}")
        
        if document_types is None:
            document_types = ['legislation', 'guidance', 'policy', 'standards', 'reports']
        
        if regions is None:
            regions = ['uk']
        
        if keywords is None:
            keywords = [industry]
        
        # Create search terms combining industry and document types
        search_terms = self._generate_search_terms(industry, document_types, keywords)
        
        # Initialize session
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        try:
            discovered_docs = []
            
            # Search each region
            for region in regions:
                region_docs = await self._search_region_documents(
                    region, search_terms, document_types, date_range
                )
                discovered_docs.extend(region_docs)
            
            # Deduplicate documents
            unique_docs = self._deduplicate_documents(discovered_docs)
            
            # Analyze and categorize documents with AI
            analyzed_docs = await self._analyze_documents_with_ai(unique_docs, industry)
            
            self.discovered_documents = analyzed_docs
            
            logger.info(f"Discovered {len(analyzed_docs)} regulatory documents for {industry}")
            
            return analyzed_docs
            
        finally:
            if self.session:
                await self.session.close()
    
    def _generate_search_terms(self, industry: str, document_types: List[str], keywords: List[str]) -> List[str]:
        """Generate comprehensive search terms"""
        
        search_terms = []
        
        # Base industry terms
        base_terms = [industry] + keywords
        
        # Combine with document types
        for base_term in base_terms:
            for doc_type in document_types:
                search_terms.append(f"{base_term} {doc_type}")
                search_terms.append(f"{doc_type} {base_term}")
        
        # Add regulatory-specific terms
        regulatory_terms = [
            'regulation', 'compliance', 'requirements', 'standards',
            'guidance', 'policy', 'legislation', 'act', 'directive'
        ]
        
        for base_term in base_terms:
            for reg_term in regulatory_terms:
                search_terms.append(f"{base_term} {reg_term}")
        
        # Remove duplicates and return
        return list(set(search_terms))
    
    async def _search_region_documents(self, 
                                     region: str, 
                                     search_terms: List[str], 
                                     document_types: List[str],
                                     date_range: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """Search for documents in a specific region"""
        
        documents = []
        domains = self.regulatory_domains.get(region, [])
        
        for domain in domains:
            try:
                domain_docs = await self._search_domain(domain, search_terms, document_types, date_range)
                documents.extend(domain_docs)
                
                # Respectful delay between domains
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error searching domain {domain}: {e}")
                continue
        
        return documents
    
    async def _search_domain(self, 
                           domain: str, 
                           search_terms: List[str], 
                           document_types: List[str],
                           date_range: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """Search a specific domain for documents"""
        
        documents = []
        
        # Try different search approaches based on domain
        if 'gov.uk' in domain:
            documents.extend(await self._search_gov_uk(domain, search_terms, date_range))
        elif 'legislation.gov.uk' in domain:
            documents.extend(await self._search_legislation_gov_uk(search_terms, date_range))
        elif 'europa.eu' in domain:
            documents.extend(await self._search_europa_eu(search_terms, date_range))
        else:
            # Generic search approach
            documents.extend(await self._generic_domain_search(domain, search_terms, date_range))
        
        return documents
    
    async def _search_gov_uk(self, domain: str, search_terms: List[str], date_range: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """Search gov.uk sites"""
        
        documents = []
        
        for search_term in search_terms[:10]:  # Limit to avoid overwhelming
            try:
                # Use gov.uk search API if available, otherwise scrape
                search_url = f"https://{domain}/search?q={search_term.replace(' ', '+')}"
                
                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract search results
                        results = soup.find_all(['a', 'h3'], class_=re.compile(r'result|search|title'))
                        
                        for result in results[:20]:  # Limit results per search
                            doc_info = await self._extract_document_info(result, domain, search_term)
                            if doc_info:
                                documents.append(doc_info)
                
                await asyncio.sleep(1)  # Respectful delay
                
            except Exception as e:
                logger.error(f"Error searching {domain} for '{search_term}': {e}")
                continue
        
        return documents
    
    async def _search_legislation_gov_uk(self, search_terms: List[str], date_range: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """Search UK legislation site"""
        
        documents = []
        base_url = "https://www.legislation.gov.uk"
        
        for search_term in search_terms[:5]:
            try:
                # Use legislation.gov.uk search
                search_url = f"{base_url}/search?text={search_term.replace(' ', '+')}"
                
                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract legislation results
                        results = soup.find_all('div', class_='searchResult')
                        
                        for result in results[:15]:
                            doc_info = await self._extract_legislation_info(result, base_url, search_term)
                            if doc_info:
                                documents.append(doc_info)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error searching legislation.gov.uk for '{search_term}': {e}")
                continue
        
        return documents
    
    async def _search_europa_eu(self, search_terms: List[str], date_range: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """Search EU documentation"""
        
        documents = []
        base_url = "https://eur-lex.europa.eu"
        
        for search_term in search_terms[:5]:
            try:
                # Use EUR-Lex search
                search_url = f"{base_url}/search.html?qid=&text={search_term.replace(' ', '+')}&scope=EURLEX&type=quick&lang=en"
                
                async with self.session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract EU document results
                        results = soup.find_all('div', class_='SearchResult')
                        
                        for result in results[:10]:
                            doc_info = await self._extract_eu_document_info(result, base_url, search_term)
                            if doc_info:
                                documents.append(doc_info)
                
                await asyncio.sleep(2)  # EU sites may be more restrictive
                
            except Exception as e:
                logger.error(f"Error searching EUR-Lex for '{search_term}': {e}")
                continue
        
        return documents
    
    async def _generic_domain_search(self, domain: str, search_terms: List[str], date_range: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """Generic search approach for any domain"""
        
        documents = []
        
        for search_term in search_terms[:5]:
            try:
                # Try common search patterns
                search_patterns = [
                    f"https://{domain}/search?q={search_term.replace(' ', '+')}",
                    f"https://{domain}/search?query={search_term.replace(' ', '+')}",
                    f"https://{domain}/?s={search_term.replace(' ', '+')}"
                ]
                
                for search_url in search_patterns:
                    try:
                        async with self.session.get(search_url) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Look for common result patterns
                                results = soup.find_all(['a', 'div', 'article'], 
                                                      class_=re.compile(r'result|search|document|publication'))
                                
                                for result in results[:10]:
                                    doc_info = await self._extract_generic_document_info(result, domain, search_term)
                                    if doc_info:
                                        documents.append(doc_info)
                                
                                break  # Success, don't try other patterns
                                
                    except Exception as e:
                        continue  # Try next pattern
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in generic search of {domain} for '{search_term}': {e}")
                continue
        
        return documents
    
    async def _extract_document_info(self, element, domain: str, search_term: str) -> Optional[Dict[str, Any]]:
        """Extract document information from HTML element"""
        
        try:
            # Find link
            link = element.find('a') if element.name != 'a' else element
            if not link or not link.get('href'):
                return None
            
            url = urljoin(f"https://{domain}", link.get('href'))
            title = link.get_text(strip=True) or link.get('title', '')
            
            if not title or len(title) < 10:
                return None
            
            # Extract additional info
            description = ""
            parent = element.parent
            if parent:
                desc_elem = parent.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt'))
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
            
            # Determine document type
            doc_type = self._classify_document_type(title, description, url)
            
            return {
                'title': title,
                'url': url,
                'description': description,
                'domain': domain,
                'document_type': doc_type,
                'search_term': search_term,
                'discovered_at': datetime.now().isoformat(),
                'file_type': self._get_file_type_from_url(url),
                'relevance_score': self._calculate_relevance_score(title, description, search_term)
            }
            
        except Exception as e:
            logger.error(f"Error extracting document info: {e}")
            return None
    
    async def _extract_legislation_info(self, element, base_url: str, search_term: str) -> Optional[Dict[str, Any]]:
        """Extract UK legislation information"""
        
        try:
            title_elem = element.find(['h3', 'h4', 'a'])
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            link = title_elem.find('a') or title_elem
            
            if not link.get('href'):
                return None
            
            url = urljoin(base_url, link.get('href'))
            
            # Extract metadata
            metadata = {}
            meta_elems = element.find_all(['span', 'div'], class_=re.compile(r'meta|date|type'))
            for meta in meta_elems:
                text = meta.get_text(strip=True)
                if re.search(r'\d{4}', text):  # Year
                    metadata['year'] = re.search(r'\d{4}', text).group()
                if 'act' in text.lower():
                    metadata['legislation_type'] = 'Act'
                elif 'regulation' in text.lower():
                    metadata['legislation_type'] = 'Regulation'
            
            return {
                'title': title,
                'url': url,
                'description': '',
                'domain': 'legislation.gov.uk',
                'document_type': 'legislation',
                'search_term': search_term,
                'discovered_at': datetime.now().isoformat(),
                'file_type': 'html',
                'metadata': metadata,
                'relevance_score': self._calculate_relevance_score(title, '', search_term)
            }
            
        except Exception as e:
            logger.error(f"Error extracting legislation info: {e}")
            return None
    
    async def _extract_eu_document_info(self, element, base_url: str, search_term: str) -> Optional[Dict[str, Any]]:
        """Extract EU document information"""
        
        try:
            title_elem = element.find(['h3', 'h4', 'a'])
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            link = title_elem.find('a') or title_elem
            
            if not link.get('href'):
                return None
            
            url = urljoin(base_url, link.get('href'))
            
            # Extract EU-specific metadata
            metadata = {}
            celex_elem = element.find(text=re.compile(r'CELEX'))
            if celex_elem:
                metadata['celex_number'] = celex_elem.strip()
            
            return {
                'title': title,
                'url': url,
                'description': '',
                'domain': 'europa.eu',
                'document_type': 'eu_legislation',
                'search_term': search_term,
                'discovered_at': datetime.now().isoformat(),
                'file_type': 'html',
                'metadata': metadata,
                'relevance_score': self._calculate_relevance_score(title, '', search_term)
            }
            
        except Exception as e:
            logger.error(f"Error extracting EU document info: {e}")
            return None
    
    async def _extract_generic_document_info(self, element, domain: str, search_term: str) -> Optional[Dict[str, Any]]:
        """Extract generic document information"""
        
        try:
            # Find title and link
            if element.name == 'a':
                link = element
                title = element.get_text(strip=True)
            else:
                link = element.find('a')
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5']) or link
                title = title_elem.get_text(strip=True) if title_elem else ''
            
            if not link or not link.get('href') or not title:
                return None
            
            url = urljoin(f"https://{domain}", link.get('href'))
            
            # Extract description
            description = ""
            desc_elem = element.find(['p', 'div'], class_=re.compile(r'description|summary|excerpt|abstract'))
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            doc_type = self._classify_document_type(title, description, url)
            
            return {
                'title': title,
                'url': url,
                'description': description,
                'domain': domain,
                'document_type': doc_type,
                'search_term': search_term,
                'discovered_at': datetime.now().isoformat(),
                'file_type': self._get_file_type_from_url(url),
                'relevance_score': self._calculate_relevance_score(title, description, search_term)
            }
            
        except Exception as e:
            logger.error(f"Error extracting generic document info: {e}")
            return None
    
    def _classify_document_type(self, title: str, description: str, url: str) -> str:
        """Classify document type based on content"""
        
        text = f"{title} {description} {url}".lower()
        
        for doc_type, patterns in self.document_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    return doc_type
        
        return 'unknown'
    
    def _get_file_type_from_url(self, url: str) -> str:
        """Determine file type from URL"""
        
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith('.pdf'):
            return 'pdf'
        elif path.endswith(('.doc', '.docx')):
            return 'word'
        elif path.endswith(('.xls', '.xlsx')):
            return 'excel'
        elif path.endswith('.xml'):
            return 'xml'
        elif path.endswith('.json'):
            return 'json'
        else:
            return 'html'
    
    def _calculate_relevance_score(self, title: str, description: str, search_term: str) -> float:
        """Calculate relevance score for document"""
        
        text = f"{title} {description}".lower()
        search_words = search_term.lower().split()
        
        score = 0.0
        total_words = len(search_words)
        
        for word in search_words:
            if word in text:
                # Higher score for title matches
                if word in title.lower():
                    score += 2.0
                else:
                    score += 1.0
        
        return min(score / total_words, 1.0) if total_words > 0 else 0.0
    
    def _deduplicate_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate documents"""
        
        seen_urls = set()
        unique_docs = []
        
        for doc in documents:
            url = doc.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_docs.append(doc)
        
        return unique_docs
    
    async def _analyze_documents_with_ai(self, documents: List[Dict[str, Any]], industry: str) -> List[Dict[str, Any]]:
        """Analyze documents with AI to extract insights and improve categorization"""
        
        logger.info(f"Analyzing {len(documents)} documents with AI")
        
        analyzed_docs = []
        
        for doc in documents:
            try:
                # Create AI analysis prompt
                analysis_prompt = f"""
                You are an expert regulatory and policy analyst. Analyze this document and provide structured insights.
                
                Document Information:
                Title: {doc.get('title', '')}
                URL: {doc.get('url', '')}
                Description: {doc.get('description', '')}
                Domain: {doc.get('domain', '')}
                Industry Context: {industry}
                
                Please provide analysis in JSON format:
                
                {{
                    "document_classification": {{
                        "primary_type": "legislation|guidance|policy|standard|report|consultation|other",
                        "secondary_type": "specific subtype",
                        "regulatory_authority": "name of issuing authority",
                        "jurisdiction": "UK|EU|England|Scotland|Wales|Northern Ireland|Other",
                        "industry_relevance": "high|medium|low",
                        "compliance_impact": "mandatory|recommended|informational"
                    }},
                    "content_analysis": {{
                        "key_topics": ["list of main topics"],
                        "regulatory_requirements": ["list of requirements if any"],
                        "target_audience": ["who this applies to"],
                        "effective_date": "date if mentioned or null",
                        "review_date": "review date if mentioned or null"
                    }},
                    "business_impact": {{
                        "affected_sectors": ["list of affected business sectors"],
                        "compliance_actions": ["actions businesses need to take"],
                        "deadlines": ["any important deadlines"],
                        "penalties": ["penalties for non-compliance if mentioned"]
                    }},
                    "strategic_insights": {{
                        "importance_score": 0.85,
                        "urgency_level": "high|medium|low",
                        "implementation_complexity": "high|medium|low",
                        "monitoring_required": true,
                        "related_documents": ["suggestions for related documents to find"]
                    }},
                    "summary": "2-3 sentence summary of the document's purpose and impact"
                }}
                
                Focus on practical business implications and compliance requirements.
                """
                
                # Get AI analysis
                ai_response = await self.vertex_ai.generate_content_async(analysis_prompt)
                
                # Parse AI response
                try:
                    import json
                    import re
                    
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        ai_analysis = json.loads(json_match.group())
                        doc['ai_analysis'] = ai_analysis
                        doc['ai_analyzed_at'] = datetime.now().isoformat()
                        
                        # Update document classification based on AI analysis
                        if 'document_classification' in ai_analysis:
                            classification = ai_analysis['document_classification']
                            doc['document_type'] = classification.get('primary_type', doc.get('document_type'))
                            doc['regulatory_authority'] = classification.get('regulatory_authority')
                            doc['jurisdiction'] = classification.get('jurisdiction')
                            doc['industry_relevance'] = classification.get('industry_relevance')
                            doc['compliance_impact'] = classification.get('compliance_impact')
                        
                        # Add strategic insights
                        if 'strategic_insights' in ai_analysis:
                            insights = ai_analysis['strategic_insights']
                            doc['importance_score'] = insights.get('importance_score', 0.5)
                            doc['urgency_level'] = insights.get('urgency_level', 'medium')
                            doc['monitoring_required'] = insights.get('monitoring_required', False)
                    
                except Exception as parse_error:
                    logger.error(f"Failed to parse AI analysis for document {doc.get('title', 'Unknown')}: {parse_error}")
                    doc['ai_analysis'] = {'raw_response': ai_response, 'parsing_error': str(parse_error)}
                
                analyzed_docs.append(doc)
                
                # Respectful delay for AI calls
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Failed to analyze document {doc.get('title', 'Unknown')}: {e}")
                doc['ai_analysis_error'] = str(e)
                analyzed_docs.append(doc)
        
        return analyzed_docs
    
    async def download_and_process_documents(self, 
                                           documents: List[Dict[str, Any]], 
                                           download_limit: int = 50,
                                           file_types: List[str] = None) -> List[Dict[str, Any]]:
        """Download and process document content"""
        
        if file_types is None:
            file_types = ['pdf', 'html', 'word', 'xml']
        
        logger.info(f"Downloading and processing up to {download_limit} documents")
        
        # Create downloads directory
        downloads_dir = "regulatory_documents"
        os.makedirs(downloads_dir, exist_ok=True)
        
        processed_docs = []
        
        # Sort by importance and relevance
        sorted_docs = sorted(documents, 
                           key=lambda x: (x.get('importance_score', 0.5), x.get('relevance_score', 0.5)), 
                           reverse=True)
        
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=60)
        session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        
        try:
            for i, doc in enumerate(sorted_docs[:download_limit]):
                if doc.get('file_type') not in file_types:
                    continue
                
                try:
                    logger.info(f"Processing document {i+1}/{min(download_limit, len(sorted_docs))}: {doc.get('title', 'Unknown')}")
                    
                    # Download document
                    downloaded_doc = await self._download_document(session, doc, downloads_dir)
                    
                    if downloaded_doc:
                        # Extract text content
                        text_content = await self._extract_text_content(downloaded_doc)
                        
                        if text_content:
                            downloaded_doc['text_content'] = text_content
                            downloaded_doc['content_length'] = len(text_content)
                            
                            # Analyze content with AI
                            content_analysis = await self._analyze_document_content(downloaded_doc, text_content)
                            downloaded_doc['content_analysis'] = content_analysis
                        
                        processed_docs.append(downloaded_doc)
                    
                    # Respectful delay
                    await asyncio.sleep(2.0)
                    
                except Exception as e:
                    logger.error(f"Failed to process document {doc.get('title', 'Unknown')}: {e}")
                    continue
        
        finally:
            await session.close()
        
        self.processed_documents = processed_docs
        
        logger.info(f"Successfully processed {len(processed_docs)} documents")
        
        return processed_docs
    
    async def _download_document(self, session: aiohttp.ClientSession, doc: Dict[str, Any], downloads_dir: str) -> Optional[Dict[str, Any]]:
        """Download a single document"""
        
        try:
            url = doc.get('url')
            if not url:
                return None
            
            # Create safe filename
            title = doc.get('title', 'unknown')
            safe_title = re.sub(r'[^\w\s-]', '', title)[:100]
            file_ext = doc.get('file_type', 'html')
            filename = f"{safe_title}.{file_ext}"
            filepath = os.path.join(downloads_dir, filename)
            
            # Download file
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Save to file
                    with open(filepath, 'wb') as f:
                        f.write(content)
                    
                    # Update document info
                    doc['local_filepath'] = filepath
                    doc['file_size'] = len(content)
                    doc['downloaded_at'] = datetime.now().isoformat()
                    doc['download_status'] = 'success'
                    
                    return doc
                else:
                    logger.warning(f"Failed to download {url}: HTTP {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error downloading document from {doc.get('url')}: {e}")
            return None
    
    async def _extract_text_content(self, doc: Dict[str, Any]) -> Optional[str]:
        """Extract text content from downloaded document"""
        
        filepath = doc.get('local_filepath')
        file_type = doc.get('file_type')
        
        if not filepath or not os.path.exists(filepath):
            return None
        
        try:
            if file_type == 'html':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    html = f.read()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    return soup.get_text()
            
            elif file_type == 'pdf':
                try:
                    import PyPDF2
                    with open(filepath, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        return text
                except ImportError:
                    logger.warning("PyPDF2 not available for PDF processing")
                    return None
            
            elif file_type in ['word', 'docx']:
                try:
                    from docx import Document
                    doc_obj = Document(filepath)
                    text = ""
                    for paragraph in doc_obj.paragraphs:
                        text += paragraph.text + "\n"
                    return text
                except ImportError:
                    logger.warning("python-docx not available for Word processing")
                    return None
            
            elif file_type == 'xml':
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    soup = BeautifulSoup(content, 'xml')
                    return soup.get_text()
            
            else:
                # Try as plain text
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        
        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {e}")
            return None
    
    async def _analyze_document_content(self, doc: Dict[str, Any], text_content: str) -> Dict[str, Any]:
        """Analyze document content with AI"""
        
        try:
            # Truncate content for AI analysis (to avoid token limits)
            content_sample = text_content[:8000] if len(text_content) > 8000 else text_content
            
            analysis_prompt = f"""
            You are an expert regulatory analyst. Analyze this document content and extract key information.
            
            Document: {doc.get('title', 'Unknown')}
            Content Sample: {content_sample}
            
            Provide analysis in JSON format:
            
            {{
                "key_findings": {{
                    "main_requirements": ["list of key regulatory requirements"],
                    "compliance_deadlines": ["any deadlines mentioned"],
                    "affected_parties": ["who must comply"],
                    "penalties": ["penalties for non-compliance"],
                    "exemptions": ["any exemptions mentioned"]
                }},
                "content_structure": {{
                    "sections": ["main sections of the document"],
                    "appendices": ["any appendices or schedules"],
                    "references": ["other documents referenced"],
                    "definitions": ["key terms defined"]
                }},
                "practical_impact": {{
                    "implementation_steps": ["steps for implementation"],
                    "cost_implications": ["any cost implications mentioned"],
                    "timeline": "implementation timeline if specified",
                    "monitoring_requirements": ["ongoing monitoring required"]
                }},
                "risk_assessment": {{
                    "compliance_risk": "high|medium|low",
                    "business_impact": "high|medium|low",
                    "implementation_difficulty": "high|medium|low",
                    "regulatory_scrutiny": "high|medium|low"
                }},
                "actionable_insights": ["specific actions organizations should take"],
                "content_quality": {{
                    "completeness": 0.85,
                    "clarity": 0.90,
                    "actionability": 0.75
                }}
            }}
            
            Focus on practical, actionable insights for compliance and business operations.
            """
            
            ai_response = await self.vertex_ai.generate_content_async(analysis_prompt)
            
            # Parse response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {'raw_analysis': ai_response, 'parsing_error': 'Could not extract JSON'}
        
        except Exception as e:
            logger.error(f"Error analyzing document content: {e}")
            return {'error': str(e)}
    
    def save_to_database(self, documents: List[Dict[str, Any]]) -> bool:
        """Save discovered documents to database"""
        
        try:
            from database.regulatory_document_manager import RegulatoryDocumentManager
            
            doc_manager = RegulatoryDocumentManager()
            
            for doc in documents:
                doc_manager.save_document(doc)
            
            logger.info(f"Saved {len(documents)} documents to database")
            return True
            
        except Exception as e:
            logger.error(f"Error saving documents to database: {e}")
            return False
    
    def generate_discovery_report(self, documents: List[Dict[str, Any]], industry: str) -> Dict[str, Any]:
        """Generate comprehensive discovery report"""
        
        report = {
            'discovery_summary': {
                'industry': industry,
                'total_documents': len(documents),
                'discovery_date': datetime.now().isoformat(),
                'document_types': {},
                'regulatory_authorities': {},
                'jurisdictions': {},
                'urgency_levels': {}
            },
            'key_findings': [],
            'compliance_priorities': [],
            'recommended_actions': [],
            'monitoring_requirements': []
        }
        
        # Analyze document distribution
        for doc in documents:
            doc_type = doc.get('document_type', 'unknown')
            report['discovery_summary']['document_types'][doc_type] = \
                report['discovery_summary']['document_types'].get(doc_type, 0) + 1
            
            authority = doc.get('regulatory_authority', 'unknown')
            report['discovery_summary']['regulatory_authorities'][authority] = \
                report['discovery_summary']['regulatory_authorities'].get(authority, 0) + 1
            
            jurisdiction = doc.get('jurisdiction', 'unknown')
            report['discovery_summary']['jurisdictions'][jurisdiction] = \
                report['discovery_summary']['jurisdictions'].get(jurisdiction, 0) + 1
            
            urgency = doc.get('urgency_level', 'medium')
            report['discovery_summary']['urgency_levels'][urgency] = \
                report['discovery_summary']['urgency_levels'].get(urgency, 0) + 1
        
        # Extract high-priority items
        high_priority_docs = [doc for doc in documents if doc.get('urgency_level') == 'high']
        mandatory_docs = [doc for doc in documents if doc.get('compliance_impact') == 'mandatory']
        
        report['compliance_priorities'] = [
            {
                'title': doc.get('title'),
                'url': doc.get('url'),
                'urgency_level': doc.get('urgency_level'),
                'compliance_impact': doc.get('compliance_impact'),
                'summary': doc.get('ai_analysis', {}).get('summary', '')
            }
            for doc in high_priority_docs[:10]
        ]
        
        return report

# Global instance
regulatory_agent = None

def get_regulatory_agent() -> RegulatoryDocumentAgent:
    """Get global regulatory document agent instance"""
    global regulatory_agent
    if regulatory_agent is None:
        regulatory_agent = RegulatoryDocumentAgent()
    return regulatory_agent