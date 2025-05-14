import sqlite3
import os
import sys

# Define database path
DATA_DIR = os.path.join(os.getcwd(), 'data')
DB_PATH = os.path.join(DATA_DIR, 'lists.db')

def migrate_database():
    """Migrate the existing database to include the new status and completed_at columns"""
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if the status column already exists
        cursor.execute("PRAGMA table_info(list_items)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'status' not in column_names:
            print("Adding 'status' column to list_items table...")
            cursor.execute("ALTER TABLE list_items ADD COLUMN status TEXT DEFAULT 'active'")
        else:
            print("Column 'status' already exists.")
            
        if 'completed_at' not in column_names:
            print("Adding 'completed_at' column to list_items table...")
            cursor.execute("ALTER TABLE list_items ADD COLUMN completed_at TIMESTAMP")
        else:
            print("Column 'completed_at' already exists.")
            
        conn.commit()
        print("Migration completed successfully!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
