# scripts/run_queries.py
import os
from lib.db.connection import DATABASE_NAME
from lib.models.author import Author
from lib.models.magazine import Magazine
from lib.models.article import Article
from scripts.setup_db import main as setup_db_script # Import the setup script main function

def run_example_queries():
    print("--- Running Example Queries ---")

    # 1. Get all authors
    print("\n1. All Authors:")
    authors = Author.get_all()
    for author in authors:
        print(author)

    # 2. Get all magazines
    print("\n2. All Magazines:")
    magazines = Magazine.get_all()
    for mag in magazines:
        print(mag)

    # 3. Get all articles
    print("\n3. All Articles:")
    articles = Article.get_all()
    for art in articles:
        print(art)

    # 4. Find an author by name and get their articles and magazines
    print("\n4. John Doe's Articles and Magazines:")
    john = Author.find_by_name("John Doe")
    if john:
        print(f"Author: {john.name}")
        print("Articles:")
        for article in john.articles():
            print(f"  - {article.title} (Magazine: {article.magazine().name})")
        print("Magazines contributed to:")
        for mag in john.magazines():
            print(f"  - {mag.name} ({mag.category})")
        print("Topic Areas:")
        print(f"  - {john.topic_areas()}")

    # 5. Find a magazine by name and get its articles and contributors
    print("\n5. Tech Today's Articles and Contributors:")
    tech_today = Magazine.find_by_name("Tech Today")
    if tech_today:
        print(f"Magazine: {tech_today.name}")
        print("Articles:")
        for article_title in tech_today.article_titles():
            print(f"  - {article_title}")
        print("Contributors:")
        for contributor in tech_today.contributors():
            print(f"  - {contributor.name}")
        print("Authors with > 2 articles:")
        for heavy_contributor in tech_today.contributing_authors():
            print(f"  - {heavy_contributor.name}")

    # 6. Count articles in each magazine
    print("\n6. Article Count per Magazine:")
    article_counts = Article.count_articles_in_magazines()
    for name, count in article_counts.items():
        print(f"  - {name}: {count} articles")

    # 7. Find author with most articles
    print("\n7. Author with Most Articles:")
    most_articles_author = Article.find_author_with_most_articles()
    if most_articles_author:
        print(f"  - {most_articles_author.name}")

    # 8. Magazines with articles by at least 2 different authors
    print("\n8. Magazines with Articles by at least 2 different Authors:")
    multi_author_mags = Article.magazines_with_multiple_authors()
    for mag in multi_author_mags:
        print(f"  - {mag.name}")

    # 9. Test transaction handling (adding author and articles)
    print("\n9. Testing Transaction Handling (Adding 'New Author' with articles):")
    conn = Article.get_connection() # Use any model's get_connection
    try:
        conn.execute("BEGIN TRANSACTION")
        cursor = conn.cursor()

        # Insert New Author
        cursor.execute("INSERT INTO authors (name) VALUES (?)", ("New Author",))
        new_author_id = cursor.lastrowid
        print(f"  - Created New Author with ID: {new_author_id}")

        # Insert Articles for New Author
        # Using existing magazine IDs from our seed data
        magazine1_id = Magazine.find_by_name("Tech Today").id
        magazine2_id = Magazine.find_by_name("Fashion Weekly").id

        cursor.execute(
            "INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)",
            ("New Article 1 by New Author", new_author_id, magazine1_id)
        )
        cursor.execute(
            "INSERT INTO articles (title, author_id, magazine_id) VALUES (?, ?, ?)",
            ("New Article 2 by New Author", new_author_id, magazine2_id)
        )
        print("  - Inserted two articles for New Author.")

        conn.commit()
        print("  - Transaction committed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"  - Transaction failed: {e}. Rolled back.")
    finally:
        Article.close_connection(conn) # Use any model's close_connection

    # Verify the new author and articles
    new_author = Author.find_by_name("New Author")
    if new_author:
        print(f"\nVerification: New Author '{new_author.name}' articles:")
        for article in new_author.articles():
            print(f"  - {article.title}")
    else:
        print("\nVerification: New Author not found (transaction might have failed).")

    # 10. Bonus: Top Publisher
    print("\n10. Top Publisher:")
    top_mag = Magazine.top_publisher()
    if top_mag:
        print(f"  - The magazine with the most articles is: {top_mag.name}")
    else:
        print("  - No top publisher found.")

    print("\n--- Example Queries Complete ---")

if __name__ == "__main__":
    # Ensure database is set up and seeded before running queries
    print("Setting up database for example queries...")
    setup_db_script() # Call the main function from setup_db.py
    run_example_queries()