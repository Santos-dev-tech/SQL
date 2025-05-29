# lib/models/magazine.py
from lib.db.connection import get_connection, close_connection
from lib.models.article import Article # For relationships/type hinting
from lib.models.author import Author # For relationships/type hinting

class Magazine:
    def __init__(self, name, category, id=None):
        self._name = name
        self._category = category
        self._id = id
        self._validate_name_category()

    def __repr__(self):
        return f"<Magazine {self.id}: {self.name} ({self.category})>"

    def _validate_name_category(self):
        if not isinstance(self._name, str) or not (2 <= len(self._name) <= 16):
            raise ValueError("Name must be a string between 2 and 16 characters.")
        if not isinstance(self._category, str) or not (0 < len(self._category) <= 20):
            raise ValueError("Category must be a string between 1 and 20 characters.")

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) or not (2 <= len(value) <= 16):
            raise ValueError("Name must be a string between 2 and 16 characters.")
        self._name = value
        self.update()

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if not isinstance(value, str) or not (0 < len(value) <= 20):
            raise ValueError("Category must be a string between 1 and 20 characters.")
        self._category = value
        self.update()

    @classmethod
    def _create_instance(cls, row):
        """Helper to create a Magazine instance from a database row."""
        return cls(row["name"], row["category"], row["id"])

    @classmethod
    def create(cls, name, category):
        """Inserts a new magazine into the database."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", (name, category))
            conn.commit()
            new_id = cursor.lastrowid
            return cls(name, category, new_id)
        except Exception as e:
            conn.rollback()
            print(f"Error creating magazine: {e}")
            return None
        finally:
            close_connection(conn)

    def save(self):
        """Saves the current magazine instance to the database (for new magazines)."""
        if self.id is None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", (self.name, self.category))
                conn.commit()
                self._id = cursor.lastrowid
            except Exception as e:
                conn.rollback()
                print(f"Error saving magazine: {e}")
            finally:
                close_connection(conn)
        else:
            self.update()

    def update(self):
        """Updates an existing magazine in the database."""
        if self.id is not None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE magazines SET name = ?, category = ? WHERE id = ?", (self.name, self.category, self.id))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Error updating magazine: {e}")
            finally:
                close_connection(conn)

    def delete(self):
        """Deletes the magazine from the database."""
        if self.id is not None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM magazines WHERE id = ?", (self.id,))
                conn.commit()
                self._id = None
            except Exception as e:
                conn.rollback()
                print(f"Error deleting magazine: {e}")
            finally:
                close_connection(conn)

    @classmethod
    def find_by_id(cls, magazine_id):
        """Finds a magazine by its ID."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM magazines WHERE id = ?", (magazine_id,))
            row = cursor.fetchone()
            return cls._create_instance(row) if row else None
        finally:
            close_connection(conn)

    @classmethod
    def find_by_name(cls, name):
        """Finds a magazine by its name."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM magazines WHERE name = ?", (name,))
            row = cursor.fetchone()
            return cls._create_instance(row) if row else None
        finally:
            close_connection(conn)

    @classmethod
    def get_all(cls):
        """Returns a list of all magazines."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM magazines")
            rows = cursor.fetchall()
            return [cls._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    # Relationship Methods

    def articles(self):
        """Returns a list of all articles published in the magazine."""
        from lib.models.article import Article # Deferred import
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM articles
                WHERE magazine_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [Article._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    def contributors(self):
        """Returns a unique list of authors who have written for this magazine."""
        from lib.models.author import Author # Deferred import
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT a.* FROM authors a
                JOIN articles art ON a.id = art.author_id
                WHERE art.magazine_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [Author._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    def article_titles(self):
        """Returns a list of titles of all articles in the magazine."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT title FROM articles
                WHERE magazine_id = ?
            """, (self.id,))
            rows = cursor.fetchall()
            return [row["title"] for row in rows]
        finally:
            close_connection(conn)

    def contributing_authors(self):
        """Returns list of authors with more than 2 articles in the magazine."""
        from lib.models.author import Author # Deferred import
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT a.*, COUNT(art.id) AS article_count
                FROM authors a
                JOIN articles art ON a.id = art.author_id
                WHERE art.magazine_id = ?
                GROUP BY a.id
                HAVING COUNT(art.id) > 2
            """, (self.id,))
            rows = cursor.fetchall()
            return [Author._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    @classmethod
    def top_publisher(cls):
        """Class method to find the magazine with the most articles."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT m.*, COUNT(a.id) AS article_count
                FROM magazines m
                LEFT JOIN articles a ON m.id = a.magazine_id
                GROUP BY m.id
                ORDER BY article_count DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return cls._create_instance(row) if row else None
        finally:
            close_connection(conn)