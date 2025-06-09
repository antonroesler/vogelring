import requests
import json
import os
from datetime import datetime
from typing import Set, Tuple

# Configuration
API_BASE_URL = 'https://782syzefh4.execute-api.eu-central-1.amazonaws.com/Prod'
API_KEY = os.environ.get('RING_API_KEY')

if not API_KEY:
    print("Error: RING_API_KEY environment variable not set")
    exit(1)

headers = {
    'x-api-key': API_KEY,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

def get_all_sightings():
    """Fetch all sightings from the API"""
    print("Fetching all sightings...")
    response = requests.get(f"{API_BASE_URL}/sightings?per_page=10000", headers=headers)
    response.raise_for_status()
    return response.json()

def add_partner_relationship(ring: str, partner_ring: str, year: int):
    """Add a partner relationship via the API"""
    url = f"{API_BASE_URL}/family/{ring}/partners"
    data = {
        "partner_ring": partner_ring,
        "year": year
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"✓ Added partner relationship: {ring} <-> {partner_ring} ({year})")
            return True
        else:
            print(f"✗ Failed to add partner relationship: {ring} <-> {partner_ring} ({year}) - Status: {response.status_code}")
            if response.text:
                print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error adding partner relationship: {ring} <-> {partner_ring} ({year}) - {str(e)}")
        return False

def migrate_partner_relationships():
    """Migrate all partner relationships from sightings to family tree"""
    sightings = get_all_sightings()
    
    # Track unique partner relationships to avoid duplicates
    partner_relationships: Set[Tuple[str, str, int]] = set()
    
    print(f"Processing {len(sightings)} sightings...")
    
    for sighting in sightings:
        ring = sighting.get('ring')
        partner = sighting.get('partner')
        date_str = sighting.get('date')
        
        # Skip if missing required data
        if not ring or not partner or not date_str:
            continue
            
        try:
            # Parse year from date
            year = datetime.fromisoformat(date_str).year
            
            # Create a normalized relationship tuple (smaller ring first to avoid duplicates)
            relationship = tuple(sorted([ring, partner]) + [year])
            
            if relationship not in partner_relationships:
                partner_relationships.add(relationship)
                
        except Exception as e:
            print(f"Warning: Could not parse date '{date_str}' for sighting {sighting.get('id', 'unknown')}: {e}")
            continue
    
    print(f"\nFound {len(partner_relationships)} unique partner relationships to migrate")
    
    # Add each relationship
    success_count = 0
    for ring1, ring2, year in partner_relationships:
        # Add relationship for both birds (bidirectional)
        if add_partner_relationship(ring1, ring2, year):
            success_count += 1
    
    print(f"\nMigration complete: {success_count}/{len(partner_relationships)} relationships added successfully")

if __name__ == "__main__":
    print("Starting partner relationship migration...")
    print("=" * 50)
    
    try:
        migrate_partner_relationships()
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
    except Exception as e:
        print(f"\nMigration failed: {str(e)}")
        exit(1)