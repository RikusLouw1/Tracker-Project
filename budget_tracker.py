import datetime
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

def insert_preset_data(db):

    cursor = db.cursor()

    # Ensure the mtb category exists
    cursor.execute('''
        INSERT OR IGNORE INTO expense_categories (name) VALUES (?)
    ''', ('mtb',))
    db.commit()

    # Retrieve the category ID for mtb
    cursor.execute('''
        SELECT id FROM expense_categories WHERE name = ?
    ''', ('mtb',))
    mtb_category_id = cursor.fetchone()[0]

    expenses = [
        ("2024-02-12", mtb_category_id, "bought mtb", 12000),
        ("2024-03-01", mtb_category_id, "shifter parts", 500),
        ("2024-04-05", mtb_category_id, "drivetrain parts", 3500),
        ("2024-05-03", mtb_category_id, "brake bleeding kit", 400)
    ]

    cursor.executemany('''
        INSERT INTO expenses (date, category_id, description, amount)
        VALUES (?, ?, ?, ?)
    ''', expenses)
    db.commit()

# Define functions for menu options
def add_expense(db):
    """
    Add a new expense to the database.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    while True:
        # Prompt user for expense details
        date = input("Enter the date of the expense (YYYY-MM-DD): ").lower()
        
        # Validate date format
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD "
                  "format.")
            continue
        
        category_name = input("Enter the category name of the expense: "
                              ).lower()
        description = input("Enter a description of the expense: ").lower()

        # Prompt user for the amount of the expense
        while True:
            amount_input = input("Enter the amount of the expense: ").strip()
            if amount_input == "":
                print("Amount cannot be empty. Please enter a valid amount.")
                continue
            try:
                amount = float(amount_input)
                break
            except ValueError:
                print("Invalid amount format. Please enter a valid number.")

        try:
            # Create a cursor object to execute SQL commands
            cursor = db.cursor()

            # Check if the category already exists
            cursor.execute('''
                SELECT id FROM expense_categories WHERE name = ?
            ''', (category_name,))
            category = cursor.fetchone()
            
            # If category does not exist, create it
            if category is None:
                cursor.execute('''
                    INSERT INTO expense_categories (name) VALUES (?)
                ''', (category_name,))
                db.commit()

                # Get the new category id
                category_id = cursor.lastrowid
            else:
                # Use existing category id
                category_id = category[0]

            # Retrieve the latest ID from the expenses table
            cursor.execute("SELECT MAX(id) FROM expenses")
            latest_id = cursor.fetchone()[0]

            # Increment the latest ID by 1 to generate a new ID
            new_id = latest_id + 1 if latest_id is not None else 1

            # Insert the new expense into the 'expenses' table
            cursor.execute('''
                INSERT INTO expenses (id, date, category_id, description, 
                           amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (new_id, date, category_id, description, amount))

            # Commit the transaction
            db.commit()
                        
            # Prompt user for confirmation
            while True:
                confirm = input("Do you confirm to add this expense? "
                                "(yes/no): ").lower()
                if confirm == 'yes':
                    print("Expense added successfully.")
                    return
                elif confirm == 'no':
                    cursor.execute("DELETE FROM expenses WHERE id=?", 
                                   (new_id,))
                    db.commit()
                    print("Expense not added.")
                    return  # Return to main menu
                else:
                    print("Invalid choice. Please enter 'yes' or 'no'.")

        except sqlite3.Error as e:
            # Print error message if insertion fails
            print(f"Error adding expense: {e}")

def view_expenses(db):
    """
    View all expenses, update an expense, or delete an expense.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Fetch all expenses from the database
    cursor.execute('''
        SELECT expenses.id, expenses.date, expense_categories.name, 
                   expenses.description, expenses.amount
        FROM expenses
        JOIN expense_categories ON expenses.category_id = expense_categories.id
    ''')
    expenses = cursor.fetchall()

    if not expenses:
        print("No expenses found.\n")
        return

    # Display all expenses
    print("Expenses:")
    for expense in expenses:
        print(f"ID: {expense[0]}, Date: {expense[1]}, Category: {expense[2]}, "
              f"Description: {expense[3]}, Amount: {expense[4]}\n")

    while True:
        action = input("Enter the ID of the expense to update/delete, or "
                       "'back' to return to the main menu: ").strip().lower()
        
        if action == 'back':
            return

        try:
            expense_id = int(action)
        except ValueError:
            print("Invalid ID. Please enter a valid expense ID.\n")
            continue

        # Check if the entered ID is valid
        cursor.execute('''
            SELECT id FROM expenses WHERE id = ?
        ''', (expense_id,))
        if not cursor.fetchone():
            print("Expense ID not found. Please enter a valid expense ID.\n")
            continue

        # Ask user for the action to perform on the selected expense
        update_delete = input("Would you like to update or delete this "
                              "expense? (update/delete): \n").strip().lower()
        
        if update_delete == 'delete':
            try:
                cursor.execute('''
                    DELETE FROM expenses WHERE id = ?
                ''', (expense_id,))
                db.commit()
                print("Expense deleted successfully.\n")
            except sqlite3.Error as e:
                print(f"Error deleting expense: {e}\n")
            return

        elif update_delete == 'update':
            # Update expense details
            new_date = input("Enter the new date of the expense (YYYY-MM-DD), "
                             "or press enter to keep the current date: \n"
                             ).strip().lower()
            if new_date:
                try:
                    datetime.datetime.strptime(new_date, "%Y-%m-%d")
                except ValueError:
                    print("Invalid date format. Please enter the date in "
                          "YYYY-MM-DD format.\n")
                    continue

            new_category = input("Enter the new category of the expense, or "
                                 "press enter to keep the current category: \n"
                                 ).strip().lower()
            new_description = input("Enter the new description of the "
                                    "expense, or press enter to keep the "
                                    "current description: \n").strip().lower()
            new_amount_input = input("Enter the new amount of the expense, or "
                                     "press enter to keep the current "
                                     "amount: \n"
                                     ).strip()
            if new_amount_input:
                try:
                    new_amount = float(new_amount_input)
                except ValueError:
                    print("Invalid amount format. Please enter a valid "
                          "number.\n")
                    continue

            try:
                # Update the expense details in the database
                if new_date:
                    cursor.execute('''
                        UPDATE expenses SET date = ? WHERE id = ?
                    ''', (new_date, expense_id))
                
                if new_category:
                    cursor.execute('''
                        SELECT id FROM expense_categories WHERE name = ?
                    ''', (new_category,))
                    category = cursor.fetchone()
                    
                    if category is None:
                        cursor.execute('''
                            INSERT INTO expense_categories (name) VALUES (?)
                        ''', (new_category,))
                        db.commit()
                        category_id = cursor.lastrowid
                    else:
                        category_id = category[0]
                    
                    cursor.execute('''
                        UPDATE expenses SET category_id = ? WHERE id = ?
                    ''', (category_id, expense_id))

                if new_description:
                    cursor.execute('''
                        UPDATE expenses SET description = ? WHERE id = ?
                    ''', (new_description, expense_id))
                
                if new_amount_input:
                    cursor.execute('''
                        UPDATE expenses SET amount = ? WHERE id = ?
                    ''', (new_amount, expense_id))

                db.commit()
                print("Expense updated successfully.\n")
            except sqlite3.Error as e:
                print(f"Error updating expense: {e}\n")
            return

        else:
            print("Invalid choice. Please enter 'update' or 'delete'.\n")


