import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'chatbot.db')

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            intent TEXT,
            confidence REAL,
            context TEXT,
            sentiment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            log_id INTEGER,
            rating INTEGER CHECK(rating IN (1, -1)),
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (log_id) REFERENCES conversation_logs (id)
        )
    ''')
    conn.commit()
    conn.close()

def log_interaction(session_id, user_message, bot_response, intent, confidence, context, sentiment):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversation_logs (session_id, user_message, bot_response, intent, confidence, context, sentiment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (session_id, user_message, bot_response, intent, float(confidence), context, sentiment))
    conn.commit()
    log_id = cursor.lastrowid
    conn.close()
    return log_id

def log_feedback(session_id, log_id, rating, comment=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_feedback (session_id, log_id, rating, comment)
        VALUES (?, ?, ?, ?)
    ''', (session_id, log_id, rating, comment))
    conn.commit()
    conn.close()

def get_analytics():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total interactions
    cursor.execute('SELECT COUNT(*) as total FROM conversation_logs')
    total_messages = cursor.fetchone()['total']
    
    # Distinct sessions
    cursor.execute('SELECT COUNT(DISTINCT session_id) as total_sessions FROM conversation_logs')
    total_sessions = cursor.fetchone()['total_sessions']
    
    # Intent distribution
    cursor.execute('''
        SELECT intent, COUNT(*) as count 
        FROM conversation_logs 
        GROUP BY intent 
        ORDER BY count DESC 
        LIMIT 10
    ''')
    intents_breakdown = [dict(row) for row in cursor.fetchall()]
    
    # Recent logs
    cursor.execute('''
        SELECT id, session_id, user_message, bot_response, intent, confidence, sentiment, timestamp 
        FROM conversation_logs 
        ORDER BY id DESC 
        LIMIT 15
    ''')
    recent_logs = [dict(row) for row in cursor.fetchall()]

    # Feedback ratings
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive,
            SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as negative
        FROM user_feedback
    ''')
    feedback_row = cursor.fetchone()
    feedback_stats = {
        'positive': feedback_row['positive'] or 0,
        'negative': feedback_row['negative'] or 0
    }
    
    conn.close()
    return {
        'total_messages': total_messages,
        'total_sessions': total_sessions,
        'intents_breakdown': intents_breakdown,
        'recent_logs': recent_logs,
        'feedback_stats': feedback_stats
    }

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at", DB_PATH)
