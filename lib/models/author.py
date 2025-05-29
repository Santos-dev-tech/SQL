# lib/models/author.py
from lib.db.connection import get_connection, close_connection
from lib.models.article import Article # Import for type hinting/relationship methods later
from lib.models.magazine import Magazine # Import for type hinting/relationship methods later

class Author:
    def __init__(self, name, id=None):
        if not isinstance(name, str) or not (0 < len(name) <= 255):
            raise ValueError("Name must be a string between 1 and 255 characters.")
        self._name = name
        self._id = id

    def __repr__(self):
        return f"<Author {self.id}: {self.name}>"

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) or not (0 < len(value) <= 255):
            raise ValueError("Name must be a string between 1 and 255 characters.")
        self._name = value
        self.update() # Automatically update in DB if name changes

    @classmethod
    def _create_instance(cls, row):
        """Helper to create an Author instance from a database row."""
        return cls(row["name"], row["id"])

    @classmethod
    def create(cls, name):
        """Inserts a new author into the database."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO authors (name) VALUES (?)", (name,))
            conn.commit()
            new_id = cursor.lastrowid
            return cls(name, new_id)
        except Exception as e:
            conn.rollback()
            print(f"Error creating author: {e}")
            return None
        finally:
            close_connection(conn)

    def save(self):
        """Saves the current author instance to the database (for new authors)."""
        if self.id is None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO authors (name) VALUES (?)", (self.name,))
                conn.commit()
                self._id = cursor.lastrowid
            except Exception as e:
                conn.rollback()
                print(f"Error saving author: {e}")
            finally:
                close_connection(conn)
        else:
            self.update()

    def update(self):
        """Updates an existing author in the database."""
        if self.id is not None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE authors SET name = ? WHERE id = ?", (self.name, self.id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Error updating author: {e}")
            finally:
                close_connection(conn)

    def delete(self):
        """Deletes the author from the database."""
        if self.id is not None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM authors WHERE id = ?", (self.id,))
                conn.commit()
                self._id = None # Invalidate ID after deletion
            except Exception as e:
                conn.rollback()
                print(f"Error deleting author: {e}")
            finally:
                close_connection(conn)

    @classmethod
    def find_by_id(cls, author_id):
        """Finds an author by their ID."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM authors WHERE id = ?", (author_id,))
            row = cursor.fetchone()
            return cls._create_instance(row) if row else None
        finally:
            close_connection(conn)

    @classmethod
    def find_by_name(cls, name):
        """Finds an author by their name."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM authors WHERE name = ?", (name,))
            row = cursor.fetchone()
            return cls._create_instance(row) if row else None
        finally:
            close_connection(conn)

    @classmethod
    def get_all(cls):
        """Returns a list of all authors."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM authors")
            rows = cursor.fetchall()
            return [cls._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    # Relationship Methods

    def articles(self):
        """Returns a list of all articles written by the author."""
        from lib.models.article import Article # Deferred import to avoid circular dependency
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM articles
                WHERE author_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [Article._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    def magazines(self):
        """Returns a unique list of magazines the author has contributed to."""
        from lib.models.magazine import Magazine # Deferred import
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT m.* FROM magazines m
                JOIN articles a ON m.id = a.magazine_id
                WHERE a.author_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [Magazine._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    def add_article(self, magazine, title):
        """Creates and inserts a new Article into the database for this author."""
        from lib.models.article import Article # Deferred import
        if not isinstance(magazine, Magazine):
            raise TypeError("magazine must be an instance of Magazine.")
        return Article.create(title, self.id, magazine.id)

    def topic_areas(self):
        """Returns a unique list of categories of magazines the author has contributed to."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT m.category FROM magazines m
                JOIN articles a ON m.id = a.magazine_id
                WHERE a.author_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return sorted(list(set([row["category"] for row in rows]))) # Ensure unique and sorted
        finally:
            close_connection(conn)