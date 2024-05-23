import sqlite3

def connect_to_db(db_name="budget_tracker.db"):
    """
    Connect to the SQLite database. If the database does not exist, it will be created.
    
    Args:
        db_name (str): The name of the database file.
    
    Returns:
        sqlite3.Connection: Connection object to the SQLite database, or None if the connection fails.
    """
    try:
        db = sqlite3.connect(db_name)
        return db
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables(db):
    """
    Create tables in the budget_tracker.db database to store expenses, income, categories, and budgets.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    # Create a cursor object to execute SQL commands
    cursor = db.cursor()

    # Create table for expense categories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Create table for income categories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # Create table for expenses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id)
        )
    ''')

    # Create table for income
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES income_categories (id)
        )
    ''')

    # Create table for budgets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id)
        )
    ''')

    # Commit changes to the database
    db.commit()


def main():
    # Connect to the database
    db = connect_to_db()

    # Create tables if they don't exist
    if db:
        create_tables(db)
        print("Tables created successfully.")
    else:
        print("Failed to connect to the database.")

main()