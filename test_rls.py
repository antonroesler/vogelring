#!/usr/bin/env python3
"""
Test script to verify RLS is working correctly
"""

import os
import sys
import requests
import json


def test_rls():
    """Test if RLS is working correctly"""

    # Test the organization-aware endpoint
    print("🔍 Testing organization-aware endpoint...")
    response = requests.get("http://localhost/api/auth/test-org-data")
    if response.status_code == 200:
        data = response.json()
        print(
            f"✅ Organization-aware endpoint: {data['data_counts']['sightings']} sightings"
        )
    else:
        print(f"❌ Organization-aware endpoint failed: {response.status_code}")
        return

    # Test the main sightings endpoint
    print("🔍 Testing main sightings endpoint...")
    response = requests.get("http://localhost/api/sightings?per_page=5")
    if response.status_code == 200:
        sightings = response.json()
        print(f"✅ Main sightings endpoint: {len(sightings)} sightings")

        # Check org_ids of returned sightings
        if sightings:
            print("🔍 Checking org_ids of returned sightings...")
            for i, sighting in enumerate(sightings[:3]):
                print(
                    f"  Sighting {i + 1}: org_id = {sighting.get('org_id', 'MISSING')}"
                )
    else:
        print(f"❌ Main sightings endpoint failed: {response.status_code}")
        return

    # Test if we can access the current org_id setting
    print("🔍 Testing current organization context...")
    response = requests.get("http://localhost/api/auth/me")
    if response.status_code == 200:
        user_data = response.json()
        print(f"✅ Current user org_id: {user_data.get('org_id', 'MISSING')}")
    else:
        print(f"❌ Auth me endpoint failed: {response.status_code}")


if __name__ == "__main__":
    test_rls()

