# server.py
import sqlite3
import os
import datetime
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

# Define database path
DATA_DIR = os.path.join(os.getcwd(), 'data')
# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'lists.db')

def init_db():
    """Initialize the SQLite database if it doesn't exist"""
    # Check if database file exists
    db_exists = os.path.exists(DB_PATH)
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    if not db_exists:
        # Create lists table
        cursor.execute('''
        CREATE TABLE lists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create list_items table
        cursor.execute('''
        CREATE TABLE list_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (list_id) REFERENCES lists (id)
        )
        ''')
        
        conn.commit()
        print("Database initialized with tables")
    
    conn.close()

# Initialize the database when the server starts
init_db()

def migrate_database():
    """Migrate the existing database to include the new status and completed_at columns"""
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


@mcp.tool()
def add_list_item(channel_id: str, list_name: str, item_name: str) -> str:
    """Adds an item to a list identified by channel_id and list_name. Creates the list if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Find the list by channel_id and list_name
        cursor.execute(
            "SELECT id, name FROM lists WHERE channel_id = ? AND name = ?", 
            (channel_id, list_name)
        )
        list_result = cursor.fetchone()
        
        # If list doesn't exist, create it
        if not list_result:
            cursor.execute(
                "INSERT INTO lists (channel_id, name) VALUES (?, ?)",
                (channel_id, list_name)
            )
            list_id = cursor.lastrowid
            list_created = True
        else:
            list_id, list_name = list_result
            list_created = False
        
        # Insert the new item into the list_items table
        cursor.execute(
            "INSERT INTO list_items (list_id, name) VALUES (?, ?)",
            (list_id, item_name)
        )
        conn.commit()
        
        if list_created:
            return f"Created list '{list_name}' in channel {channel_id} and added '{item_name}'"
        else:
            return f"Added '{item_name}' to list '{list_name}' in channel {channel_id}"
    except Exception as e:
        conn.rollback()
        return f"Error adding item to list: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_lists(channel_id: str = None) -> str:
    """Gets all lists, optionally filtered by channel_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if channel_id:
            cursor.execute("SELECT id, name FROM lists WHERE channel_id = ?", (channel_id,))
            lists = cursor.fetchall()
            if not lists:
                return f"No lists found for channel {channel_id}"
        else:
            cursor.execute("SELECT id, channel_id, name FROM lists")
            lists = cursor.fetchall()
            if not lists:
                return "No lists found"
        
        result = "Available lists:\n"
        for list_data in lists:
            if channel_id:
                result += f"- ID: {list_data[0]}, Name: {list_data[1]}\n"
            else:
                result += f"- ID: {list_data[0]}, Channel: {list_data[1]}, Name: {list_data[2]}\n"
        
        return result.strip()
    except Exception as e:
        return f"Error retrieving lists: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_list_items(channel_id: str, list_name: str, show_completed: bool = False) -> str:
    """Gets all items for a specific list identified by channel_id and list_name. 
    By default only shows active items, set show_completed=True to see completed items too."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Find the list by channel_id and list_name
        cursor.execute(
            "SELECT id FROM lists WHERE channel_id = ? AND name = ?", 
            (channel_id, list_name)
        )
        list_result = cursor.fetchone()
        
        if not list_result:
            return f"List '{list_name}' not found in channel {channel_id}"
        
        list_id = list_result[0]
        
        # Get all items for this list
        if show_completed:
            cursor.execute(
                "SELECT name, created_at, status, completed_at FROM list_items WHERE list_id = ? ORDER BY created_at",
                (list_id,)
            )
        else:
            cursor.execute(
                "SELECT name, created_at, status, completed_at FROM list_items WHERE list_id = ? AND status = 'active' ORDER BY created_at",
                (list_id,)
            )
        items = cursor.fetchall()
        
        if not items:
            return f"No items found in list '{list_name}'"
        
        result = f"Items in list '{list_name}':\n"
        for i, (item_name, created_at, status, completed_at) in enumerate(items, 1):
            # Format the timestamp for better readability
            created_time = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_time = created_time.strftime("%Y-%m-%d %H:%M:%S")
            
            if status == 'completed' and completed_at:
                completed_time = datetime.datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                formatted_completed = completed_time.strftime("%Y-%m-%d %H:%M:%S")
                result += f"{i}. {item_name} ✓ (added: {formatted_time}, completed: {formatted_completed})\n"
            else:
                result += f"{i}. {item_name} (added: {formatted_time})\n"
        
        return result.strip()
    except Exception as e:
        return f"Error retrieving list items: {str(e)}"
    finally:
        conn.close()


@mcp.tool()
def complete_list_item(channel_id: str, list_name: str, item_name: str) -> str:
    """Marks a list item as completed instead of deleting it"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Find the list by channel_id and list_name
        cursor.execute(
            "SELECT id FROM lists WHERE channel_id = ? AND name = ?", 
            (channel_id, list_name)
        )
        list_result = cursor.fetchone()
        
        if not list_result:
            return f"List '{list_name}' not found in channel {channel_id}"
        
        list_id = list_result[0]
        
        # Find the item by name in the specified list
        cursor.execute(
            "SELECT id, status FROM list_items WHERE list_id = ? AND name = ? AND status = 'active'",
            (list_id, item_name)
        )
        item_result = cursor.fetchone()
        
        if not item_result:
            return f"Active item '{item_name}' not found in list '{list_name}'"
        
        item_id = item_result[0]
        
        # Mark the item as completed with current timestamp
        current_time = datetime.datetime.now().isoformat()
        cursor.execute(
            "UPDATE list_items SET status = 'completed', completed_at = ? WHERE id = ?",
            (current_time, item_id)
        )
        conn.commit()
        
        return f"Marked '{item_name}' as completed in list '{list_name}'"
    except Exception as e:
        conn.rollback()
        return f"Error completing list item: {str(e)}"
    finally:
        conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        # Run migration if requested
        migrate_database()
    else:
        # Otherwise run the server
        mcp.run(transport="sse", host="0.0.0.0", port=8001)
