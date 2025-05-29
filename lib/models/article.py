# lib/models/article.py
from lib.db.connection import get_connection, close_connection
from lib.models.author import Author # For relationships/type hinting
from lib.models.magazine import Magazine # For relationships/type hinting

class Article:
    def __init__(self, title, author_id, magazine_id, id=None):
        self._title = title
        self._author_id = author_id
        self._magazine_id = magazine_id
        self._id = id
        self._validate_title()

    def __repr__(self):
        return f"<Article {self.id}: {self.title}>"

    def _validate_title(self):
        if not isinstance(self._title, str) or not (0 < len(self._title) <= 50):
            raise ValueError("Title must be a string between 1 and 50 characters.")

    @property
    def id(self):
        return self._id

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not isinstance(value, str) or not (0 < len(value) <= 50):
            raise ValueError("Title must be a string between 1 and 50 characters.")
        self._title = value
        self.update()

    @property
    def author_id(self):
        return self._author_id

    @property
    def magazine_id(self):
        return self._magazine_id

    @classmethod
    def _create_instance(cls, row):
        """Helper to create an Article instance from a database row."""
        return cls(row["title"], row["author_id"], row["magazine_id"], row["id"])

    @classmethod
    def create(cls, title, author_id, magazine_id):
        """Inserts a new article into the database."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)",
                (title, author_id, magazine_id)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return cls(title, author_id, magazine_id, new_id)
        except Exception as e:
            conn.rollback()
            print(f"Error creating article: {e}")
            return None
        finally:
            close_connection(conn)

    def save(self):
        """Saves the current article instance to the database (for new articles)."""
        if self.id is None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)",
                    (self.title, self.author_id, self.magazine_id)
                )
                conn.commit()
                self._id = cursor.lastrowid
            except Exception as e:
                conn.rollback()
                print(f"Error saving article: {e}")
            finally:
                close_connection(conn)
        else:
            self.update()

    def update(self):
        """Updates an existing article in the database."""
        if self.id is not None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE articles SET title = ?, author_id = ?, magazine_id = ? WHERE id = ?",
                    (self.title, self.author_id, self.magazine_id, self.id)
                )
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"Error updating article: {e}")
            finally:
                close_connection(conn)

    def delete(self):
        """Deletes the article from the database."""
        if self.id is not None:
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM articles WHERE id = ?", (self.id,))
                conn.commit()
                self._id = None
            except Exception as e:
                conn.rollback()
                print(f"Error deleting article: {e}")
            finally:
                close_connection(conn)

    @classmethod
    def find_by_id(cls, article_id):
        """Finds an article by its ID."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            return cls._create_instance(row) if row else None
        finally:
            close_connection(conn)

    @classmethod
    def find_by_title(cls, title):
        """Finds an article by its title."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM articles WHERE title = ?", (title,))
            row = cursor.fetchone()
            return cls._create_instance(row) if row else None
        finally:
            close_connection(conn)

    @classmethod
    def get_all(cls):
        """Returns a list of all articles."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM articles")
            rows = cursor.fetchall()
            return [cls._create_instance(row) for row in rows]
        finally:
            close_connection(conn)

    # Relationship Methods

    def author(self):
        """Returns the Author object for this article."""
        from lib.models.author import Author # Deferred import
        return Author.find_by_id(self.author_id)

    def magazine(self):
        """Returns the Magazine object for this article."""
        from lib.models.magazine import Magazine # Deferred import
        return Magazine.find_by_id(self.magazine_id)

    @classmethod
    def count_articles_in_magazines(cls):
        """Counts the number of articles in each magazine."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT m.name, COUNT(a.id) AS article_count
                FROM magazines m
                LEFT JOIN articles a ON m.id = a.magazine_id
                GROUP BY m.id
                ORDER BY article_count DESC
            """)
            rows = cursor.fetchall()
            return {row["name"]: row["article_count"] for row in rows}
        finally:
            close_connection(conn)

    @classmethod
    def find_author_with_most_articles(cls):
        """Finds the author who has written the most articles."""
        from lib.models.author import Author # Deferred import
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT a.*, COUNT(art.id) AS article_count
                FROM authors a
                JOIN articles art ON a.id = art.author_id
                GROUP BY a.id
                ORDER BY article_count DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return Author._create_instance(row) if row else None
        finally:
            close_connection(conn)

    @classmethod
    def magazines_with_multiple_authors(cls):
        """Finds magazines with articles by at least 2 different authors."""
        from lib.models.magazine import Magazine # Deferred import
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT m.*
                FROM magazines m
                JOIN articles a ON m.id = a.magazine_id
                GROUP BY m.id
                HAVING COUNT(DISTINCT a.author_id) >= 2
            """)
            rows = cursor.fetchall()
            return [Magazine._create_instance(row) for row in rows]
        finally:
            close_connection(conn)