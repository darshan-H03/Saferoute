"""
Database connection testing and diagnostic tool for SafeRoute.
Run from backend directory:
    python check_db.py
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from app import create_app
from app.extensions import db
from sqlalchemy import inspect, text


def check_database():
    app = create_app()
    with app.app_context():
        db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        # Mask password in URI for secure display
        masked_uri = db_uri
        if "@" in db_uri and "://" in db_uri:
            proto, rest = db_uri.split("://", 1)
            auth, host_part = rest.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                masked_uri = f"{proto}://{user}:*****@{host_part}"

        print("=" * 60)
        print("SafeRoute Database Connection Check")
        print("=" * 60)
        print(f"Configured URI: {masked_uri}")

        try:
            # Test raw connection
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1

            dialect = db.engine.dialect.name
            print(f"Status:         CONNECTED successfully")
            print(f"Dialect:        {dialect.upper()}")

            # Inspector
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Tables found:   {len(tables)}")
            print("-" * 60)
            print(f"{'Table Name':<30} {'Row Count':<15}")
            print("-" * 60)

            for table in sorted(tables):
                try:
                    with db.engine.connect() as conn:
                        res = conn.execute(text(f'SELECT count(*) FROM "{table}"'))
                        cnt = res.scalar()
                        print(f"{table:<30} {cnt:<15}")
                except Exception:
                    # Some dialects might not like quoted names
                    try:
                        with db.engine.connect() as conn:
                            res = conn.execute(text(f"SELECT count(*) FROM {table}"))
                            cnt = res.scalar()
                            print(f"{table:<30} {cnt:<15}")
                    except Exception as e:
                        print(f"{table:<30} (Error: {e})")

            print("=" * 60)
            print("Database is properly connected and ready for SafeRoute.")
            return True

        except Exception as exc:
            print("\n[FAILED] Could not connect to database.")
            print(f"Error details: {exc}\n")
            print("Troubleshooting tips:")
            print("1. For PostgreSQL: set DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname> in backend/.env")
            print("   Make sure psycopg2-binary is installed (already in requirements.txt).")
            print("2. For MySQL: set DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<dbname> in backend/.env")
            print("   Make sure pymysql is installed (pip install pymysql).")
            print("3. For local dev SQLite: leave DATABASE_URL=sqlite:///saferoute.db in backend/.env")
            return False


if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)