def view_expenses_by_category(db):
    pass

def add_income(db):
    """
    Add a new income to the database.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    while True:
        # Prompt user for income details
        date = input("Enter the date of the income (YYYY-MM-DD): ").lower()
        
        # Validate date format
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD "
                  "format.\n")
            continue
        
        category_name = input("Enter the category name of the income: "
                              ).lower()
        description = input("Enter a description of the income: ").lower()

        # Prompt user for the amount of the income
        while True:
            amount_input = input("Enter the amount of the income: ").strip()
            if amount_input == "":
                print("Amount cannot be empty. Please enter a valid amount.\n")
                continue
            try:
                amount = float(amount_input)
                break
            except ValueError:
                print("Invalid amount format. Please enter a valid number.\n")

        try:
            # Create a cursor object to execute SQL commands
            cursor = db.cursor()

            # Check if the category already exists
            cursor.execute('''
                SELECT id FROM income_categories WHERE name = ?
            ''', (category_name,))
            category = cursor.fetchone()
            
            # If category does not exist, create it
            if category is None:
                cursor.execute('''
                    INSERT INTO income_categories (name) VALUES (?)
                ''', (category_name,))
                db.commit()

                # Get the new category id
                category_id = cursor.lastrowid
            else:
                # Use existing category id
                category_id = category[0]

            # Retrieve the latest ID from the income table
            cursor.execute("SELECT MAX(id) FROM income")
            latest_id = cursor.fetchone()[0]

            # Increment the latest ID by 1 to generate a new ID
            new_id = latest_id + 1 if latest_id is not None else 1

            # Insert the new income into the 'income' table
            cursor.execute('''
                INSERT INTO income (id, date, category_id, description, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (new_id, date, category_id, description, amount))

            # Commit the transaction
            db.commit()
                        
            # Prompt user for confirmation
            while True:
                confirm = input("Do you confirm to add this income? (yes/no): "
                                ).lower()
                if confirm == 'yes':
                    print("Income added successfully.\n")
                    return
                elif confirm == 'no':
                    cursor.execute("DELETE FROM income WHERE id=?", (new_id,))
                    db.commit()
                    print("Income not added.\n")
                    return  # Return to main menu
                else:
                    print("Invalid choice. Please enter 'yes' or 'no'.\n")

        except sqlite3.Error as e:
            # Print error message if insertion fails
            print(f"Error adding income: {e}\n")

def view_income(db):
    """
    View all incomes, update an income, or delete an income.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Fetch all incomes from the database
    cursor.execute('''
        SELECT income.id, income.date, income_categories.name, 
                   income.description, income.amount
        FROM income
        JOIN income_categories ON income.category_id = income_categories.id
    ''')
    incomes = cursor.fetchall()

    if not incomes:
        print("No income found.\n")
        return

    # Display all income
    print("\nIncomes:\n")
    for income in incomes:
        print(f"ID: {income[0]}, Date: {income[1]}, Category: {income[2]}, "
              f"Description: {income[3]}, Amount: {income[4]}\n")

    while True:
        action = input("Enter the ID of the income to update/delete, or 'back'"
                       " to return to the main menu: ").strip().lower()
        
        if action == 'back':
            return

        try:
            income_id = int(action)
        except ValueError:
            print("Invalid ID. Please enter a valid income ID.\n")
            continue

        # Check if the entered ID is valid
        cursor.execute('''
            SELECT id FROM income WHERE id = ?
        ''', (income_id,))
        if not cursor.fetchone():
            print("Income ID not found. Please enter a valid income ID.\n")
            continue

        # Ask user for the action to perform on the selected income
        update_delete = input("Would you like to update or delete this "
                              "income? (update/delete): ").strip().lower()
        
        if update_delete == 'delete':
            try:
                cursor.execute('''
                    DELETE FROM income WHERE id = ?
                ''', (income_id,))
                db.commit()
                print("Income deleted successfully.\n")
            except sqlite3.Error as e:
                print(f"Error deleting income: {e}\n")
            return

        elif update_delete == 'update':
            # Update income details
            new_date = input("Enter the new date of the income (YYYY-MM-DD), "
                             "or press enter to keep the current date: "
                             ).strip().lower()
            if new_date:
                try:
                    datetime.datetime.strptime(new_date, "%Y-%m-%d")
                except ValueError:
                    print("Invalid date format. Please enter the date in "
                          "YYYY-MM-DD format.\n")
                    continue

            new_category = input("Enter the new category of the income, or "
                                 "press enter to keep the current category: "
                                 "\n").strip().lower()
            new_description = input("Enter the new description of the income, "
                                    "or press enter to keep the current "
                                    "description: \n").strip().lower()
            new_amount_input = input("Enter the new amount of the income, or "
                                     "press enter to keep the current amount: "
                                     "\n").strip()
            if new_amount_input:
                try:
                    new_amount = float(new_amount_input)
                except ValueError:
                    print("Invalid amount format. Please enter a valid "
                          "number.\n")
                    continue

            try:
                # Update the income details in the database
                if new_date:
                    cursor.execute('''
                        UPDATE income SET date = ? WHERE id = ?
                    ''', (new_date, income_id))
                
                if new_category:
                    cursor.execute('''
                        SELECT id FROM income_categories WHERE name = ?
                    ''', (new_category,))
                    category = cursor.fetchone()
                    
                    if category is None:
                        cursor.execute('''
                            INSERT INTO income_categories (name) VALUES (?)
                        ''', (new_category,))
                        db.commit()
                        category_id = cursor.lastrowid
                    else:
                        category_id = category[0]
                    
                    cursor.execute('''
                        UPDATE income SET category_id = ? WHERE id = ?
                    ''', (category_id, income_id))

                if new_description:
                    cursor.execute('''
                        UPDATE income SET description = ? WHERE id = ?
                    ''', (new_description, income_id))
                
                if new_amount_input:
                    cursor.execute('''
                        UPDATE income SET amount = ? WHERE id = ?
                    ''', (new_amount, income_id))

                db.commit()
                print("Income updated successfully.\n")
            except sqlite3.Error as e:
                print(f"Error updating income: {e}\n")
            return

        else:
            print("Invalid choice. Please enter 'update' or 'delete'.\n")


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
        # insert_preset_data(db)

        print("Tables created and preset data inserted successfully.")
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