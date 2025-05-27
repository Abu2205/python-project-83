import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def get_connection():
    try:
        return psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise

def add_url(url):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (url,))
            existing_url = cur.fetchone()
            if existing_url:
                return existing_url[0], False
            created_at = datetime.utcnow()
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id",
                (url, created_at)
            )
            url_id = cur.fetchone()[0]
            return url_id, True

def get_url_by_id(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls WHERE id = %s", (url_id,))
            return cur.fetchone()

def get_url_by_name(name):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM urls WHERE name = %s", (name,))
            return cur.fetchone()

def get_all_urls():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT urls.*, (
                    SELECT created_at 
                    FROM url_checks 
                    WHERE url_checks.url_id = urls.id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ) as last_check, (
                    SELECT status_code 
                    FROM url_checks 
                    WHERE url_checks.url_id = urls.id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ) as last_status_code
                FROM urls 
                ORDER BY created_at DESC
            """)
            return cur.fetchall()

def add_url_check(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            created_at = datetime.utcnow()
            cur.execute(
                "INSERT INTO url_checks (url_id, created_at) VALUES (%s, %s) RETURNING id",
                (url_id, created_at)
            )
            check_id = cur.fetchone()[0]
            return check_id

def get_checks_by_url_id(url_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM url_checks WHERE url_id = %s ORDER BY created_at DESC", (url_id,))
            return cur.fetchall()

def update_check_status(check_id, status_code, h1=None, title=None, description=None):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE url_checks SET status_code = %s, h1 = %s, title = %s, description = %s WHERE id = %s",
                (status_code, h1, title, description, check_id)
            )
            conn.commit()