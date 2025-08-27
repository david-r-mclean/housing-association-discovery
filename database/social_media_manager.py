"""
Social Media Database Manager
Manages social media intelligence data storage and retrieval
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SocialMediaManager:
    """Manages social media intelligence data"""
    
    def __init__(self, db_path: str = "social_media_intelligence.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the social media database"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Social media profiles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS social_media_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        association_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        profile_handle TEXT,
                        profile_url TEXT,
                        profile_name TEXT,
                        verified BOOLEAN DEFAULT FALSE,
                        followers_count INTEGER DEFAULT 0,
                        following_count INTEGER DEFAULT 0,
                        posts_count INTEGER DEFAULT 0,
                        profile_data TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(association_name, platform, profile_handle)
                    )
                """)
                
                # Social media posts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS social_media_posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        association_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        post_id TEXT,
                        post_url TEXT,
                        content TEXT,
                        post_type TEXT,
                        author TEXT,
                        published_date TIMESTAMP,
                        likes_count INTEGER DEFAULT 0,
                        shares_count INTEGER DEFAULT 0,
                        comments_count INTEGER DEFAULT 0,
                        engagement_rate REAL DEFAULT 0.0,
                        sentiment_score REAL DEFAULT 0.0,
                        sentiment_label TEXT DEFAULT 'neutral',
                        hashtags TEXT,
                        mentions TEXT,
                        post_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, post_id)
                    )
                """)
                
                # Social media mentions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS social_media_mentions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        association_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        mention_id TEXT,
                        mention_url TEXT,
                        content TEXT,
                        author TEXT,
                        author_followers INTEGER DEFAULT 0,
                        published_date TIMESTAMP,
                        sentiment_score REAL DEFAULT 0.0,
                        sentiment_label TEXT DEFAULT 'neutral',
                        engagement_metrics TEXT,
                        context TEXT,
                        mention_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(platform, mention_id)
                    )
                """)
                
                # Social media analytics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS social_media_analytics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        association_name TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        analysis_date DATE NOT NULL,
                        followers_count INTEGER DEFAULT 0,
                        following_count INTEGER DEFAULT 0,
                        posts_count INTEGER DEFAULT 0,
                        engagement_rate REAL DEFAULT 0.0,
                        reach INTEGER DEFAULT 0,
                        impressions INTEGER DEFAULT 0,
                        sentiment_score REAL DEFAULT 0.0,
                        analytics_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(association_name, platform, analysis_date)
                    )
                """)
                
                # Social media reports table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS social_media_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        association_name TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        report_date DATE NOT NULL,
                        analysis_period TEXT,
                        platforms_analyzed TEXT,
                        digital_presence_score REAL DEFAULT 0.0,
                        overall_sentiment REAL DEFAULT 0.0,
                        key_findings TEXT,
                        recommendations TEXT,
                        report_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_association ON social_media_profiles(association_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_platform ON social_media_profiles(platform)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_association ON social_media_posts(association_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_platform ON social_media_posts(platform)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_date ON social_media_posts(published_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_association ON social_media_mentions(association_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_mentions_sentiment ON social_media_mentions(sentiment_label)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_association ON social_media_analytics(association_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_association ON social_media_reports(association_name)")
                
                conn.commit()
                logger.info("Social media database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize social media database: {e}")
            raise
    
    def save_social_media_analysis(self, association_name: str, analysis_data: Dict[str, Any]) -> int:
        """Save complete social media analysis"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Save social media profiles
                social_data = analysis_data.get('social_media_data', {})
                for platform, platform_data in social_data.items():
                    if isinstance(platform_data, dict) and 'error' not in platform_data:
                        self._save_platform_profiles(cursor, association_name, platform, platform_data)
                        self._save_platform_posts(cursor, association_name, platform, platform_data)
                        self._save_platform_mentions(cursor, association_name, platform, platform_data)
                        self._save_platform_analytics(cursor, association_name, platform, platform_data)
                
                # Save overall report
                report_id = self._save_social_media_report(cursor, association_name, analysis_data)
                
                conn.commit()
                logger.info(f"Social media analysis saved for {association_name}")
                return report_id
                
        except Exception as e:
            logger.error(f"Failed to save social media analysis: {e}")
            raise
    
    def _save_platform_profiles(self, cursor, association_name: str, platform: str, platform_data: Dict[str, Any]):
        """Save social media profiles for a platform"""
        
        profiles = platform_data.get('profiles', []) or platform_data.get('pages', []) or platform_data.get('channels', [])
        
        for profile in profiles:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO social_media_profiles 
                    (association_name, platform, profile_handle, profile_url, profile_name, 
                     verified, followers_count, following_count, posts_count, profile_data, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    association_name,
                    platform,
                    profile.get('handle') or profile.get('name', ''),
                    profile.get('profile_url') or profile.get('url', ''),
                    profile.get('name', ''),
                    profile.get('verified', False),
                    profile.get('followers', 0),
                    profile.get('following', 0),
                    profile.get('posts_count', 0),
                    json.dumps(profile),
                    datetime.now().isoformat()
                ))
                
            except Exception as e:
                logger.error(f"Error saving profile for {platform}: {e}")
    
    def _save_platform_posts(self, cursor, association_name: str, platform: str, platform_data: Dict[str, Any]):
        """Save social media posts for a platform"""
        
        posts = platform_data.get('posts', []) or platform_data.get('videos', [])
        
        for post in posts:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO social_media_posts 
                    (association_name, platform, post_id, post_url, content, post_type, author,
                     published_date, likes_count, shares_count, comments_count, engagement_rate,
                     sentiment_score, sentiment_label, hashtags, mentions, post_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    association_name,
                    platform,
                    post.get('id', ''),
                    post.get('url', ''),
                    post.get('content') or post.get('text', ''),
                    post.get('type', 'post'),
                    post.get('author', ''),
                    post.get('published_date'),
                    post.get('likes', 0),
                    post.get('shares', 0),
                    post.get('comments', 0),
                    post.get('engagement_rate', 0.0),
                    post.get('sentiment_score', 0.0),
                    post.get('sentiment', 'neutral'),
                    json.dumps(post.get('hashtags', [])),
                    json.dumps(post.get('mentions', [])),
                    json.dumps(post)
                ))
                
            except Exception as e:
                logger.error(f"Error saving post for {platform}: {e}")
    
    def _save_platform_mentions(self, cursor, association_name: str, platform: str, platform_data: Dict[str, Any]):
        """Save social media mentions for a platform"""
        
        mentions = platform_data.get('mentions', [])
        
        for mention in mentions:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO social_media_mentions 
                    (association_name, platform, mention_id, mention_url, content, author,
                     author_followers, published_date, sentiment_score, sentiment_label,
                     engagement_metrics, context, mention_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    association_name,
                    platform,
                    mention.get('id', ''),
                    mention.get('url', ''),
                    mention.get('content') or mention.get('text', ''),
                    mention.get('author', ''),
                    mention.get('author_followers', 0),
                    mention.get('published_date'),
                    mention.get('sentiment_score', 0.0),
                    mention.get('sentiment', 'neutral'),
                    json.dumps(mention.get('engagement', {})),
                    mention.get('context', ''),
                    json.dumps(mention)
                ))
                
            except Exception as e:
                logger.error(f"Error saving mention for {platform}: {e}")
    
    def _save_platform_analytics(self, cursor, association_name: str, platform: str, platform_data: Dict[str, Any]):
        """Save social media analytics for a platform"""
        
        metrics = platform_data.get('metrics', {})
        if not metrics:
            return
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO social_media_analytics 
                (association_name, platform, analysis_date, followers_count, following_count,
                 posts_count, engagement_rate, reach, impressions, sentiment_score, analytics_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                association_name,
                platform,
                datetime.now().date().isoformat(),
                metrics.get('followers', 0),
                metrics.get('following', 0),
                metrics.get('posts', 0),
                metrics.get('engagement_rate', 0.0),
                metrics.get('reach', 0),
                metrics.get('impressions', 0),
                metrics.get('sentiment_score', 0.0),
                json.dumps(metrics)
            ))
            
        except Exception as e:
            logger.error(f"Error saving analytics for {platform}: {e}")
    
    def _save_social_media_report(self, cursor, association_name: str, analysis_data: Dict[str, Any]) -> int:
        """Save social media report"""
        
        try:
            report = analysis_data.get('report', {})
            analysis = analysis_data.get('analysis', {})
            insights = analysis_data.get('insights', {})
            
            cursor.execute("""
                INSERT INTO social_media_reports 
                (association_name, report_type, report_date, analysis_period, platforms_analyzed,
                 digital_presence_score, overall_sentiment, key_findings, recommendations, report_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                association_name,
                'comprehensive_analysis',
                datetime.now().date().isoformat(),
                '30_days',
                json.dumps(analysis_data.get('platforms_analyzed', [])),
                analysis.get('digital_presence_score', {}).get('overall_score', 0.0),
                analysis.get('sentiment_analysis', {}).get('sentiment_score', 0.0),
                json.dumps(report.get('executive_summary', {}).get('key_findings', [])),
                json.dumps(insights.get('strategic_priorities', [])),
                json.dumps(analysis_data)
            ))
            
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error saving social media report: {e}")
            raise
    
    def get_social_media_profiles(self, association_name: str = None, platform: str = None) -> List[Dict[str, Any]]:
        """Get social media profiles"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM social_media_profiles WHERE 1=1"
                params = []
                
                if association_name:
                    query += " AND association_name = ?"
                    params.append(association_name)
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                query += " ORDER BY last_updated DESC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                profiles = []
                for row in rows:
                    profile = dict(row)
                    if profile['profile_data']:
                        profile['profile_data'] = json.loads(profile['profile_data'])
                    profiles.append(profile)
                
                return profiles
                
        except Exception as e:
            logger.error(f"Error retrieving social media profiles: {e}")
            return []
    
    def get_social_media_analytics(self, association_name: str, days: int = 30) -> Dict[str, Any]:
        """Get social media analytics summary"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get recent analytics
                cursor.execute("""
                    SELECT platform, AVG(followers_count) as avg_followers, 
                           AVG(engagement_rate) as avg_engagement,
                           AVG(sentiment_score) as avg_sentiment,
                           COUNT(*) as data_points
                    FROM social_media_analytics 
                    WHERE association_name = ? 
                    AND analysis_date >= date('now', '-{} days')
                    GROUP BY platform
                """.format(days), (association_name,))
                
                analytics_data = {}
                for row in cursor.fetchall():
                    analytics_data[row['platform']] = {
                        'avg_followers': row['avg_followers'],
                        'avg_engagement': row['avg_engagement'],
                        'avg_sentiment': row['avg_sentiment'],
                        'data_points': row['data_points']
                    }
                
                # Get total counts
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT platform) as platforms_count,
                        SUM(followers_count) as total_followers,
                        AVG(engagement_rate) as overall_engagement,
                        AVG(sentiment_score) as overall_sentiment
                    FROM social_media_profiles 
                    WHERE association_name = ?
                """, (association_name,))
                
                summary = cursor.fetchone()
                
                return {
                    'association_name': association_name,
                    'analysis_period_days': days,
                    'platforms_count': summary['platforms_count'] or 0,
                    'total_followers': summary['total_followers'] or 0,
                    'overall_engagement': summary['overall_engagement'] or 0.0,
                    'overall_sentiment': summary['overall_sentiment'] or 0.0,
                    'platform_analytics': analytics_data
                }
                
        except Exception as e:
            logger.error(f"Error retrieving social media analytics: {e}")
            return {}
    
    def get_social_media_reports(self, association_name: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get social media reports"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM social_media_reports WHERE 1=1"
                params = []
                
                if association_name:
                    query += " AND association_name = ?"
                    params.append(association_name)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                reports = []
                for row in rows:
                    report = dict(row)
                    # Parse JSON fields
                    for field in ['platforms_analyzed', 'key_findings', 'recommendations', 'report_data']:
                        if report.get(field):
                            try:
                                report[field] = json.loads(report[field])
                            except:
                                pass
                    reports.append(report)
                
                return reports
                
        except Exception as e:
            logger.error(f"Error retrieving social media reports: {e}")
            return []
    
    def search_social_media_content(self, search_term: str, platform: str = None, 
                                  content_type: str = None) -> Dict[str, Any]:
        """Search social media content"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                results = {
                    'posts': [],
                    'mentions': [],
                    'profiles': []
                }
                
                # Search posts
                query = "SELECT * FROM social_media_posts WHERE content LIKE ?"
                params = [f"%{search_term}%"]
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                cursor.execute(query, params)
                for row in cursor.fetchall():
                    post = dict(row)
                    if post['post_data']:
                        post['post_data'] = json.loads(post['post_data'])
                    results['posts'].append(post)
                
                # Search mentions
                query = "SELECT * FROM social_media_mentions WHERE content LIKE ?"
                params = [f"%{search_term}%"]
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                cursor.execute(query, params)
                for row in cursor.fetchall():
                    mention = dict(row)
                    if mention['mention_data']:
                        mention['mention_data'] = json.loads(mention['mention_data'])
                    results['mentions'].append(mention)
                
                # Search profiles
                query = "SELECT * FROM social_media_profiles WHERE profile_name LIKE ? OR profile_handle LIKE ?"
                params = [f"%{search_term}%", f"%{search_term}%"]
                
                if platform:
                    query += " AND platform = ?"
                    params.append(platform)
                
                cursor.execute(query, params)
                for row in cursor.fetchall():
                    profile = dict(row)
                    if profile['profile_data']:
                        profile['profile_data'] = json.loads(profile['profile_data'])
                    results['profiles'].append(profile)
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching social media content: {e}")
            return {'posts': [], 'mentions': [], 'profiles': []}
    
    def get_sentiment_analysis(self, association_name: str, days: int = 30) -> Dict[str, Any]:
        """Get sentiment analysis summary"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get sentiment from posts
                cursor.execute("""
                    SELECT platform, sentiment_label, COUNT(*) as count,
                           AVG(sentiment_score) as avg_score
                    FROM social_media_posts 
                    WHERE association_name = ? 
                    AND published_date >= date('now', '-{} days')
                    GROUP BY platform, sentiment_label
                """.format(days), (association_name,))
                
                post_sentiment = {}
                for row in cursor.fetchall():
                    platform = row['platform']
                    if platform not in post_sentiment:
                        post_sentiment[platform] = {}
                    post_sentiment[platform][row['sentiment_label']] = {
                        'count': row['count'],
                        'avg_score': row['avg_score']
                    }
                
                # Get sentiment from mentions
                cursor.execute("""
                    SELECT platform, sentiment_label, COUNT(*) as count,
                           AVG(sentiment_score) as avg_score
                    FROM social_media_mentions 
                    WHERE association_name = ? 
                    AND published_date >= date('now', '-{} days')
                    GROUP BY platform, sentiment_label
                """.format(days), (association_name,))
                
                mention_sentiment = {}
                for row in cursor.fetchall():
                    platform = row['platform']
                    if platform not in mention_sentiment:
                        mention_sentiment[platform] = {}
                    mention_sentiment[platform][row['sentiment_label']] = {
                        'count': row['count'],
                        'avg_score': row['avg_score']
                    }
                
                return {
                    'association_name': association_name,
                    'analysis_period_days': days,
                    'post_sentiment': post_sentiment,
                    'mention_sentiment': mention_sentiment
                }
                
        except Exception as e:
            logger.error(f"Error retrieving sentiment analysis: {e}")
            return {}

# Global instance
social_media_manager = None

def get_social_media_manager() -> SocialMediaManager:
    """Get global social media manager instance"""
    global social_media_manager
    if social_media_manager is None:
        social_media_manager = SocialMediaManager()
    return social_media_manager