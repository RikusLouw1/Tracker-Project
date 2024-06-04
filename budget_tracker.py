import datetime
import sqlite3

def connect_to_db(db_name="budget_tracker.db"):
    """
    Connect to the SQLite database. If the database does not exist, it will be 
    created.
    
    Args:
        db_name (str): The name of the database file.
    
    Returns:
        sqlite3.Connection: Connection object to the SQLite database, or None 
        if the connection fails.
    """
    try:
        db = sqlite3.connect(db_name)
        return db
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def create_tables(db):
    """
    Create tables in the budget_tracker.db database to store expenses, income, 
    categories, and budgets.

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
            name TEXT NOT NULL UNIQUE,
            budget_limit REAL
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

    # Create table for financial goals
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_amount REAL NOT NULL,
            target_date TEXT NOT NULL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES expense_categories(id)
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
                    print("\nExpense added successfully.\n")
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

    # Display all expenses and calculate total amount
    total_amount = 0
    print("\nExpenses:\n")
    for expense in expenses:
        print(f"ID: {expense[0]}, Date: {expense[1]}, Category: {expense[2]}, "
              f"Description: {expense[3]}, Amount: {expense[4]}\n")
        total_amount += expense[4]

    print(f"Total Amount: {total_amount}\n")

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
        update_delete = input("\nWould you like to update or delete this "
                              "expense? (update/delete): \n").strip().lower()
        
        if update_delete == 'delete':
            try:
                cursor.execute('''
                    DELETE FROM expenses WHERE id = ?
                ''', (expense_id,))
                db.commit()
                print("\nExpense deleted successfully.\n")
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
    """
    View all expenses by category, update a category name or delete a category 
    and all associated expenses.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Fetch all expense categories from the database
    cursor.execute('SELECT id, name FROM expense_categories')
    categories = cursor.fetchall()

    if not categories:
        print("No expense categories found.\n")
        return

    # Display all categories
    print("Expense Categories:\n")
    for category in categories:
        print(f"ID: {category[0]}, Name: {category[1]}\n")

    while True:
        action = input("Enter the ID of the category to view/update/delete, "
                       "or 'back' to return to the main menu: "
                       ).strip().lower()
        
        if action == 'back':
            # Check for categories with no associated expenses and delete them
            cursor.execute('''
                DELETE FROM expense_categories 
                WHERE id NOT IN (SELECT DISTINCT category_id FROM expenses)
            ''')
            db.commit()
            return

        try:
            category_id = int(action)
        except ValueError:
            print("Invalid ID. Please enter a valid category ID.\n")
            continue

        # Check if the entered ID is valid
        cursor.execute('SELECT id FROM expense_categories WHERE id = ?', 
                       (category_id,))
        if not cursor.fetchone():
            print("Category ID not found. Please enter a valid category ID.\n")
            continue

        # Fetch all expenses associated with the selected category
        cursor.execute('''
            SELECT expenses.id, expenses.date, expense_categories.name, 
                   expenses.description, expenses.amount
            FROM expenses
            JOIN expense_categories ON expenses.category_id = 
                       expense_categories.id
            WHERE expense_categories.id = ?
        ''', (category_id,))
        expenses = cursor.fetchall()

        if not expenses:
            print(f"No expenses found for category ID {category_id}.\n")
        else:
            total_amount = 0
            print(f"Expenses for Category ID {category_id}:\n")
            for expense in expenses:
                print(f"ID: {expense[0]}, Date: {expense[1]}, "
                      f"Category: {expense[2]}, Description: {expense[3]}, "
                      f"Amount: {expense[4]}\n")
                total_amount += expense[4]
            print(f"Total Amount for Category ID {category_id}: {total_amount}"
                  "\n")

        # Ask user for the action to perform on the selected category
        update_delete = input("Would you like to update or delete this "
                              "category? (update/delete/back): "
                              ).strip().lower()
        
        if update_delete == 'delete':
            try:
                # Delete all expenses associated with the category
                cursor.execute('DELETE FROM expenses WHERE category_id = ?', 
                               (category_id,))
                # Delete the category itself
                cursor.execute('DELETE FROM expense_categories WHERE id = ?', 
                               (category_id,))
                db.commit()
                print("Category and all associated expenses deleted "
                      "successfully.\n")
            except sqlite3.Error as e:
                print(f"Error deleting category: {e}\n")
            return

        elif update_delete == 'update':
            new_name = input("Enter the new name for the category, or press "
                             "enter to keep the current name: ").strip()
            
            if new_name:
                try:
                    # Update the category name in the database
                    cursor.execute('UPDATE expense_categories SET name = ? '
                                   'WHERE id = ?', (new_name, category_id))
                    db.commit()
                    print("Category name updated successfully.\n")
                except sqlite3.Error as e:
                    print(f"Error updating category name: {e}\n")
                return
            
        elif update_delete == 'back':
            continue

        else:
            print("Invalid choice. Please enter 'update' or 'delete'.\n")

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
                    print("\nIncome added successfully.\n")
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

    # Display all income and calculate total amount
    total_amount = 0
    print("\nIncomes:\n")
    for income in incomes:
        print(f"ID: {income[0]}, Date: {income[1]}, Category: {income[2]}, "
              f"Description: {income[3]}, Amount: {income[4]}\n")
        total_amount += income[4]

    print(f"Total Amount: {total_amount}\n")

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
    """
    View all incomes by category, update a category name or delete a category
    and all associated incomes.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Fetch all income categories from the database
    cursor.execute('SELECT id, name FROM income_categories')
    categories = cursor.fetchall()

    if not categories:
        print("No income categories found.\n")
        return

    # Display all categories
    print("Income Categories:\n")
    for category in categories:
        print(f"ID: {category[0]}, Name: {category[1]}\n")

    while True:
        action = input("Enter the ID of the category to view/update/delete, "
                       "or 'back' to return to the main menu: ").strip().lower()

        if action == 'back':
            # Check for categories with no associated incomes and delete them
            cursor.execute('''
                DELETE FROM income_categories
                WHERE id NOT IN (SELECT DISTINCT category_id FROM income)
            ''')
            db.commit()
            return

        try:
            category_id = int(action)
        except ValueError:
            print("Invalid ID. Please enter a valid category ID.\n")
            continue

        # Check if the entered ID is valid
        cursor.execute('SELECT id FROM income_categories WHERE id = ?', 
                       (category_id,))
        if not cursor.fetchone():
            print("Category ID not found. Please enter a valid category ID.\n")
            continue

        # Fetch all incomes associated with the selected category
        cursor.execute('''
            SELECT income.id, income.date, income_categories.name,
                   income.description, income.amount
            FROM income
            JOIN income_categories ON income.category_id = income_categories.id
            WHERE income_categories.id = ?
        ''', (category_id,))
        incomes = cursor.fetchall()

        if not incomes:
            print(f"No incomes found for category ID {category_id}.\n")
        else:
            total_amount = 0
            print(f"Incomes for Category ID {category_id}:\n")
            for income in incomes:
                print(f"ID: {income[0]}, Date: {income[1]}, "
                      f"Category: {income[2]}, Description: {income[3]}, "
                      f"Amount: {income[4]}\n")
                total_amount += income[4]
            print(f"Total Amount for Category ID {category_id}: "
                  f"{total_amount}\n")

        # Ask user for the action to perform on the selected category
        update_delete = input("Would you like to update or delete this "
                              "category? (update/delete/back): "
                              ).strip().lower()

        if update_delete == 'delete':
            try:
                # Delete all incomes associated with the category
                cursor.execute('DELETE FROM income WHERE category_id = ?', 
                               (category_id,))
                # Delete the category itself
                cursor.execute('DELETE FROM income_categories WHERE id = ?', 
                               (category_id,))
                db.commit()
                print("Category and all associated incomes deleted "
                      "successfully.\n")
            except sqlite3.Error as e:
                print(f"Error deleting category: {e}\n")
            return

        elif update_delete == 'update':
            new_name = input("Enter the new name for the category, or press "
                             "enter to keep the current name: ").strip()

            if new_name:
                try:
                    # Update the category name in the database
                    cursor.execute('UPDATE income_categories SET name = ? '
                                   'WHERE id = ?', (new_name, category_id))
                    db.commit()
                    print("Category name updated successfully.\n")
                except sqlite3.Error as e:
                    print(f"Error updating category name: {e}\n")
                return
            
        elif update_delete == 'back':
            continue

        else:
            print("Invalid choice. Please enter 'update' or 'delete'.\n")

def set_budget(db):
    """
    Set a budget limit for a specific expense category.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Fetch expense categories from the database
    cursor.execute('SELECT id, name FROM expense_categories')
    categories = cursor.fetchall()

    if not categories:
        print("No expense categories found.\n")
        return

    # Display available categories
    print("Available Expense Categories:")
    for category in categories:
        print(f"ID: {category[0]}, Name: {category[1]}")

    # Prompt user to select a category
    while True:
        try:
            category_id = int(input("\nEnter the ID of the category to set the budget for: ").strip())
            break
        except ValueError:
            print("Invalid input. Please enter a valid category ID.\n")

    # Check if the entered category ID exists
    if category_id not in [cat[0] for cat in categories]:
        print("Invalid category ID. Please select a valid category.\n")
        return

    # Fetch the name of the selected category
    category_name = [cat[1] for cat in categories if cat[0] == category_id][0]

    # Prompt user to enter the budget limit
    while True:
        budget_limit_input = input(f"Enter the budget limit for '{category_name}': ").strip()
        try:
            budget_limit = float(budget_limit_input)
            if budget_limit <= 0:
                raise ValueError("Budget limit must be a positive number.")
            break
        except ValueError as ve:
            print(f"Invalid input: {ve}\n")

    try:
        # Update the budget limit for the category in the database
        cursor.execute('''
            UPDATE expense_categories
            SET budget_limit = ?
            WHERE id = ?
        ''', (budget_limit, category_id))
        db.commit()
        print(f"Budget limit for '{category_name}' set successfully.\n")
    except sqlite3.Error as e:
        print(f"Error setting budget limit: {e}\n")

