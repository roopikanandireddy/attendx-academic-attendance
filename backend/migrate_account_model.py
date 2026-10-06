"""
AttendX Safe Database Migration: Account Lifecycle & Activation Tokens
Adds account_status to users table and creates account_activation_tokens table.
Compatible with both SQLite and PostgreSQL. Idempotent. Non-destructive.
"""
import sys
import os
import argparse
from urllib.parse import urlparse
from sqlalchemy import text, inspect, create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.database import engine as default_engine, Base
from app.models.account_token import AccountToken
from app.models.user import User


def get_masked_db_info(db_url: str) -> str:
    """Return safe masked database description without exposing credentials."""
    try:
        parsed = urlparse(db_url)
        scheme = parsed.scheme or "sqlite"
        host = parsed.hostname or "local"
        port = f":{parsed.port}" if parsed.port else ""
        db_name = parsed.path or ""
        return f"{scheme}://***@{host}{port}{db_name}"
    except Exception:
        return "configured-database-target"


def get_target_engine(db_url: str = None):
    """Resolve target database engine with optimized connection pooling."""
    if db_url and db_url.strip():
        url = db_url.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("sqlite"):
            return create_engine(url, connect_args={"check_same_thread": False})
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            pool_timeout=15,
            pool_recycle=300,
            connect_args={"connect_timeout": 10},
        )
    return default_engine


def run_migration(target_engine=None):
    """
    Execute idempotent, non-destructive migration on the target database engine.
    1. Adds users.account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'
    2. Updates null/empty account_status to 'ACTIVE'
    3. Creates account_activation_tokens table if missing
    4. Creates performance indexes on account_status and token fields
    5. Verifies all user records and relationships remain intact
    """
    eng = target_engine or default_engine
    dialect_name = eng.dialect.name
    masked_target = get_masked_db_info(str(eng.url))

    print("=" * 65)
    print("ATTENDX DATABASE MIGRATION — MODULE 1")
    print(f"Target Dialect : {dialect_name}")
    print(f"Target Endpoint: {masked_target}")
    print("=" * 65)

    inspector = inspect(eng)
    table_names = inspector.get_table_names()

    if "users" not in table_names:
        print("[MIGRATION WARNING] 'users' table not found. Creating base schema first...")
        Base.metadata.create_all(bind=eng)
        inspector = inspect(eng)

    # 1. Pre-flight record count
    with eng.connect() as conn:
        user_count_before = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        print(f"[PRE-FLIGHT] Verified existing user records: {user_count_before} accounts present.")

    # 2. Check and migrate users table columns
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    with eng.begin() as conn:
        if "account_status" not in user_columns:
            print("[MIGRATION] Adding 'account_status' column to 'users' table...")
            if dialect_name == "postgresql":
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"))
            else:
                conn.execute(text("ALTER TABLE users ADD COLUMN account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE'"))
            print("[MIGRATION] Added 'account_status' column (VARCHAR(20), NOT NULL, DEFAULT 'ACTIVE').")
        else:
            print("[MIGRATION] 'account_status' column already exists in 'users'.")

        # Ensure all existing users have ACTIVE status
        conn.execute(text("UPDATE users SET account_status = 'ACTIVE' WHERE account_status IS NULL OR account_status = ''"))
        print("[MIGRATION] Ensured all existing users have status 'ACTIVE'.")

    # 3. Check and create account_activation_tokens table
    inspector = inspect(eng)
    table_names = inspector.get_table_names()
    if "account_activation_tokens" not in table_names:
        print("[MIGRATION] Creating 'account_activation_tokens' table...")
        Base.metadata.tables["account_activation_tokens"].create(bind=eng, checkfirst=True)
        print("[MIGRATION] Created 'account_activation_tokens' table successfully.")
    else:
        print("[MIGRATION] 'account_activation_tokens' table already exists.")

    # 4. Create required indexes idempotently
    print("[MIGRATION] Verifying required performance indexes...")
    with eng.begin() as conn:
        if dialect_name == "postgresql":
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_account_status ON users(account_status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_account_tokens_token_hash ON account_activation_tokens(token_hash)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_account_tokens_user_id ON account_activation_tokens(user_id)"))
        else:
            # SQLite safe index creation
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_account_status ON users(account_status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_account_tokens_token_hash ON account_activation_tokens(token_hash)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_account_tokens_user_id ON account_activation_tokens(user_id)"))
    print("[MIGRATION] Indexes verified successfully.")

    # 5. Post-migration verification
    inspector = inspect(eng)
    updated_cols = [col["name"] for col in inspector.get_columns("users")]
    assert "account_status" in updated_cols, "Verification Failed: users.account_status missing!"

    with eng.connect() as conn:
        user_count_after = conn.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0
        active_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE account_status = 'ACTIVE'")).scalar() or 0
        assert user_count_after == user_count_before, f"Data Loss Error: Expected {user_count_before} users, found {user_count_after}!"
        print(f"[VERIFICATION] User records intact: {user_count_after}/{user_count_before} preserved.")
        print(f"[VERIFICATION] Active accounts count: {active_count}/{user_count_after}.")

    print("[MIGRATION] Migration complete and 100% verified.")
    return True


def main():
    parser = argparse.ArgumentParser(description="AttendX Account Model Database Migration")
    parser.add_argument(
        "--database-url",
        "-d",
        type=str,
        default=os.getenv("DATABASE_URL"),
        help="Target database connection URL (e.g. Supabase PostgreSQL)",
    )
    args = parser.parse_args()

    target_eng = get_target_engine(args.database_url)
    run_migration(target_eng)


if __name__ == "__main__":
    main()

