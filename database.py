import sqlite3
import json
from datetime import datetime
from pathlib import Path

class Database:
    def __init__(self, db_path="events.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialise la base de données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    table_number TEXT NOT NULL,
                    status TEXT DEFAULT 'absent',
                    checkin_time TEXT,
                    notes TEXT,
                    FOREIGN KEY (event_id) REFERENCES events (id)
                )
            ''')
            
            conn.commit()
    
    def create_event(self, name, event_date):
        """Crée un nouvel événement"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (name, event_date) VALUES (?, ?)",
                (name, event_date)
            )
            conn.commit()
            return cursor.lastrowid
    
    def add_guests_batch(self, event_id, guests_list):
        """Ajoute plusieurs invités en une fois"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for guest in guests_list:
                cursor.execute(
                    """INSERT INTO guests 
                    (event_id, first_name, last_name, table_number) 
                    VALUES (?, ?, ?, ?)""",
                    (event_id, guest['first_name'], 
                     guest['last_name'], guest['table_number'])
                )
            conn.commit()
    
    def add_guest(self, event_id, first_name, last_name, table_number, notes=""):
        """Ajoute un seul invité"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO guests 
                (event_id, first_name, last_name, table_number, notes) 
                VALUES (?, ?, ?, ?, ?)""",
                (event_id, first_name, last_name, table_number, notes)
            )
            conn.commit()
            return cursor.lastrowid
    
    def get_event(self, event_id):
        """Récupère un événement"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            return cursor.fetchone()
    
    def get_all_events(self):
        """Récupère tous les événements"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM events ORDER BY created_at DESC"
            )
            return cursor.fetchall()
    
    def get_guests(self, event_id):
        """Récupère tous les invités d'un événement"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM guests WHERE event_id = ? ORDER BY last_name, first_name",
                (event_id,)
            )
            return cursor.fetchall()
    
    def checkin_guest(self, guest_id):
        """Check-in d'un invité"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE guests 
                SET status = 'present', 
                    checkin_time = ? 
                WHERE id = ?""",
                (datetime.now().isoformat(), guest_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def search_guests(self, event_id, query):
        """Recherche rapide d'invités"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM guests 
                WHERE event_id = ? 
                AND (first_name LIKE ? OR last_name LIKE ?)
                ORDER BY last_name, first_name
                LIMIT 20""",
                (event_id, f"%{query}%", f"%{query}%")
            )
            return cursor.fetchall()
    
    def get_stats(self, event_id):
        """Statistiques de l'événement"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) FROM guests WHERE event_id = ?",
                (event_id,)
            )
            total = cursor.fetchone()[0]
            
            cursor.execute(
                "SELECT COUNT(*) FROM guests WHERE event_id = ? AND status = 'present'",
                (event_id,)
            )
            present = cursor.fetchone()[0]
            
            cursor.execute(
                """SELECT table_number, 
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as presents
                FROM guests 
                WHERE event_id = ? 
                GROUP BY table_number
                ORDER BY table_number""",
                (event_id,)
            )
            tables = cursor.fetchall()
            
            return {
                'total': total,
                'present': present,
                'absent': total - present,
                'percentage': round((present / total * 100) if total > 0 else 0, 1),
                'tables': [
                    {
                        'number': t[0],
                        'total': t[1],
                        'present': t[2]
                    } for t in tables
                ]
            }
    
    def get_last_checkins(self, event_id, limit=5):
        """Derniers check-ins"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM guests 
                WHERE event_id = ? AND status = 'present'
                ORDER BY checkin_time DESC
                LIMIT ?""",
                (event_id, limit)
            )
            return cursor.fetchall()
    
    def delete_event(self, event_id):
        """Supprime un événement et tous ses invités"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM guests WHERE event_id = ?", (event_id,))
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
            return cursor.rowcount > 0