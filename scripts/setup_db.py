# scripts/setup_db.py
import os
from lib.db.connection import create_tables, DATABASE_NAME
from lib.db.seed import seed_data

def main():
    # Remove existing database file if it exists
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Removed existing database: {DATABASE_NAME}")

    create_tables()
    seed_data()
    print("Database setup complete with seeded data.")

if __name__ == "__main__":
    main()