def view_budget(db):
    """
    View the set budget, actual expenses, and remaining budget for a specific category.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Fetch all expense categories from the database
    cursor.execute('SELECT id, name FROM expense_categories')
    categories = cursor.fetchall()

    if not categories:
        print("No expense categories found.")
        return

    print("Expense Categories:\n")
    for category in categories:
        print(f"ID: {category[0]}, Name: {category[1]}")

    while True:
        category_id_input = input("\nEnter the ID of the category to view the budget, or 'back' to return to the main menu: ").strip().lower()
        
        if category_id_input == 'back':
            return

        try:
            category_id = int(category_id_input)
        except ValueError:
            print("Invalid ID. Please enter a valid category ID.")
            continue

        # Check if the entered ID is valid
        valid_category_ids = [category[0] for category in categories]
        if category_id not in valid_category_ids:
            print("Category ID not found. Please enter a valid category ID.")
            continue

        # Fetch the set budget for the category
        cursor.execute('SELECT budget_limit FROM expense_categories WHERE id = ?', (category_id,))
        set_budget = cursor.fetchone()[0]

        # Fetch the total expenses for the category
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE category_id = ?', (category_id,))
        total_expenses = cursor.fetchone()[0]
        total_expenses = total_expenses if total_expenses else 0

        # Calculate the remaining budget
        remaining_budget = set_budget - total_expenses

        print(f"\nBudget Overview for Category ID {category_id} ({[category[1] for category in categories if category[0] == category_id][0]}):")
        print(f"Set Budget: {set_budget}")
        print(f"Total Expenses: {total_expenses}")
        print(f"Remaining Budget: {remaining_budget}\n")

        return

def set_goals(db):
    """
    Set a financial goal, such as saving a specific amount by a target date.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Input the goal amount
    while True:
        goal_amount_input = input("Enter the goal amount: ").strip()
        try:
            goal_amount = float(goal_amount_input)
            if goal_amount <= 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid amount. Please enter a positive number.")

    # Input the target date
    while True:
        target_date = input("Enter the target date (YYYY-MM-DD): ").strip()
        try:
            datetime.datetime.strptime(target_date, "%Y-%m-%d")
            break
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD "
                  "format.")

    # Choose a category (optional)
    cursor.execute('SELECT id, name FROM expense_categories')
    categories = cursor.fetchall()

    category_id = None
    if categories:
        print("Expense Categories:")
        for category in categories:
            print(f"ID: {category[0]}, Name: {category[1]}")

        category_input = input("Enter the ID of the category related to this "
                               "goal, or press enter to skip: ").strip()
        if category_input:
            try:
                category_id = int(category_input)
                if category_id not in [category[0] for category in categories]:
                    print("Category ID not found. Skipping category "
                          "selection.")
                    category_id = None
            except ValueError:
                print("Invalid ID. Skipping category selection.")

    # Insert the goal into the database
    try:
        cursor.execute('''
            INSERT INTO financial_goals (goal_amount, target_date, category_id) 
            VALUES (?, ?, ?)
        ''', (goal_amount, target_date, category_id))
        db.commit()
        print("Financial goal set successfully.")
    except sqlite3.Error as e:
        print(f"Error setting financial goal: {e}")

