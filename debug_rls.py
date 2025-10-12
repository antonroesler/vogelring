#!/usr/bin/env python3
"""
Debug script to check RLS and organization context
"""

import os
import sys
import requests
import json


def debug_rls():
    """Debug RLS and organization context"""

    print("🔍 Debugging RLS and Organization Context")
    print("=" * 50)

    # Get current user info
    print("1. Current User Information:")
    response = requests.get("http://localhost/api/auth/me")
    if response.status_code == 200:
        user_data = response.json()
        print(f"   User ID: {user_data.get('id')}")
        print(f"   Email: {user_data.get('email')}")
        print(f"   Org ID: {user_data.get('org_id')}")
        print(f"   Display Name: {user_data.get('display_name')}")
    else:
        print(f"   ❌ Failed to get user info: {response.status_code}")
        return

    # Test organization-aware endpoint
    print("\n2. Organization-Aware Endpoint:")
    response = requests.get("http://localhost/api/auth/test-org-data")
    if response.status_code == 200:
        data = response.json()
        print(f"   User Org ID: {data['organization']['id']}")
        print(f"   Sightings Count: {data['data_counts']['sightings']}")
        print(f"   Ringings Count: {data['data_counts']['ringings']}")
    else:
        print(f"   ❌ Failed to get org data: {response.status_code}")

    # Test main sightings endpoint with detailed info
    print("\n3. Main Sightings Endpoint:")
    response = requests.get("http://localhost/api/sightings?per_page=3")
    if response.status_code == 200:
        sightings = response.json()
        print(f"   Total Returned: {len(sightings)}")
        for i, sighting in enumerate(sightings):
            print(f"   Sighting {i + 1}:")
            print(f"     ID: {sighting.get('id')}")
            print(f"     Org ID: {sighting.get('org_id')}")
            print(f"     Ring: {sighting.get('ring')}")
            print(f"     Species: {sighting.get('species')}")
    else:
        print(f"   ❌ Failed to get sightings: {response.status_code}")

    # Test if we can get sightings count
    print("\n4. Sightings Count Endpoint:")
    response = requests.get("http://localhost/api/sightings/count")
    if response.status_code == 200:
        count_data = response.json()
        print(f"   Count: {count_data.get('count')}")
    else:
        print(f"   ❌ Failed to get count: {response.status_code}")

    print("\n" + "=" * 50)
    print("🔍 Analysis:")
    print(
        "   - If org-aware endpoint shows 0 but main endpoint shows >0, RLS is not working"
    )
    print("   - If both show same count, RLS is working correctly")
    print("   - Check if sighting org_ids match current user org_id")


if __name__ == "__main__":
    debug_rls()
