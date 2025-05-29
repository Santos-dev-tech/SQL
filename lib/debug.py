# lib/debug.py
import ipdb
from lib.db.connection import get_connection, close_connection, create_tables
from lib.db.seed import seed_data
from lib.models.author import Author
from lib.models.magazine import Magazine
from lib.models.article import Article
import os

def setup_db_for_debug():
    # Remove existing database file if it exists, for a clean slate
    if os.path.exists('articles.db'):
        os.remove('articles.db')
        print("Removed existing database: articles.db")
    create_tables()
    seed_data()
    print("Database setup complete for debugging.")

if __name__ == "__main__":
    setup_db_for_debug()
    print("Entering debugger. Type 'q' to quit, 'n' for next, 'c' to continue.")
    print("\nAvailable objects:")
    print("- Author, Magazine, Article classes")
    print("- Example data is seeded (e.g., Author.get_all(), Magazine.get_all())")

    # Example usage for debugging
    author1 = Author.find_by_name("John Doe")
    magazine1 = Magazine.find_by_name("Tech Today")
    article1 = Article.find_by_title("The Future of AI")

    ipdb.set_trace()