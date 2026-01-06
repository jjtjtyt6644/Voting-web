import sqlite3
import sys

DATABASE = 'un_voting.db'

def migrate_database():
    """Migrate database schema from 'country' column to 'position' column"""
    try:
        db = sqlite3.connect(DATABASE)
        cursor = db.cursor()
        
        # Check if position column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'position' in columns:
            print("✓ 'position' column already exists. No migration needed.")
            db.close()
            return
        
        if 'country' not in columns:
            print("❌ Neither 'country' nor 'position' column found. Database schema is corrupted.")
            db.close()
            return
        
        print("🔄 Migrating 'country' column to 'position'...")
        
        # Rename the column by creating a new table and copying data
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                position TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copy data from old table to new table
        cursor.execute("""
            INSERT INTO users_new (id, name, password, position, created_date)
            SELECT id, name, password, country, created_date FROM users
        """)
        
        # Drop the old table
        cursor.execute("DROP TABLE users")
        
        # Rename the new table to users
        cursor.execute("ALTER TABLE users_new RENAME TO users")
        
        db.commit()
        db.close()
        
        print("✓ Migration completed successfully!")
        print("✓ Column 'country' has been renamed to 'position'")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("UN Voting Platform - Database Migration")
    print("=" * 50)
    print("This script will migrate the 'country' column to 'position'")
    print("=" * 50)
    
    confirm = input("\nDo you want to proceed? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        migrate_database()
    else:
        print("Migration cancelled.")
