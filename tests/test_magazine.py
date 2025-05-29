# tests/test_magazine.py
import pytest
import sqlite3
from lib.models.author import Author
from lib.models.article import Article
from lib.models.magazine import Magazine

# Re-use fixtures from test_author.py or create separate ones if needed
# For simplicity, assuming these fixtures are available or redefined.

@pytest.fixture
def db_connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Create tables here again, or refactor into a shared fixture
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

@pytest.fixture(autouse=True)
def mock_get_connection(monkeypatch, db_connection):
    def mock_conn():
        return db_connection
    monkeypatch.setattr("lib.db.connection.get_connection", mock_conn)
    monkeypatch.setattr("lib.db.connection.close_connection", lambda conn: None)

@pytest.fixture
def seed_test_data(db_connection):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO authors (name) VALUES (?)", ("John Doe",))
    cursor.execute("INSERT INTO authors (name) VALUES (?)", ("Jane Smith",))
    cursor.execute("INSERT INTO authors (name) VALUES (?)", ("Alice Wonderland",))
    author1_id = 1
    author2_id = 2
    author3_id = 3

    cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", ("Tech Today", "Technology"))
    cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", ("Fashion Weekly", "Fashion"))
    cursor.execute("INSERT INTO magazines (name, category) VALUES (?, ?)", ("Science Now", "Science"))
    magazine1_id = 1
    magazine2_id = 2
    magazine3_id = 3

    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("The Future of AI", author1_id, magazine1_id))
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("Summer Fashion Trends", author2_id, magazine2_id))
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("Quantum Computing Explained", author1_id, magazine1_id)) # John Doe, Tech Today
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("New Research", author3_id, magazine1_id)) # Alice Wonderland, Tech Today
    cursor.execute("INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)", ("Another Science Article", author3_id, magazine3_id))
    db_connection.commit()


# --- Magazine Tests ---

def test_magazine_creation(db_connection):
    magazine = Magazine("New Mag", "New Cat")
    magazine.save()
    assert magazine.id is not None
    assert magazine.name == "New Mag"
    assert magazine.category == "New Cat"

    retrieved_magazine = Magazine.find_by_id(magazine.id)
    assert retrieved_magazine.name == "New Mag"
    assert retrieved_magazine.category == "New Cat"

def test_magazine_name_category_validation():
    with pytest.raises(ValueError):
        Magazine("a", "Category") # Name too short
    with pytest.raises(ValueError):
        Magazine("TooLongNameForMagazine", "Category") # Name too long
    with pytest.raises(ValueError):
        Magazine("ValidName", "") # Category too short
    with pytest.raises(ValueError):
        Magazine("ValidName", "a" * 21) # Category too long
    with pytest.raises(ValueError):
        Magazine(123, "Category") # Invalid name type

def test_magazine_articles_relationship(db_connection, seed_test_data):
    tech_today = Magazine.find_by_name("Tech Today")
    articles = tech_today.articles()
    assert len(articles) == 3 # "The Future of AI", "Quantum Computing Explained", "New Research"
    titles = {a.title for a in articles}
    assert "The Future of AI" in titles
    assert "Quantum Computing Explained" in titles
    assert "New Research" in titles
    assert all(isinstance(a, Article) for a in articles)

def test_magazine_contributors_relationship(db_connection, seed_test_data):
    tech_today = Magazine.find_by_name("Tech Today")
    contributors = tech_today.contributors()
    assert len(contributors) == 2 # John Doe, Alice Wonderland
    names = {c.name for c in contributors}
    assert "John Doe" in names
    assert "Alice Wonderland" in names
    assert all(isinstance(c, Author) for c in contributors)

def test_magazine_article_titles(db_connection, seed_test_data):
    tech_today = Magazine.find_by_name("Tech Today")
    titles = tech_today.article_titles()
    assert len(titles) == 3
    assert "The Future of AI" in titles
    assert "Quantum Computing Explained" in titles
    assert "New Research" in titles

def test_magazine_contributing_authors(db_connection, seed_test_data):
    # John Doe has 2 articles in Tech Today in this seeded data
    tech_today = Magazine.find_by_name("Tech Today")
    contributing_authors = tech_today.contributing_authors()
    assert len(contributing_authors) == 0 # Based on current seed, no one has > 2

    # Add more articles for John Doe to make him a contributing author
    john = Author.find_by_name("John Doe")
    tech_today.articles # Force load to avoid stale data
    john.add_article(tech_today, "Advanced AI Concepts")
    john.add_article(tech_today, "Robotics and AI")

    contributing_authors_after = tech_today.contributing_authors()
    assert len(contributing_authors_after) == 1
    assert contributing_authors_after[0].name == "John Doe"


def test_magazine_top_publisher(db_connection, seed_test_data):
    # Initially, Tech Today has 3 articles, others have 1 or 2
    top_mag = Magazine.top_publisher()
    assert top_mag.name == "Tech Today"
    assert top_mag.category == "Technology"

    # Add more articles to Fashion Weekly to make it the top publisher
    jane = Author.find_by_name("Jane Smith")
    fashion_weekly = Magazine.find_by_name("Fashion Weekly")
    jane.add_article(fashion_weekly, "New Dress Styles")
    jane.add_article(fashion_weekly, "Winter Fashion Lookbook")
    jane.add_article(fashion_weekly, "Spring Collection Preview") # Now Jane has 4 articles in Fashion Weekly

    top_mag_after = Magazine.top_publisher()
    assert top_mag_after.name == "Fashion Weekly"