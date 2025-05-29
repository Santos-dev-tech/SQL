# lib/db/connection.py
import sqlite3

DATABASE_NAME = 'articles.db'

def get_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def close_connection(conn):
    """Closes the database connection."""
    if conn:
        conn.close()

def create_tables():
    """Creates tables based on the schema.sql file."""
    conn = get_connection()
    try:
        with open('lib/db/schema.sql', 'r') as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
        conn.commit()
        print("Database tables created successfully.")
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        close_connection(conn)