def view_goals_progress(db):
    """
    View progress towards financial goals, including the amount saved/spent 
    and the remaining amount needed to achieve each goal.

    Args:
        db (sqlite3.Connection): Connection object to the SQLite database.

    Returns:
        None
    """
    cursor = db.cursor()

    # Fetch all financial goals from the database
    cursor.execute('''
        SELECT financial_goals.id, financial_goals.goal_amount, 
                   financial_goals.target_date, expense_categories.name
        FROM financial_goals
        LEFT JOIN expense_categories ON financial_goals.category_id = 
                   expense_categories.id
    ''')
    goals = cursor.fetchall()

    if not goals:
        print("No financial goals found.\n")
        return

    print("Financial Goals:\n")

    for goal in goals:
        goal_id, goal_amount, target_date, category_name = goal
        category_name = category_name if category_name else "General"

        # Calculate the progress towards the goal
        if category_name == "General":
            cursor.execute('SELECT SUM(amount) FROM income')
            total_income = cursor.fetchone()[0] or 0

            cursor.execute('SELECT SUM(amount) FROM expenses')
            total_expenses = cursor.fetchone()[0] or 0

            progress = total_income - total_expenses
        else:
            cursor.execute('''
                SELECT SUM(amount) FROM income
                JOIN income_categories ON income.category_id = 
                           income_categories.id
                WHERE income_categories.name = ?
            ''', (category_name,))
            total_income = cursor.fetchone()[0] or 0

            cursor.execute('''
                SELECT SUM(amount) FROM expenses
                JOIN expense_categories ON expenses.category_id = 
                           expense_categories.id
                WHERE expense_categories.name = ?
            ''', (category_name,))
            total_expenses = cursor.fetchone()[0] or 0

            progress = total_income - total_expenses

        remaining = goal_amount - progress
        progress_percentage = (progress / goal_amount) * 100 if goal_amount != 0 else 0

        print(f"Goal ID: {goal_id}")
        print(f"Goal Amount: {goal_amount}")
        print(f"Target Date: {target_date}")
        print(f"Category: {category_name}")
        print(f"Progress: {progress} ({progress_percentage:.2f}%)")
        print(f"Remaining Amount: {remaining}\n")

        if remaining < 0:
            print(f"Congratulations, you have achieved the {category_name} "
                  f"financial goal!\n")

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

        print("\nTables created and preset data inserted successfully.\n")
    else:
        print("\nFailed to connect to the database.\n")

    while True:
        # Display main menu
        main_menu()
        choice = input("\nEnter your choice: ")
        
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