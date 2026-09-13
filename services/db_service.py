import os
import json
import sqlite3
import pymysql
from dotenv import load_dotenv

load_dotenv()

# MySQL environment details
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "student_workspace")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))

# In-memory storage / SQLite fallback if MySQL is unreachable locally
USE_SQLITE_FALLBACK = False

def get_mysql_connection():
    """
    Attempts to connect to MySQL database using configured environment parameters.
    """
    return pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        port=MYSQL_PORT,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )

def get_sqlite_connection():
    """
    Fallback SQLite database connection for seamless local testing without MySQL dependency.
    """
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/student_workspace.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes database tables. First tries MySQL database setup;
    if connection fails, initializes SQLite fallback automatically.
    """
    global USE_SQLITE_FALLBACK

    # Try MySQL initialization
    try:
        # Connect directly to the existing MySQL database
        conn = get_mysql_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    filename VARCHAR(255),
                    subject VARCHAR(100) DEFAULT 'General',
                    extracted_text LONGTEXT,
                    notes_json JSON,
                    quiz_json JSON,
                    mindmap_markdown LONGTEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.close()
        USE_SQLITE_FALLBACK = False
        print("[DB SERVICE] Successfully connected and initialized MySQL database.")
    except Exception as e:
        print(f"[DB SERVICE WARNING] Could not connect to MySQL ({e}). Using SQLite local database fallback.")
        USE_SQLITE_FALLBACK = True
        conn = get_sqlite_connection()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    subject TEXT DEFAULT 'General',
                    extracted_text TEXT,
                    notes_json TEXT,
                    quiz_json TEXT,
                    mindmap_markdown TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.close()

def save_document(filename, extracted_text, notes_json, quiz_json, mindmap_markdown, subject="General"):
    """
    Inserts a newly processed PDF document record into database using parameterized query.
    
    :return: Inserted document ID
    """
    global USE_SQLITE_FALLBACK

    notes_str = json.dumps(notes_json) if isinstance(notes_json, (list, dict)) else notes_json
    quiz_str = json.dumps(quiz_json) if isinstance(quiz_json, (list, dict)) else quiz_json

    if not USE_SQLITE_FALLBACK:
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO documents (filename, subject, extracted_text, notes_json, quiz_json, mindmap_markdown)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (filename, subject, extracted_text, notes_str, quiz_str, mindmap_markdown))
                doc_id = cursor.lastrowid
            conn.close()
            return doc_id
        except Exception as err:
            print(f"[DB SERVICE ERROR] MySQL save failed ({err}), using SQLite fallback.")
            USE_SQLITE_FALLBACK = True

    # SQLite fallback insert
    conn = get_sqlite_connection()
    with conn:
        cursor = conn.cursor()
        sql = """
            INSERT INTO documents (filename, subject, extracted_text, notes_json, quiz_json, mindmap_markdown)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (filename, subject, extracted_text, notes_str, quiz_str, mindmap_markdown))
        doc_id = cursor.lastrowid
    conn.close()
    return doc_id

def get_document_by_id(doc_id=None):
    """
    Retrieves document record by ID. If doc_id is None, retrieves the most recent document.
    
    :param doc_id: Document ID integer or None
    :return: Dictionary containing document fields or None
    """
    global USE_SQLITE_FALLBACK

    if not USE_SQLITE_FALLBACK:
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                if doc_id:
                    cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
                else:
                    cursor.execute("SELECT * FROM documents ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
            conn.close()
            if row:
                # Ensure JSON fields are parsed if returned as strings
                if isinstance(row.get('notes_json'), str):
                    row['notes_json'] = json.loads(row['notes_json'])
                if isinstance(row.get('quiz_json'), str):
                    row['quiz_json'] = json.loads(row['quiz_json'])
                return row
        except Exception as err:
            print(f"[DB SERVICE ERROR] MySQL fetch failed ({err}), switching to SQLite fallback.")
            USE_SQLITE_FALLBACK = True

    # SQLite fetch
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    if doc_id:
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    else:
        cursor.execute("SELECT * FROM documents ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if row:
        row_dict = dict(row)
        if isinstance(row_dict.get('notes_json'), str):
            row_dict['notes_json'] = json.loads(row_dict['notes_json'])
        if isinstance(row_dict.get('quiz_json'), str):
            row_dict['quiz_json'] = json.loads(row_dict['quiz_json'])
        return row_dict
    return None