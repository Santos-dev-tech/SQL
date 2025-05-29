# lib/db/seed.py
from lib.db.connection import get_connection, close_connection
from lib.models.author import Author
from lib.models.magazine import Magazine
from lib.models.article import Article

def seed_data():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Clear existing data (optional, useful for clean re-seeding)
        cursor.execute("DELETE FROM articles")
        cursor.execute("DELETE FROM authors")
        cursor.execute("DELETE FROM magazines")
        conn.commit()

        # Create Authors
        author1 = Author.create("John Doe")
        author2 = Author.create("Jane Smith")
        author3 = Author.create("Alice Wonderland")
        author4 = Author.create("Bob The Builder")

        # Create Magazines
        magazine1 = Magazine.create("Tech Today", "Technology")
        magazine2 = Magazine.create("Fashion Weekly", "Fashion")
        magazine3 = Magazine.create("Science Now", "Science")
        magazine4 = Magazine.create("Gaming Monthly", "Gaming")

        # Create Articles
        Article.create("The Future of AI", author1.id, magazine1.id)
        Article.create("Summer Fashion Trends", author2.id, magazine2.id)
        Article.create("Quantum Computing Explained", author1.id, magazine3.id)
        Article.create("New Trends in Gaming", author3.id, magazine4.id)
        Article.create("AI Ethics", author1.id, magazine1.id)
        Article.create("Sustainable Fashion", author2.id, magazine2.id)
        Article.create("Dark Matter Mysteries", author3.id, magazine3.id)
        Article.create("Retro Gaming Revival", author4.id, magazine4.id)
        Article.create("Cybersecurity Basics", author1.id, magazine1.id)
        Article.create("Mobile Gaming Evolution", author4.id, magazine4.id)

        print("Sample data seeded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error seeding data: {e}")
    finally:
        close_connection(conn)

if __name__ == "__main__":
    # This block allows you to run seed.py directly for testing
    seed_data()