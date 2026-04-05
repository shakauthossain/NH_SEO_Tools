import os
import sys

# Add the parent directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine

def migrate():
    with engine.connect() as conn:
        print("Checking for full_results column...")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='audits' AND column_name='full_results';"))
        if not result.fetchone():
            print("Adding full_results column...")
            conn.execute(text("ALTER TABLE audits ADD COLUMN full_results JSONB;"))
            conn.commit()
            print("Done!")
        else:
            print("Column already exists.")

if __name__ == "__main__":
    migrate()
