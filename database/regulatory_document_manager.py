"""
Database Manager for Regulatory Documents
Handles storage and retrieval of regulatory documents and analysis
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class RegulatoryDocumentManager:
    """Manages regulatory documents in database"""
    
    def __init__(self, db_path: str = "regulatory_documents.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create regulatory documents table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS regulatory_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        description TEXT,
                        domain TEXT,
                        document_type TEXT,
                        file_type TEXT,
                        regulatory_authority TEXT,
                        jurisdiction TEXT,
                        industry_relevance TEXT,
                        compliance_impact TEXT,
                        importance_score REAL,
                        urgency_level TEXT,
                        relevance_score REAL,
                        search_term TEXT,
                        local_filepath TEXT,
                        file_size INTEGER,
                        content_length INTEGER,
                        ai_analysis TEXT,
                        content_analysis TEXT,
                        discovered_at TEXT,
                        downloaded_at TEXT,
                        ai_analyzed_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create document content table for full text
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS document_content (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        text_content TEXT,
                        content_hash TEXT,
                        extracted_at TEXT,
                        FOREIGN KEY (document_id) REFERENCES regulatory_documents (id)
                    )
                ''')
                
                # Create document relationships table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS document_relationships (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_document_id INTEGER,
                        related_document_id INTEGER,
                        relationship_type TEXT,
                        confidence_score REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_document_id) REFERENCES regulatory_documents (id),
                        FOREIGN KEY (related_document_id) REFERENCES regulatory_documents (id)
                    )
                ''')
                
                # Create compliance tracking table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS compliance_tracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        organization_id INTEGER,
                        compliance_status TEXT,
                        due_date TEXT,
                        completion_date TEXT,
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (document_id) REFERENCES regulatory_documents (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_type ON regulatory_documents(document_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_authority ON regulatory_documents(regulatory_authority)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON regulatory_documents(jurisdiction)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_urgency ON regulatory_documents(urgency_level)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_compliance ON regulatory_documents(compliance_impact)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_relevance ON regulatory_documents(industry_relevance)')
                
                conn.commit()
                logger.info("Regulatory documents database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing regulatory documents database: {e}")
            raise
    
    def save_document(self, doc: Dict[str, Any]) -> int:
        """Save a regulatory document to database"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Prepare document data
                doc_data = (
                    doc.get('title'),
                    doc.get('url'),
                    doc.get('description'),
                    doc.get('domain'),
                    doc.get('document_type'),
                    doc.get('file_type'),
                    doc.get('regulatory_authority'),
                    doc.get('jurisdiction'),
                    doc.get('industry_relevance'),
                    doc.get('compliance_impact'),
                    doc.get('importance_score'),
                    doc.get('urgency_level'),
                    doc.get('relevance_score'),
                    doc.get('search_term'),
                    doc.get('local_filepath'),
                    doc.get('file_size'),
                    doc.get('content_length'),
                    json.dumps(doc.get('ai_analysis', {})),
                    json.dumps(doc.get('content_analysis', {})),
                    doc.get('discovered_at'),
                    doc.get('downloaded_at'),
                    doc.get('ai_analyzed_at'),
                    datetime.now().isoformat()
                )
                
                # Insert or update document
                cursor.execute('''
                    INSERT OR REPLACE INTO regulatory_documents (
                        title, url, description, domain, document_type, file_type,
                        regulatory_authority, jurisdiction, industry_relevance, compliance_impact,
                        importance_score, urgency_level, relevance_score, search_term,
                        local_filepath, file_size, content_length, ai_analysis, content_analysis,
                        discovered_at, downloaded_at, ai_analyzed_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', doc_data)
                
                document_id = cursor.lastrowid
                
                # Save text content if available
                if doc.get('text_content'):
                    import hashlib
                    content_hash = hashlib.md5(doc['text_content'].encode()).hexdigest()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO document_content (
                            document_id, text_content, content_hash, extracted_at
                        ) VALUES (?, ?, ?, ?)
                    ''', (document_id, doc['text_content'], content_hash, datetime.now().isoformat()))
                
                conn.commit()
                logger.info(f"Saved document: {doc.get('title', 'Unknown')}")
                
                return document_id
                
        except Exception as e:
            logger.error(f"Error saving document {doc.get('title', 'Unknown')}: {e}")
            raise
    
    def get_documents(self, 
                     document_type: str = None,
                     regulatory_authority: str = None,
                     jurisdiction: str = None,
                     urgency_level: str = None,
                     compliance_impact: str = None,
                     industry_relevance: str = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Get documents with optional filtering"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query with filters
                query = "SELECT * FROM regulatory_documents WHERE 1=1"
                params = []
                
                if document_type:
                    query += " AND document_type = ?"
                    params.append(document_type)
                
                if regulatory_authority:
                    query += " AND regulatory_authority = ?"
                    params.append(regulatory_authority)
                
                if jurisdiction:
                    query += " AND jurisdiction = ?"
                    params.append(jurisdiction)
                
                if urgency_level:
                    query += " AND urgency_level = ?"
                    params.append(urgency_level)
                
                if compliance_impact:
                    query += " AND compliance_impact = ?"
                    params.append(compliance_impact)
                
                if industry_relevance:
                    query += " AND industry_relevance = ?"
                    params.append(industry_relevance)
                
                query += " ORDER BY importance_score DESC, created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert to dictionaries
                columns = [description[0] for description in cursor.description]
                documents = []
                
                for row in rows:
                    doc = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    if doc.get('ai_analysis'):
                        try:
                            doc['ai_analysis'] = json.loads(doc['ai_analysis'])
                        except:
                            pass
                    
                    if doc.get('content_analysis'):
                        try:
                            doc['content_analysis'] = json.loads(doc['content_analysis'])
                        except:
                            pass
                    
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def get_document_content(self, document_id: int) -> Optional[str]:
        """Get full text content for a document"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT text_content FROM document_content 
                    WHERE document_id = ?
                ''', (document_id,))
                
                result = cursor.fetchone()
                return result[0] if result else None
                
        except Exception as e:
            logger.error(f"Error getting document content for ID {document_id}: {e}")
            return None
    
    def search_documents(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents by text content"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Search in title, description, and content
                cursor.execute('''
                    SELECT d.*, c.text_content 
                    FROM regulatory_documents d
                    LEFT JOIN document_content c ON d.id = c.document_id
                    WHERE d.title LIKE ? OR d.description LIKE ? OR c.text_content LIKE ?
                    ORDER BY d.importance_score DESC, d.relevance_score DESC
                    LIMIT ?
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', limit))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                documents = []
                for row in rows:
                    doc = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    if doc.get('ai_analysis'):
                        try:
                            doc['ai_analysis'] = json.loads(doc['ai_analysis'])
                        except:
                            pass
                    
                    if doc.get('content_analysis'):
                        try:
                            doc['content_analysis'] = json.loads(doc['content_analysis'])
                        except:
                            pass
                    
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary statistics"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get document counts by various categories
                summary = {}
                
                # By document type
                cursor.execute('''
                    SELECT document_type, COUNT(*) as count 
                    FROM regulatory_documents 
                    GROUP BY document_type
                ''')
                summary['by_document_type'] = dict(cursor.fetchall())
                
                # By urgency level
                cursor.execute('''
                    SELECT urgency_level, COUNT(*) as count 
                    FROM regulatory_documents 
                    GROUP BY urgency_level
                ''')
                summary['by_urgency'] = dict(cursor.fetchall())
                
                # By compliance impact
                cursor.execute('''
                    SELECT compliance_impact, COUNT(*) as count 
                    FROM regulatory_documents 
                    GROUP BY compliance_impact
                ''')
                summary['by_compliance_impact'] = dict(cursor.fetchall())
                
                # By regulatory authority
                cursor.execute('''
                    SELECT regulatory_authority, COUNT(*) as count 
                    FROM regulatory_documents 
                    WHERE regulatory_authority IS NOT NULL
                    GROUP BY regulatory_authority
                    ORDER BY count DESC
                    LIMIT 10
                ''')
                summary['top_authorities'] = dict(cursor.fetchall())
                
                # Recent documents
                cursor.execute('''
                    SELECT COUNT(*) as count 
                    FROM regulatory_documents 
                    WHERE discovered_at > datetime('now', '-30 days')
                ''')
                summary['recent_documents'] = cursor.fetchone()[0]
                
                # High priority documents
                cursor.execute('''
                    SELECT COUNT(*) as count 
                    FROM regulatory_documents 
                    WHERE urgency_level = 'high' OR compliance_impact = 'mandatory'
                ''')
                summary['high_priority_documents'] = cursor.fetchone()[0]
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting compliance summary: {e}")
            return {}
    
    def add_compliance_tracking(self, document_id: int, organization_id: int, 
                              compliance_status: str, due_date: str = None, notes: str = None) -> int:
        """Add compliance tracking entry"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO compliance_tracking (
                        document_id, organization_id, compliance_status, due_date, notes
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (document_id, organization_id, compliance_status, due_date, notes))
                
                tracking_id = cursor.lastrowid
                conn.commit()
                
                return tracking_id
                
        except Exception as e:
            logger.error(f"Error adding compliance tracking: {e}")
            raise
    
    def export_documents_to_csv(self, filename: str = None) -> str:
        """Export documents to CSV file"""
        
        if filename is None:
            filename = f"regulatory_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            import csv
            
            documents = self.get_documents(limit=10000)  # Get all documents
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                if documents:
                    fieldnames = [
                        'title', 'url', 'document_type', 'regulatory_authority', 
                        'jurisdiction', 'compliance_impact', 'urgency_level',
                        'importance_score', 'relevance_score', 'discovered_at'
                    ]
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for doc in documents:
                        row = {field: doc.get(field, '') for field in fieldnames}
                        writer.writerow(row)
            
            logger.info(f"Exported {len(documents)} documents to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error exporting documents to CSV: {e}")
            raise

# Global instance
regulatory_doc_manager = None

def get_regulatory_doc_manager() -> RegulatoryDocumentManager:
    """Get global regulatory document manager instance"""
    global regulatory_doc_manager
    if regulatory_doc_manager is None:
        regulatory_doc_manager = RegulatoryDocumentManager()
    return regulatory_doc_manager