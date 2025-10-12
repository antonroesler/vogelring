#!/usr/bin/env python3
"""
Test script to check what organization context is being set
"""

import requests
import json


def test_org_context():
    """Test what organization context is being set"""

    print("🔍 Testing Organization Context Setting")
    print("=" * 50)

    # Get current user info
    print("1. Current User Information:")
    response = requests.get("http://localhost/api/auth/me")
    if response.status_code == 200:
        user_data = response.json()
        print(f"   User ID: {user_data.get('id')}")
        print(f"   Org ID: {user_data.get('org_id')}")
        print(f"   Org ID Type: {type(user_data.get('org_id'))}")
        print(f"   Org ID Length: {len(str(user_data.get('org_id')))}")
    else:
        print(f"   ❌ Failed to get user info: {response.status_code}")
        return

    # Test organization-aware endpoint
    print("\n2. Organization-Aware Endpoint:")
    response = requests.get("http://localhost/api/auth/test-org-data")
    if response.status_code == 200:
        data = response.json()
        print(f"   User Org ID: {data['organization']['id']}")
        print(f"   Org ID Type: {type(data['organization']['id'])}")
        print(f"   Org ID Length: {len(str(data['organization']['id']))}")
        print(f"   Sightings Count: {data['data_counts']['sightings']}")
    else:
        print(f"   ❌ Failed to get org data: {response.status_code}")

    # Test main sightings endpoint
    print("\n3. Main Sightings Endpoint:")
    response = requests.get("http://localhost/api/sightings?per_page=2")
    if response.status_code == 200:
        sightings = response.json()
        print(f"   Total Returned: {len(sightings)}")
        if sightings:
            sighting_org_id = sightings[0].get("org_id")
            print(f"   First Sighting Org ID: {sighting_org_id}")
            print(f"   Org ID Type: {type(sighting_org_id)}")
            print(f"   Org ID Length: {len(str(sighting_org_id))}")

            # Check if they match
            user_org_id = user_data.get("org_id")
            print(f"   Match: {user_org_id == sighting_org_id}")
            print(f"   User Org ID: {user_org_id}")
            print(f"   Sighting Org ID: {sighting_org_id}")
    else:
        print(f"   ❌ Failed to get sightings: {response.status_code}")

    print("\n" + "=" * 50)
    print("🔍 Analysis:")
    print("   - If org_ids don't match, RLS should filter them out")
    print("   - If they do match, then RLS is working correctly")
    print("   - Check if the org_id format is correct (UUID format)")


if __name__ == "__main__":
    test_org_context()
