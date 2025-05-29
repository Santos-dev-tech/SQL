# tests/test_author.py
import pytest
import sqlite3
from lib.models.author import Author
from lib.models.article import Article
from lib.models.magazine import Magazine

# Use an in-memory database for tests
@pytest.fixture
def db_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE magazines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL UNIQUE,
            category VARCHAR(255) NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255) NOT NULL,
            author_id INTEGER NOT NULL,
            magazine_id INTEGER NOT NULL,
            FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
            FOREIGN KEY (magazine_id) REFERENCES magazines(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    yield conn
    conn.close()

# Mock get_connection to use the in-memory db
@pytest.fixture(autouse=True)
def mock_get_connection(monkeypatch, db_connection):
    def mock_conn():
        return db_connection
    monkeypatch.setattr("lib.db.connection.get_connection", mock_conn)
    monkeypatch.setattr("lib.db.connection.close_connection", lambda conn: None) # Do nothing for tests

@pytest.fixture
def seed_test_data(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO authors (name) VALUES (?)", ("John Doe",))
    cursor.execute("INSERT INTO authors (name) VALUES (?)", ("Jane Smith",))
    cursor.execute("INSERT INTO authors (name) VALUES (?)", ("Alice Wonderland",))
    author1_id = cursor.lastrowid - 2
    author2_id = cursor.lastrowid - 1
    author3_id = cursor.lastrowid

    cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", ("Tech Today", "Technology"))
    cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", ("Fashion Weekly", "Fashion"))
    cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", ("Science Now", "Science"))
    magazine1_id = cursor.lastrowid - 2
    magazine2_id = cursor.lastrowid - 1
    magazine3_id = cursor.lastrowid

    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("The Future of AI", author1_id, magazine1_id))
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("Summer Fashion Trends", author2_id, magazine2_id))
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("Quantum Computing Explained", author1_id, magazine3_id))
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("Another AI Article", author1_id, magazine1_id))
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("Yet Another AI Article", author1_id, magazine1_id)) # John Doe has 3 articles in Tech Today
    db_connection.commit()

# --- Author Tests ---

def test_author_creation(db_connection):
    author = Author("Test Author")
    author.save()
    assert author.id is not None
    assert author.name == "Test Author"

    retrieved_author = Author.find_by_id(author.id)
    assert retrieved_author.name == "Test Author"

def test_author_name_validation():
    with pytest.raises(ValueError):
        Author("") # Too short
    with pytest.raises(ValueError):
        Author("a" * 256) # Too long
    with pytest.raises(ValueError):
        Author(123) # Not a string

def test_author_name_update(db_connection, seed_test_data):
    john = Author.find_by_name("John Doe")
    assert john.name == "John Doe"
    john.name = "Jonathan Doe"
    assert john.name == "Jonathan Doe"
    updated_john = Author.find_by_id(john.id)
    assert updated_john.name == "Jonathan Doe"

def test_author_deletion(db_connection, seed_test_data):
    john = Author.find_by_name("John Doe")
    assert john is not None
    john_id = john.id
    john.delete()
    assert Author.find_by_id(john_id) is None
    # Ensure articles by deleted author are also gone (CASCADE)
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles WHERE author_id = ?", (john_id,))
    assert cursor.fetchone()[0] == 0

def test_author_find_by_id_and_name(db_connection, seed_test_data):
    john = Author.find_by_name("John Doe")
    assert john is not None
    assert john.name == "John Doe"
    found_by_id = Author.find_by_id(john.id)
    assert found_by_id.name == "John Doe"
    assert Author.find_by_id(9999) is None
    assert Author.find_by_name("Nonexistent") is None

def test_author_get_all(db_connection, seed_test_data):
    authors = Author.get_all()
    assert len(authors) == 3
    names = {a.name for a in authors}
    assert "John Doe" in names
    assert "Jane Smith" in names
    assert "Alice Wonderland" in names

def test_author_articles_relationship(db_connection, seed_test_data):
    john = Author.find_by_name("John Doe")
    articles = john.articles()
    assert len(articles) == 3 # John Doe has 3 articles in seed data
    titles = {a.title for a in articles}
    assert "The Future of AI" in titles
    assert "Quantum Computing Explained" in titles
    assert "Another AI Article" in titles
    assert all(isinstance(a, Article) for a in articles)

def test_author_magazines_relationship(db_connection, seed_test_data):
    john = Author.find_by_name("John Doe")
    magazines = john.magazines()
    assert len(magazines) == 2 # Tech Today, Science Now
    names = {m.name for m in magazines}
    assert "Tech Today" in names
    assert "Science Now" in names
    assert all(isinstance(m, Magazine) for m in magazines)

def test_author_add_article(db_connection, seed_test_data):
    john = Author.find_by_name("John Doe")
    tech_today = Magazine.find_by_name("Tech Today")

    initial_articles_count = len(john.articles())
    initial_magazine_articles_count = len(tech_today.articles())

    new_article = john.add_article(tech_today, "A Brand New Article")
    assert new_article is not None
    assert new_article.title == "A Brand New Article"
    assert new_article.author_id == john.id
    assert new_article.magazine_id == tech_today.id

    assert len(john.articles()) == initial_articles_count + 1
    assert len(tech_today.articles()) == initial_magazine_articles_count + 1

    with pytest.raises(TypeError):
        john.add_article("not a magazine", "invalid") # Invalid magazine type

def test_author_topic_areas(db_connection, seed_test_data):
    john = Author.find_by_name("John Doe")
    topic_areas = john.topic_areas()
    assert len(topic_areas) == 2
    assert "Technology" in topic_areas
    assert "Science" in topic_areas
    assert "Fashion" not in topic_areas
    assert sorted(topic_areas) == ["Science", "Technology"] # Ensure sorted output