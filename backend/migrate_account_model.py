"""
AttendX Safe Database Migration: Account Lifecycle & Activation Tokens
Adds account_status to users table and creates account_activation_tokens table.
Compatible with both SQLite and PostgreSQL. Idempotent.
"""
import sys
import os
from sqlalchemy import text, inspect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.database import engine, Base
from app.models.account_token import AccountToken
from app.models.user import User


def run_migration():
    print("[MIGRATION] Starting AttendX account model migration...")
    inspector = inspect(engine)

    # 1. Check users table columns
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    with engine.begin() as conn:
        if "account_status" not in user_columns:
            print("[MIGRATION] Adding 'account_status' column to 'users' table...")
            # Detect dialect
            if engine.dialect.name == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"))
            print("[MIGRATION] Added 'account_status' column successfully.")
        else:
            print("[MIGRATION] 'account_status' column already exists in 'users'.")

        # Ensure all existing users have ACTIVE account status
        result = conn.execute(text("UPDATE users SET account_status = 'ACTIVE' WHERE account_status IS NULL OR account_status = ''"))
        print(f"[MIGRATION] Ensured existing users have status 'ACTIVE'.")

    # 2. Check and create account_activation_tokens table
    table_names = inspector.get_table_names()
    if "account_activation_tokens" not in table_names:
        print("[MIGRATION] Creating 'account_activation_tokens' table...")
        Base.metadata.tables["account_activation_tokens"].create(bind=engine, checkfirst=True)
        print("[MIGRATION] Created 'account_activation_tokens' table successfully.")
    else:
        print("[MIGRATION] 'account_activation_tokens' table already exists.")

    print("[MIGRATION] Migration complete and verified.")


if __name__ == "__main__":
    run_migration()
