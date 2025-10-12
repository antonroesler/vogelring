#!/usr/bin/env python3
"""
Database migration runner for multi-user implementation
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


def run_migration(migration_file: str):
    """Run a specific migration file"""
    migration_path = (
        Path(__file__).parent / "backend" / "database" / "migrations" / migration_file
    )

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False

    print(f"🔄 Running migration: {migration_file}")

    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Read migration file
            with open(migration_path, "r") as f:
                migration_sql = f.read()

            # Execute migration
            cursor.execute(migration_sql)
            conn.commit()

        print(f"✅ Migration completed successfully: {migration_file}")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def check_migration_status():
    """Check if organization migration has already been applied"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cursor:
            # Check if organizations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'organizations'
                );
            """)
            orgs_table_exists = cursor.fetchone()[0]

            # Check if org_id columns exist
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'ringings' 
                    AND column_name = 'org_id'
                );
            """)
            org_id_exists = cursor.fetchone()[0]

            # Check if users table has org_id and is_admin
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'org_id'
                );
            """)
            users_org_id_exists = cursor.fetchone()[0]

        return orgs_table_exists and org_id_exists and users_org_id_exists

    except Exception as e:
        print(f"❌ Migration status check failed: {e}")
        return False
    finally:
        conn.close()


def main():
    """Main migration runner"""
    print("🗃️  Organization-Based Multi-Tenancy Migration")
    print("=" * 50)

    # Check current status
    print("🔍 Checking migration status...")
    if check_migration_status():
        print("✅ Organization migration already applied!")
        print("\n📊 Verifying tables...")

        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT count(*) FROM organizations;")
                    org_count = cursor.fetchone()[0]
                    print(f"   Organizations: {org_count}")

                    cursor.execute("SELECT count(*) FROM users;")
                    user_count = cursor.fetchone()[0]
                    print(f"   Users: {user_count}")

                    cursor.execute(
                        "SELECT count(*) FROM ringings WHERE org_id IS NOT NULL;"
                    )
                    ringings_with_org = cursor.fetchone()[0]
                    print(f"   Ringings with org_id: {ringings_with_org}")

                    cursor.execute(
                        "SELECT count(*) FROM sightings WHERE org_id IS NOT NULL;"
                    )
                    sightings_with_org = cursor.fetchone()[0]
                    print(f"   Sightings with org_id: {sightings_with_org}")

                    cursor.execute("SELECT count(*) FROM users WHERE is_admin = true;")
                    admin_count = cursor.fetchone()[0]
                    print(f"   Admin users: {admin_count}")

            except Exception as e:
                print(f"❌ Verification failed: {e}")
            finally:
                conn.close()

        return

    # Run combined organization migration
    print("🚀 Applying complete organization migration...")
    if run_migration("005_complete_organization_migration.sql"):
        print("\n✅ Organization migration completed successfully!")
        print("\n🔧 Next steps:")
        print("   1. Restart the application: docker-compose restart api")
        print("   2. Test with: python test_multi_user.py")
        print(
            "   3. Check organization data isolation with different DEV_USER_EMAIL values"
        )
        print("   4. Set admin privileges:")
        print("      docker-compose exec postgres psql -U vogelring -d vogelring")
        print(
            "      UPDATE users SET is_admin=true WHERE email='your-email@domain.com';"
        )
        print("   5. Test admin endpoints: curl http://localhost/api/admin/status")
    else:
        print("\n❌ Migration failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
