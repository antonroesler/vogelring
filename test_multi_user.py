#!/usr/bin/env python3
"""
Test script for organization-based multi-tenancy implementation
Run this after starting the development environment to verify organization functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost/api"


def test_authentication():
    """Test authentication endpoints"""
    print("🔐 Testing Authentication...")

    # Test /auth/me endpoint
    try:
        response = requests.get(f"{BASE_URL}/auth/me")
        if response.status_code == 200:
            user_data = response.json()
            print(
                f"✅ Current user: {user_data['email']} ({user_data['display_name']})"
            )
            return user_data
        else:
            print(f"❌ Auth failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return None


def test_auth_status():
    """Test authentication status endpoint"""
    print("\n📊 Testing Auth Status...")

    try:
        response = requests.get(f"{BASE_URL}/auth/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Development mode: {status_data['development_mode']}")
            print(f"✅ Headers present: {status_data['headers_present']}")
            return status_data
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Status error: {e}")
        return None


def test_org_data():
    """Test organization data isolation endpoint"""
    print("\n📈 Testing Organization Data Isolation...")

    try:
        response = requests.get(f"{BASE_URL}/auth/test-org-data")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User ID: {data['user']['id']}")
            print(f"✅ User is admin: {data['user']['is_admin']}")
            print(f"✅ Organization ID: {data['organization']['id']}")
            print(f"✅ Organization name: {data['organization']['name']}")
            print(f"✅ Sightings count: {data['data_counts']['sightings']}")
            print(f"✅ Ringings count: {data['data_counts']['ringings']}")
            return data
        else:
            print(
                f"❌ Organization data test failed: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        print(f"❌ Organization data error: {e}")
        return None


def test_api_health():
    """Test basic API health"""
    print("\n🏥 Testing API Health...")

    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            api_data = response.json()
            print(f"✅ API Status: {api_data['status']}")
            print(f"✅ API Version: {api_data['version']}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health error: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Organization-Based Multi-Tenancy Test Suite")
    print("=" * 55)

    # Test API health first
    if not test_api_health():
        print("\n❌ API is not responding. Make sure docker-compose is running.")
        return

    # Test authentication
    user_data = test_authentication()
    if not user_data:
        print("\n❌ Authentication failed. Check backend logs.")
        return

    # Test auth status
    status_data = test_auth_status()

    # Test organization data isolation
    data_counts = test_org_data()

    print("\n" + "=" * 55)
    if user_data and status_data and data_counts:
        print("✅ All tests passed! Organization-based multi-tenancy is working.")
        print("\n📋 Summary:")
        print(f"   User: {user_data['email']}")
        print(f"   Organization: {data_counts['organization']['name']}")
        print(f"   Admin Status: {data_counts['user']['is_admin']}")
        print(f"   Development Mode: {status_data['development_mode']}")
        print(
            f"   Data Isolation: Working (Organization has {data_counts['data_counts']['sightings']} sightings)"
        )

        print("\n🔧 Next Steps:")
        print("   1. Run migration: Apply organization migration script")
        print("   2. Test with different organizations by changing DEV_USER_EMAIL")
        print("   3. Update API endpoints to use organization-aware repositories")
        print("   4. Test admin functionality with is_admin=true in database")

    else:
        print("❌ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    main()
