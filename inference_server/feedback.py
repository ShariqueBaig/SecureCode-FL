"""
User Feedback System for SecureCode-FL
======================================

This module handles user feedback for improving the vulnerability detection model.
Users can mark detections as false positives or report missed vulnerabilities.

The feedback is stored locally and used for:
1. Local model fine-tuning
2. Federated Learning updates (only model weights shared)
"""

import sqlite3
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class FeedbackType(Enum):
    FALSE_POSITIVE = "false_positive"  # System incorrectly flagged as vulnerable
    MISSED_VULNERABILITY = "missed_vulnerability"  # System missed a real vulnerability
    CONFIRMED_VULNERABLE = "confirmed_vulnerable"  # User confirms detection is correct
    CONFIRMED_SECURE = "confirmed_secure"  # User confirms code is secure


@dataclass
class UserFeedback:
    """Represents a single feedback entry from a user."""
    id: Optional[int]
    timestamp: str
    feedback_type: str
    code_snippet: str
    code_hash: str
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    original_detection: Optional[str]  # Original vulnerability type if any
    user_label: str  # "vulnerable" or "secure"
    severity: Optional[str]  # User-specified severity if marking as vulnerable
    vulnerability_type: Optional[str]  # User-specified type if marking as vulnerable
    notes: Optional[str]  # Additional user notes
    file_path: str
    language: str
    trained: bool = False  # Whether this feedback has been used for training


class FeedbackDatabase:
    """
    SQLite database for storing user feedback.
    
    Data stays LOCAL - only model weights are shared during FL.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the feedback database."""
        if db_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_path, "data", "user_feedback.db")
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Create the feedback table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                code_snippet TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                start_column INTEGER NOT NULL,
                end_column INTEGER NOT NULL,
                original_detection TEXT,
                user_label TEXT NOT NULL,
                severity TEXT,
                vulnerability_type TEXT,
                notes TEXT,
                file_path TEXT NOT NULL,
                language TEXT NOT NULL,
                trained INTEGER DEFAULT 0
            )
        ''')
        
        # Index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_trained ON feedback(trained)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_code_hash ON feedback(code_hash)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)
        ''')
        
        conn.commit()
        conn.close()
        print(f"✓ Feedback database initialized at: {self.db_path}")
    
    def add_feedback(self, feedback: UserFeedback) -> int:
        """
        Add a new feedback entry.
        
        Args:
            feedback: UserFeedback object
        
        Returns:
            ID of the new feedback entry
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO feedback (
                timestamp, feedback_type, code_snippet, code_hash,
                start_line, end_line, start_column, end_column,
                original_detection, user_label, severity, vulnerability_type,
                notes, file_path, language, trained
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feedback.timestamp,
            feedback.feedback_type,
            feedback.code_snippet,
            feedback.code_hash,
            feedback.start_line,
            feedback.end_line,
            feedback.start_column,
            feedback.end_column,
            feedback.original_detection,
            feedback.user_label,
            feedback.severity,
            feedback.vulnerability_type,
            feedback.notes,
            feedback.file_path,
            feedback.language,
            0
        ))
        
        feedback_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✓ Feedback #{feedback_id} saved: {feedback.feedback_type} - {feedback.user_label}")
        return feedback_id
    
    def get_untrained_feedback(self) -> List[UserFeedback]:
        """Get all feedback entries that haven't been used for training."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM feedback WHERE trained = 0')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_feedback(row) for row in rows]
    
    def get_all_feedback(self) -> List[UserFeedback]:
        """Get all feedback entries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM feedback ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_feedback(row) for row in rows]
    
    def mark_as_trained(self, feedback_ids: List[int]):
        """Mark feedback entries as used for training."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(feedback_ids))
        cursor.execute(f'''
            UPDATE feedback SET trained = 1 WHERE id IN ({placeholders})
        ''', feedback_ids)
        
        conn.commit()
        conn.close()
        print(f"✓ Marked {len(feedback_ids)} feedback entries as trained")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the feedback database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total count
        cursor.execute('SELECT COUNT(*) FROM feedback')
        total = cursor.fetchone()[0]
        
        # By type
        cursor.execute('''
            SELECT feedback_type, COUNT(*) FROM feedback GROUP BY feedback_type
        ''')
        by_type = dict(cursor.fetchall())
        
        # Untrained count
        cursor.execute('SELECT COUNT(*) FROM feedback WHERE trained = 0')
        untrained = cursor.fetchone()[0]
        
        # By label
        cursor.execute('''
            SELECT user_label, COUNT(*) FROM feedback GROUP BY user_label
        ''')
        by_label = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "total": total,
            "by_type": by_type,
            "untrained": untrained,
            "by_label": by_label,
            "db_path": self.db_path
        }
    
    def check_existing(self, code_hash: str) -> Optional[UserFeedback]:
        """Check if feedback already exists for this code snippet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM feedback WHERE code_hash = ? LIMIT 1', (code_hash,))
        row = cursor.fetchone()
        conn.close()
        
        return self._row_to_feedback(row) if row else None
    
    def delete_feedback(self, feedback_id: int) -> bool:
        """Delete a feedback entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM feedback WHERE id = ?', (feedback_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return deleted
    
    def _row_to_feedback(self, row: sqlite3.Row) -> UserFeedback:
        """Convert a database row to a UserFeedback object."""
        return UserFeedback(
            id=row['id'],
            timestamp=row['timestamp'],
            feedback_type=row['feedback_type'],
            code_snippet=row['code_snippet'],
            code_hash=row['code_hash'],
            start_line=row['start_line'],
            end_line=row['end_line'],
            start_column=row['start_column'],
            end_column=row['end_column'],
            original_detection=row['original_detection'],
            user_label=row['user_label'],
            severity=row['severity'],
            vulnerability_type=row['vulnerability_type'],
            notes=row['notes'],
            file_path=row['file_path'],
            language=row['language'],
            trained=bool(row['trained'])
        )


def compute_code_hash(code: str) -> str:
    """Compute a hash for a code snippet."""
    normalized = code.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


# Global database instance
_feedback_db: Optional[FeedbackDatabase] = None


def get_feedback_db() -> FeedbackDatabase:
    """Get or create the global feedback database instance."""
    global _feedback_db
    if _feedback_db is None:
        _feedback_db = FeedbackDatabase()
    return _feedback_db


if __name__ == "__main__":
    # Test the feedback database
    print("Testing Feedback Database...")
    
    db = FeedbackDatabase()
    
    # Add test feedback
    test_feedback = UserFeedback(
        id=None,
        timestamp=datetime.now().isoformat(),
        feedback_type=FeedbackType.FALSE_POSITIVE.value,
        code_snippet='password = os.environ.get("DB_PASSWORD")',
        code_hash=compute_code_hash('password = os.environ.get("DB_PASSWORD")'),
        start_line=10,
        end_line=10,
        start_column=0,
        end_column=42,
        original_detection="Broken Authentication",
        user_label="secure",
        severity=None,
        vulnerability_type=None,
        notes="This is using environment variable, not hardcoded",
        file_path="/project/config.py",
        language="python"
    )
    
    feedback_id = db.add_feedback(test_feedback)
    print(f"Added feedback with ID: {feedback_id}")
    
    # Get stats
    stats = db.get_stats()
    print(f"\nDatabase stats: {json.dumps(stats, indent=2)}")
    
    # Get untrained feedback
    untrained = db.get_untrained_feedback()
    print(f"\nUntrained feedback count: {len(untrained)}")
    
    print("\n✅ Feedback database test complete!")
