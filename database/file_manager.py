"""
Database File Manager
Handles database files and document storage
"""

import os
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseFileManager:
    """Manager for database files and document storage"""
    
    def __init__(self):
        self.database_dir = Path("database")
        self.documents_dir = Path("documents")
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        self.database_dir.mkdir(exist_ok=True)
        self.documents_dir.mkdir(exist_ok=True)
    
    def get_database_files(self) -> List[Dict[str, Any]]:
        """Get list of all database files"""
        files = []
        
        # SQLite databases
        for db_file in self.database_dir.glob("*.db"):
            try:
                stat = db_file.stat()
                
                # Get table count
                table_count = self.get_table_count(db_file)
                
                files.append({
                    "filename": db_file.name,
                    "path": str(db_file),
                    "type": "database",
                    "extension": ".db",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "table_count": table_count,
                    "category": "Database"
                })
            except Exception as e:
                logger.error(f"Error processing database file {db_file}: {e}")
        
        # Python database managers
        for py_file in self.database_dir.glob("*_manager.py"):
            try:
                stat = py_file.stat()
                files.append({
                    "filename": py_file.name,
                    "path": str(py_file),
                    "type": "python",
                    "extension": ".py",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "category": "Database Manager"
                })
            except Exception as e:
                logger.error(f"Error processing Python file {py_file}: {e}")
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    
    def get_document_files(self) -> List[Dict[str, Any]]:
        """Get list of all document files"""
        files = []
        
        document_extensions = ['.pdf', '.doc', '.docx', '.txt', '.md', '.json', '.xml', '.csv']
        
        for ext in document_extensions:
            for doc_file in self.documents_dir.glob(f"*{ext}"):
                try:
                    stat = doc_file.stat()
                    files.append({
                        "filename": doc_file.name,
                        "path": str(doc_file),
                        "type": "document",
                        "extension": ext,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "category": self.get_document_category(doc_file.name)
                    })
                except Exception as e:
                    logger.error(f"Error processing document file {doc_file}: {e}")
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    
    def get_table_count(self, db_path: Path) -> int:
        """Get number of tables in SQLite database"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Error getting table count for {db_path}: {e}")
            return 0
    
    def get_database_schema(self, db_path: Path) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            schema = {"tables": []}
            
            for table_name in tables:
                table_name = table_name[0]
                
                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                schema["tables"].append({
                    "name": table_name,
                    "columns": [
                        {
                            "name": col[1],
                            "type": col[2],
                            "not_null": bool(col[3]),
                            "primary_key": bool(col[5])
                        }
                        for col in columns
                    ],
                    "row_count": row_count
                })
            
            conn.close()
            return schema
            
        except Exception as e:
            logger.error(f"Error getting schema for {db_path}: {e}")
            return {"tables": [], "error": str(e)}
    
    def get_document_category(self, filename: str) -> str:
        """Categorize document based on filename"""
        filename_lower = filename.lower()
        
        if any(word in filename_lower for word in ['policy', 'policies']):
            return "Policy"
        elif any(word in filename_lower for word in ['regulation', 'regulatory']):
            return "Regulation"
        elif any(word in filename_lower for word in ['guideline', 'guide']):
            return "Guideline"
        elif any(word in filename_lower for word in ['report', 'analysis']):
            return "Report"
        elif any(word in filename_lower for word in ['form', 'application']):
            return "Form"
        else:
            return "Document"
    
    def read_file_content(self, file_path: str) -> Dict[str, Any]:
        """Read content from various file types"""
        path = Path(file_path)
        
        if not path.exists():
            return {"success": False, "error": "File not found"}
        
        try:
            if path.suffix == '.db':
                # For database files, return schema
                schema = self.get_database_schema(path)
                return {
                    "success": True,
                    "type": "database",
                    "content": json.dumps(schema, indent=2),
                    "schema": schema
                }
            
            elif path.suffix in ['.txt', '.md', '.py', '.json', '.xml', '.csv']:
                # Text-based files
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "type": "text",
                    "content": content,
                    "size": len(content)
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {path.suffix}"
                }
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def search_files(self, query: str) -> List[Dict[str, Any]]:
        """Search through database and document files"""
        results = []
        query_lower = query.lower()
        
        # Search database files
        db_files = self.get_database_files()
        for file_info in db_files:
            if query_lower in file_info["filename"].lower():
                results.append({
                    **file_info,
                    "match_type": "filename",
                    "matches": 1
                })
        
        # Search document files
        doc_files = self.get_document_files()
        for file_info in doc_files:
            matches = 0
            matching_lines = []
            
            # Check filename
            if query_lower in file_info["filename"].lower():
                matches += 1
            
            # Check content for text files
            if file_info["extension"] in ['.txt', '.md', '.py', '.json', '.xml', '.csv']:
                try:
                    content_result = self.read_file_content(file_info["path"])
                    if content_result["success"]:
                        content = content_result["content"]
                        lines = content.split('\n')
                        
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                matches += 1
                                matching_lines.append({
                                    "line_number": i + 1,
                                    "content": line.strip()
                                })
                                
                                if len(matching_lines) >= 5:  # Limit matches
                                    break
                except Exception as e:
                    logger.error(f"Error searching file {file_info['filename']}: {e}")
            
            if matches > 0:
                results.append({
                    **file_info,
                    "match_type": "content" if matching_lines else "filename",
                    "matches": matches,
                    "matching_lines": matching_lines[:5]
                })
        
        return sorted(results, key=lambda x: x["matches"], reverse=True)

# Global instance
_db_file_manager = None

def get_db_file_manager() -> DatabaseFileManager:
    """Get or create the global database file manager instance"""
    global _db_file_manager
    if _db_file_manager is None:
        _db_file_manager = DatabaseFileManager()
    return _db_file_manager