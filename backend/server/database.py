import sqlite3
from datetime import datetime

DB_NAME = 'research_history.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_research(title: str, content: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO research_history (title, content) VALUES (?, ?)', (title, content))
    conn.commit()
    conn.close()

def get_all_research():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM research_history ORDER BY created_at DESC')
    results = c.fetchall()
    conn.close()
    return results

def get_research_by_id(research_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM research_history WHERE id = ?', (research_id,))
    result = c.fetchone()
    conn.close()
    return result 