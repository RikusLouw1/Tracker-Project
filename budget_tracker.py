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

# Define functions for menu options
def add_expense(db):
    pass

def view_expenses(db):
    pass

def view_expenses_by_category(db):
    pass

def add_income(db):
    pass

def view_income(db):
    pass

def view_income_by_category(db):
    pass

def set_budget(db):
    pass

def view_budget(db):
    pass

def set_goals(db):
    pass

def view_goals_progress(db):
    pass

def main_menu():
    """Display the main menu options."""
    print("1. Add expense")
    print("2. View expenses")
    print("3. View expenses by category")
    print("4. Add income")
    print("5. View income")
    print("6. View income by category")
    print("7. Set budget for a category")
    print("8. View budget for a category")
    print("9. Set financial goals")
    print("10. View progress towards financial goals")
    print("11. Quit")

def main():
    # Connect to the database
    db = connect_to_db()

    # Create tables if they don't exist
    if db:
        create_tables(db)
        print("Tables created successfully.")
    else:
        print("Failed to connect to the database.")

    while True:
        # Display main menu
        main_menu()
        choice = input("Enter your choice: ")
        
        # Perform actions based on user choice
        if choice == '1':
            add_expense(db)
        elif choice == '2':
            view_expenses(db)
        elif choice == '3':
            view_expenses_by_category(db)
        elif choice == '4':
            add_income(db)
        elif choice == '5':
            view_income(db)
        elif choice == '6':
            view_income_by_category(db)
        elif choice == '7':
            set_budget(db)
        elif choice == '8':
            view_budget(db)
        elif choice == '9':
            set_goals(db)
        elif choice == '10':
            view_goals_progress(db)
        elif choice == '11':
            print("\nGoodbye!\n")
            break
        else:
            print("Invalid choice. Please try again.")

main()