"""
Script to wipe all data from the database while keeping the schema intact.
Removes all records from users, proposals, and votes tables.
"""

import sqlite3
import os

DATABASE = 'un_voting.db'

def wipe_database():
    """Delete all data from tables while preserving schema"""
    
    if not os.path.exists(DATABASE):
        print(f"❌ Database file '{DATABASE}' not found!")
        return
    
    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        
        print("🗑️  Wiping database...")
        print("-" * 50)
        
        # Delete all records from tables (keeps schema intact)
        cursor.execute('DELETE FROM votes')
        deleted_votes = cursor.rowcount
        
        cursor.execute('DELETE FROM proposals')
        deleted_proposals = cursor.rowcount
        
        cursor.execute('DELETE FROM users')
        deleted_users = cursor.rowcount
        
        db.commit()
        
        print(f"✓ Deleted {deleted_users} users")
        print(f"✓ Deleted {deleted_proposals} proposals")
        print(f"✓ Deleted {deleted_votes} votes")
        print("-" * 50)
        print("✅ Database cleaned successfully!")
        print("   Schema preserved - ready for new data")
        
        db.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    print("\n4E1 VOTING System - Database Wipe Tool")
    print("=" * 50)
    
    confirm = input("\n⚠️  Are you sure you want to delete ALL data? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        wipe_database()
    else:
        print("❌ Cancelled - no changes made")
    
    print()
