import os
import sqlite3
from datetime import datetime

class Database:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', None)
        
        if self.database_url:
            self.mode = 'postgresql'
            import psycopg2
            import urllib.parse
            result = urllib.parse.urlparse(self.database_url)
            self.conn_params = {
                'host': result.hostname,
                'database': result.path[1:],
                'user': result.username,
                'password': result.password,
                'port': result.port
            }
        else:
            self.mode = 'sqlite'
            self.db_path = 'events.db'
        
        self.init_db()
    
    def get_connection(self):
        if self.mode == 'postgresql':
            import psycopg2
            return psycopg2.connect(**self.conn_params)
        else:
            return sqlite3.connect(self.db_path)
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.mode == 'postgresql':
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    event_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS guests (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    table_number TEXT NOT NULL,
                    status TEXT DEFAULT 'absent',
                    checkin_time TEXT,
                    notes TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_requests (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    table_number TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    details TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS music_requests (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    table_number TEXT,
                    song_name TEXT,
                    artist TEXT,
                    genre TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    event_id INTEGER NOT NULL,
                    table_number TEXT,
                    author_name TEXT DEFAULT 'Invité',
                    content_type TEXT NOT NULL,
                    text_content TEXT,
                    media_url TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
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
                    notes TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS service_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    table_number TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    details TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS music_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    table_number TEXT,
                    song_name TEXT,
                    artist TEXT,
                    genre TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    table_number TEXT,
                    author_name TEXT DEFAULT 'Invité',
                    content_type TEXT NOT NULL,
                    text_content TEXT,
                    media_url TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def _fetch_all(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.mode == 'postgresql':
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result = [dict(zip(columns, row)) for row in rows]
        else:
            conn.row_factory = sqlite3.Row
            cursor.execute(query, params)
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
        cursor.close()
        conn.close()
        return result
    
    def _fetch_one(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.mode == 'postgresql':
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                cursor.close()
                conn.close()
                return dict(zip(columns, row))
        else:
            conn.row_factory = sqlite3.Row
            cursor.execute(query, params)
            row = cursor.fetchone()
            if row:
                cursor.close()
                conn.close()
                return dict(row)
        cursor.close()
        conn.close()
        return None
    
    def _execute(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        cursor.close()
        conn.close()
    
    # ============ ÉVÉNEMENTS ============
    
    def create_event(self, name, event_date):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.mode == 'postgresql':
            cursor.execute("INSERT INTO events (name, event_date) VALUES (%s, %s) RETURNING id", (name, event_date))
            event_id = cursor.fetchone()[0]
        else:
            cursor.execute("INSERT INTO events (name, event_date) VALUES (?, ?)", (name, event_date))
            event_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return event_id
    
    def get_event(self, event_id):
        if self.mode == 'postgresql':
            return self._fetch_one("SELECT * FROM events WHERE id = %s", (event_id,))
        return self._fetch_one("SELECT * FROM events WHERE id = ?", (event_id,))
    
    def get_all_events(self):
        return self._fetch_all("SELECT * FROM events ORDER BY created_at DESC")
    
    def delete_event(self, event_id):
        if self.mode == 'postgresql':
            self._execute("DELETE FROM guests WHERE event_id = %s", (event_id,))
            self._execute("DELETE FROM service_requests WHERE event_id = %s", (event_id,))
            self._execute("DELETE FROM music_requests WHERE event_id = %s", (event_id,))
            self._execute("DELETE FROM posts WHERE event_id = %s", (event_id,))
            self._execute("DELETE FROM events WHERE id = %s", (event_id,))
        else:
            self._execute("DELETE FROM guests WHERE event_id = ?", (event_id,))
            self._execute("DELETE FROM service_requests WHERE event_id = ?", (event_id,))
            self._execute("DELETE FROM music_requests WHERE event_id = ?", (event_id,))
            self._execute("DELETE FROM posts WHERE event_id = ?", (event_id,))
            self._execute("DELETE FROM events WHERE id = ?", (event_id,))
        return True
    
    # ============ INVITÉS ============
    
    def add_guests_batch(self, event_id, guests_list):
        conn = self.get_connection()
        cursor = conn.cursor()
        for guest in guests_list:
            if self.mode == 'postgresql':
                cursor.execute(
                    "INSERT INTO guests (event_id, first_name, last_name, table_number) VALUES (%s, %s, %s, %s)",
                    (event_id, guest['first_name'], guest['last_name'], guest['table_number'])
                )
            else:
                cursor.execute(
                    "INSERT INTO guests (event_id, first_name, last_name, table_number) VALUES (?, ?, ?, ?)",
                    (event_id, guest['first_name'], guest['last_name'], guest['table_number'])
                )
        conn.commit()
        cursor.close()
        conn.close()
    
    def add_guest(self, event_id, first_name, last_name, table_number, notes=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.mode == 'postgresql':
            cursor.execute(
                "INSERT INTO guests (event_id, first_name, last_name, table_number, notes) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (event_id, first_name, last_name, table_number, notes)
            )
            guest_id = cursor.fetchone()[0]
        else:
            cursor.execute(
                "INSERT INTO guests (event_id, first_name, last_name, table_number, notes) VALUES (?, ?, ?, ?, ?)",
                (event_id, first_name, last_name, table_number, notes)
            )
            guest_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return guest_id
    
    def get_guests(self, event_id):
        if self.mode == 'postgresql':
            return self._fetch_all("SELECT * FROM guests WHERE event_id = %s ORDER BY last_name, first_name", (event_id,))
        return self._fetch_all("SELECT * FROM guests WHERE event_id = ? ORDER BY last_name, first_name", (event_id,))
    
    def checkin_guest(self, guest_id):
        if self.mode == 'postgresql':
            self._execute("UPDATE guests SET status = 'present', checkin_time = %s WHERE id = %s", (datetime.now().isoformat(), guest_id))
        else:
            self._execute("UPDATE guests SET status = 'present', checkin_time = ? WHERE id = ?", (datetime.now().isoformat(), guest_id))
        return True
    
    def search_guests(self, event_id, query):
        if self.mode == 'postgresql':
            return self._fetch_all(
                "SELECT * FROM guests WHERE event_id = %s AND (first_name ILIKE %s OR last_name ILIKE %s) ORDER BY last_name, first_name LIMIT 20",
                (event_id, f"%{query}%", f"%{query}%")
            )
        return self._fetch_all(
            "SELECT * FROM guests WHERE event_id = ? AND (first_name LIKE ? OR last_name LIKE ?) ORDER BY last_name, first_name LIMIT 20",
            (event_id, f"%{query}%", f"%{query}%")
        )
    
    def get_stats(self, event_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.mode == 'postgresql':
            cursor.execute("SELECT COUNT(*) FROM guests WHERE event_id = %s", (event_id,))
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM guests WHERE event_id = %s AND status = 'present'", (event_id,))
            present = cursor.fetchone()[0]
            cursor.execute(
                "SELECT table_number, COUNT(*) as total, SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as presents FROM guests WHERE event_id = %s GROUP BY table_number ORDER BY table_number",
                (event_id,)
            )
            tables = cursor.fetchall()
        else:
            cursor.execute("SELECT COUNT(*) FROM guests WHERE event_id = ?", (event_id,))
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM guests WHERE event_id = ? AND status = 'present'", (event_id,))
            present = cursor.fetchone()[0]
            cursor.execute(
                "SELECT table_number, COUNT(*) as total, SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as presents FROM guests WHERE event_id = ? GROUP BY table_number ORDER BY table_number",
                (event_id,)
            )
            tables = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': round((present / total * 100) if total > 0 else 0, 1),
            'tables': [{'number': t[0], 'total': t[1], 'present': t[2]} for t in tables]
        }
    
    def get_last_checkins(self, event_id, limit=5):
        if self.mode == 'postgresql':
            return self._fetch_all(
                "SELECT * FROM guests WHERE event_id = %s AND status = 'present' ORDER BY checkin_time DESC LIMIT %s",
                (event_id, limit)
            )
        return self._fetch_all(
            "SELECT * FROM guests WHERE event_id = ? AND status = 'present' ORDER BY checkin_time DESC LIMIT ?",
            (event_id, limit)
        )
    
    # ============ POSTS ============
    
    def add_post(self, event_id, table_number, author_name, content_type, text_content="", media_url=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.mode == 'postgresql':
            cursor.execute(
                "INSERT INTO posts (event_id, table_number, author_name, content_type, text_content, media_url) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (event_id, table_number, author_name, content_type, text_content, media_url)
            )
            post_id = cursor.fetchone()[0]
        else:
            cursor.execute(
                "INSERT INTO posts (event_id, table_number, author_name, content_type, text_content, media_url) VALUES (?, ?, ?, ?, ?, ?)",
                (event_id, table_number, author_name, content_type, text_content, media_url)
            )
            post_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return post_id
    
    def get_posts(self, event_id, status=None):
        if self.mode == 'postgresql':
            if status:
                return self._fetch_all("SELECT * FROM posts WHERE event_id = %s AND status = %s ORDER BY created_at DESC", (event_id, status))
            return self._fetch_all("SELECT * FROM posts WHERE event_id = %s ORDER BY created_at DESC", (event_id,))
        else:
            if status:
                return self._fetch_all("SELECT * FROM posts WHERE event_id = ? AND status = ? ORDER BY created_at DESC", (event_id, status))
            return self._fetch_all("SELECT * FROM posts WHERE event_id = ? ORDER BY created_at DESC", (event_id,))
    
    def approve_post(self, post_id):
        if self.mode == 'postgresql':
            self._execute("UPDATE posts SET status = 'approved' WHERE id = %s", (post_id,))
        else:
            self._execute("UPDATE posts SET status = 'approved' WHERE id = ?", (post_id,))
        return True
    
    def reject_post(self, post_id):
        if self.mode == 'postgresql':
            self._execute("UPDATE posts SET status = 'rejected' WHERE id = %s", (post_id,))
        else:
            self._execute("UPDATE posts SET status = 'rejected' WHERE id = ?", (post_id,))
        return True
    
    # ============ SERVICE DE TABLE ============
    
    def add_service_request(self, event_id, table_number, request_type, details=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.mode == 'postgresql':
            cursor.execute(
                "INSERT INTO service_requests (event_id, table_number, request_type, details) VALUES (%s, %s, %s, %s) RETURNING id",
                (event_id, table_number, request_type, details)
            )
            request_id = cursor.fetchone()[0]
        else:
            cursor.execute(
                "INSERT INTO service_requests (event_id, table_number, request_type, details) VALUES (?, ?, ?, ?)",
                (event_id, table_number, request_type, details)
            )
            request_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return request_id
    
    def get_service_requests(self, event_id, status=None):
        if self.mode == 'postgresql':
            if status:
                return self._fetch_all("SELECT * FROM service_requests WHERE event_id = %s AND status = %s ORDER BY created_at DESC", (event_id, status))
            return self._fetch_all("SELECT * FROM service_requests WHERE event_id = %s ORDER BY created_at DESC", (event_id,))
        else:
            if status:
                return self._fetch_all("SELECT * FROM service_requests WHERE event_id = ? AND status = ? ORDER BY created_at DESC", (event_id, status))
            return self._fetch_all("SELECT * FROM service_requests WHERE event_id = ? ORDER BY created_at DESC", (event_id,))
    
    def resolve_service_request(self, request_id):
        if self.mode == 'postgresql':
            self._execute("UPDATE service_requests SET status = 'resolved' WHERE id = %s", (request_id,))
        else:
            self._execute("UPDATE service_requests SET status = 'resolved' WHERE id = ?", (request_id,))
        return True
    
    # ============ JUKEBOX ============
    
    def add_music_request(self, event_id, table_number, song_name, artist="", genre=""):
        conn = self.get_connection()
        cursor = conn.cursor()
        if self.mode == 'postgresql':
            cursor.execute(
                "INSERT INTO music_requests (event_id, table_number, song_name, artist, genre) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (event_id, table_number, song_name, artist, genre)
            )
            request_id = cursor.fetchone()[0]
        else:
            cursor.execute(
                "INSERT INTO music_requests (event_id, table_number, song_name, artist, genre) VALUES (?, ?, ?, ?, ?)",
                (event_id, table_number, song_name, artist, genre)
            )
            request_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return request_id
    
    def get_music_requests(self, event_id, status=None):
        if self.mode == 'postgresql':
            if status:
                return self._fetch_all("SELECT * FROM music_requests WHERE event_id = %s AND status = %s ORDER BY created_at DESC", (event_id, status))
            return self._fetch_all("SELECT * FROM music_requests WHERE event_id = %s ORDER BY created_at DESC", (event_id,))
        else:
            if status:
                return self._fetch_all("SELECT * FROM music_requests WHERE event_id = ? AND status = ? ORDER BY created_at DESC", (event_id, status))
            return self._fetch_all("SELECT * FROM music_requests WHERE event_id = ? ORDER BY created_at DESC", (event_id,))