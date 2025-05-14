# server.py
import sqlite3
import os
import datetime
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

def init_db():
    """Initialize the SQLite database if it doesn't exist"""
    # Check if database file exists
    db_exists = os.path.exists('lists.db')
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect('lists.db')
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (list_id) REFERENCES lists (id)
        )
        ''')
        
        conn.commit()
        print("Database initialized with tables")
    
    conn.close()

# Initialize the database when the server starts
init_db()


@mcp.tool()
def create_list(channel_id: str, list_name: str) -> str:
    """Creates a new list for a channel"""
    conn = sqlite3.connect('lists.db')
    cursor = conn.cursor()
    
    try:
        # Insert the new list into the database
        cursor.execute(
            "INSERT INTO lists (channel_id, name) VALUES (?, ?)",
            (channel_id, list_name)
        )
        list_id = cursor.lastrowid
        conn.commit()
        return f"{list_name} created in channel {channel_id} with ID {list_id}"
    except Exception as e:
        conn.rollback()
        return f"Error creating list: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def add_list_item(channel_id: str, list_name: str, item_name: str) -> str:
    """Adds an item to an existing list identified by channel_id and list_name"""
    conn = sqlite3.connect('lists.db')
    cursor = conn.cursor()
    
    try:
        # Find the list by channel_id and list_name
        cursor.execute(
            "SELECT id, name FROM lists WHERE channel_id = ? AND name = ?", 
            (channel_id, list_name)
        )
        list_result = cursor.fetchone()
        
        if not list_result:
            return f"List '{list_name}' not found in channel {channel_id}"
        
        list_id, list_name = list_result
        
        # Insert the new item into the list_items table
        cursor.execute(
            "INSERT INTO list_items (list_id, name) VALUES (?, ?)",
            (list_id, item_name)
        )
        conn.commit()
        return f"Added '{item_name}' to list '{list_name}' in channel {channel_id}"
    except Exception as e:
        conn.rollback()
        return f"Error adding item to list: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_lists(channel_id: str = None) -> str:
    """Gets all lists, optionally filtered by channel_id"""
    conn = sqlite3.connect('lists.db')
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


if __name__ == "__main__":
    # mcp.run()
    mcp.run(transport="sse", host="127.0.0.1", port=8001)
