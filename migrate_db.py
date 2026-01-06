import sqlite3
import os

DATABASE = 'un_voting.db'

def migrate_database():
    """Migrate the database to add user_id column to votes table"""
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} does not exist. Creating fresh database...")
        return

    db = sqlite3.connect(DATABASE)
    cursor = db.cursor()
    
    try:
        # Check if the votes table has the user_id column
        cursor.execute("PRAGMA table_info(votes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("Adding user_id column to votes table...")
            
            # First, check if member_id exists and needs to be renamed/migrated
            if 'member_id' in columns:
                print("Migrating member_id to user_id...")
                
                # Create new votes table with correct schema
                cursor.execute('''
                    CREATE TABLE votes_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        proposal_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        vote TEXT NOT NULL,
                        voted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(proposal_id) REFERENCES proposals(id),
                        FOREIGN KEY(user_id) REFERENCES users(id),
                        UNIQUE(proposal_id, user_id)
                    )
                ''')
                
                # Copy data from old table
                cursor.execute('''
                    INSERT INTO votes_new (id, proposal_id, user_id, vote, voted_date)
                    SELECT id, proposal_id, member_id, vote, voted_date FROM votes
                ''')
                
                # Drop old table and rename new one
                cursor.execute('DROP TABLE votes')
                cursor.execute('ALTER TABLE votes_new RENAME TO votes')
                
                print("✓ Successfully migrated member_id to user_id")
            else:
                # Just add the user_id column
                cursor.execute('ALTER TABLE votes ADD COLUMN user_id INTEGER')
                print("✓ Successfully added user_id column to votes table")
        else:
            print("✓ user_id column already exists in votes table")
        
        db.commit()
        print("✓ Database migration completed successfully!")
        
    except sqlite3.OperationalError as e:
        print(f"✗ Database error: {e}")
        db.rollback()
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    print("Starting database migration...")
    migrate_database()
