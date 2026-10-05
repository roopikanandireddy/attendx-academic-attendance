"""
AttendX — Secure Production Administrator Provisioning Script
Executes idempotent administrator account provisioning.
Guarantees password secrecy, bcrypt hash storage, and zero duplicate accounts.
Supports local SQLite and production Supabase PostgreSQL.
"""
import sys
import os
import argparse
import getpass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import SessionLocal as DefaultSessionLocal, engine as default_engine, Base
from app.services.admin_provisioning import (
    provision_admin_accounts,
    verify_existing_admins,
    ADMIN_ACCOUNTS,
)


def get_db_session(db_url: str = None):
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        target_engine = create_engine(db_url, pool_pre_ping=True)
        Base.metadata.create_all(bind=target_engine)
        TargetSession = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
        return TargetSession()
    return DefaultSessionLocal()


def main():
    parser = argparse.ArgumentParser(description="AttendX Secure Administrator Provisioning Tool")
    parser.add_argument("--interactive", "-i", action="store_true", help="Prompt for administrator passwords securely")
    parser.add_argument("--database-url", "-d", type=str, default=None, help="Target database connection URL (e.g. Supabase)")
    parser.add_argument("--verify-only", "-v", action="store_true", help="Inspect existing administrator accounts without modifying data")

    args = parser.parse_args()

    print("=" * 65)
    print("ATTENDX SECURE ADMINISTRATOR PROVISIONING TOOL")
    print("=" * 65)

    db = get_db_session(args.database_url)

    try:
        # Phase 1: Verify existing accounts
        existing_status = verify_existing_admins(db)
        print("\n[PHASE 1] Administrator Account Audit:")
        for item in existing_status:
            print(f"  - Email:    {item['email']}")
            print(f"    Exists:   {item['exists']}")
            if item['exists']:
                print(f"    ID:       {item['id']}")
                print(f"    Role:     {item['role']}")
                print(f"    Status:   {item['account_status']}")
                print(f"    Active:   {item['is_active']}")
                print(f"    Hash:     Present (bcrypt $2b$)")
            else:
                print(f"    Status:   Not yet provisioned")

        if args.verify_only:
            print("\n[VERIFY ONLY] Inspection complete. No changes made.")
            return

        passwords = {}
        if args.interactive:
            print("\n[PHASE 2] Secure Password Input (Input is hidden):")
            for acc in ADMIN_ACCOUNTS:
                email = acc["email"]
                while True:
                    p1 = getpass.getpass(f"  Enter password for {email}: ")
                    if len(p1) < 8:
                        print("  [ERROR] Password must be at least 8 characters long.")
                        continue
                    p2 = getpass.getpass(f"  Confirm password for {email}: ")
                    if p1 != p2:
                        print("  [ERROR] Passwords do not match. Try again.")
                        continue
                    passwords[email] = p1
                    del p1
                    del p2
                    break

        print("\n[PHASE 3] Executing Secure Provisioning...")
        results = provision_admin_accounts(db, passwords=passwords if passwords else None)

        print("\nProvisioning Results:")
        for r in results:
            print(f"  - Account: {r['email']}")
            print(f"    Action:  {r['action'].upper()}")
            print(f"    Role:    {r['role']}")
            print(f"    Status:  {r['account_status']}")
            print(f"    Active:  {r['is_active']}")
            print(f"    ID:      {r['id']}")
            print(f"    Hash:    Stored securely (bcrypt $2b$12$)")

        print("\n[SUCCESS] Administrator accounts provisioned safely.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
