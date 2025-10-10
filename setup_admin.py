#!/usr/bin/env python3
"""
Admin setup script for organization-based multi-tenancy
Sets admin privileges for a user (must be run manually for security)
"""

import os
import sys
import psycopg2
from pathlib import Path


def get_db_connection():
    """Get database connection from environment"""
    db_password = os.getenv("DB_PASSWORD", "defaultpassword")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "vogelring")
    db_user = os.getenv("DB_USER", "vogelring")

    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None


def set_admin_privileges(email: str):
    """Set admin privileges for a user"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Check if user exists
            cursor.execute(
                "SELECT id, email, display_name, is_admin FROM users WHERE email = %s;",
                (email,),
            )
            user = cursor.fetchone()

            if not user:
                print(f"❌ User not found: {email}")
                print("   Make sure the user has logged in at least once.")
                return False

            user_id, user_email, display_name, is_admin = user

            if is_admin:
                print(f"✅ User {email} already has admin privileges")
                return True

            # Set admin privileges
            cursor.execute(
                "UPDATE users SET is_admin = true WHERE email = %s;", (email,)
            )
            conn.commit()

            print(f"✅ Admin privileges granted to: {email}")
            print(f"   User ID: {user_id}")
            print(f"   Display Name: {display_name}")

            return True

    except Exception as e:
        print(f"❌ Failed to set admin privileges: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def list_users():
    """List all users and their admin status"""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.email, u.display_name, u.is_admin, o.name as org_name
                FROM users u
                LEFT JOIN organizations o ON u.org_id = o.id
                ORDER BY u.is_admin DESC, u.email;
            """)
            users = cursor.fetchall()

            print("\n👥 All Users:")
            print("-" * 80)
            print(f"{'Email':<30} {'Name':<20} {'Admin':<8} {'Organization':<20}")
            print("-" * 80)

            for email, display_name, is_admin, org_name in users:
                admin_status = "✅ Yes" if is_admin else "❌ No"
                name = display_name or "N/A"
                org = org_name or "N/A"
                print(f"{email:<30} {name:<20} {admin_status:<8} {org:<20}")

    except Exception as e:
        print(f"❌ Failed to list users: {e}")
    finally:
        conn.close()


def main():
    """Main admin setup"""
    print("👑 Admin Setup for Organization-Based Multi-Tenancy")
    print("=" * 55)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_admin.py <email>           # Set admin privileges")
        print("  python setup_admin.py --list            # List all users")
        print("  python setup_admin.py --help            # Show this help")
        print("\nExamples:")
        print("  python setup_admin.py admin@example.com")
        print("  python setup_admin.py dev@vogelring.local")
        return

    command = sys.argv[1]

    if command == "--list":
        list_users()
    elif command == "--help":
        main()  # Show usage
    elif "@" in command:  # Looks like an email
        email = command
        print(f"🔧 Setting admin privileges for: {email}")

        if set_admin_privileges(email):
            print(f"\n✅ Success! {email} now has admin privileges.")
            print("\n🔧 Next steps:")
            print("   1. Restart the application if needed")
            print("   2. User can now access admin endpoints:")
            print("      - GET /api/admin/organizations")
            print("      - GET /api/admin/status")
            print("      - POST /api/admin/organizations")
            print("   3. Test admin access in the frontend user menu")
        else:
            print(f"\n❌ Failed to set admin privileges for {email}")
            sys.exit(1)
    else:
        print(f"❌ Invalid command: {command}")
        print("Use --help for usage information")
        sys.exit(1)


if __name__ == "__main__":
    main()
