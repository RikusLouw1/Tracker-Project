import sqlite3

def connect_to_db(db_name="budget_tracker.db"):
    """
    Connect to the SQLite database. If the database does not exist, it will be created.
    
    Parameters:
        db_name (str): The name of the database file.
    
    Returns:
        sqlite3.Connection: Connection object to the SQLite database, or None if the connection fails.
    """
    try:
        conn = sqlite3.connect(db_name)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def main():
    conn = connect_to_db()

main()