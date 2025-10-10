GET {{URL}}/api/birds/120891

Response:

{
"ring": "120891",
"species": "Höckerschwan",
"sighting_count": 17,
"last_seen": "2022-01-23",
"first_seen": "2018-03-05",
"other_species_identifications": null,
"sightings": [
{
"id": "248bc305-fbe8-4c8e-9e58-27050f668b47",
"excel_id": 2662,
"species": "Höckerschwan",
"ring": "120891",
"reading": "…20891",
"date": "2022-01-23",
"place": "Klein-Krotzenburg, Mainauen",
"area": null,
"lat": 50.070705,
"lon": 8.986423,
"is_exact_location": false,
"partner": null,
"status": null,
"age": "ad",
"melder": "IR",
"melded": true
},
{
"id": "f680dad9-8e58-4849-b1c8-321239c4775e",
"excel_id": 2661,
"species": "Höckerschwan",
"ring": "120891",
"reading": "120891",
"date": "2020-12-30",
"place": "Klein-Krotzenburg, Mainauen",
"area": null,
"lat": 50.070696,
"lon": 8.986305,
"is_exact_location": false,
"partner": "120885",
"status": null,
"age": null,
"melder": "IR",
"melded": true
},
{
"id": "908920f0-a977-44ed-b46f-a68c8d3fbfe5",
"excel_id": 2660,
"species": "Höckerschwan",
"ring": "120891",
"reading": "120891",
"date": "2019-07-08",
"place": "OF, Carl-Ulrich-Brücke",
"area": null,
"lat": 50.110979,
"lon": 8.757553,
"is_exact_location": false,
"partner": null,
"status": null,
"age": null,
"melder": "IR",
"melded": true
}
...
],
"partners": [
{
"ring": "120885",
"year": 2020,
"confidence": null,
"source": "migration",
"notes": "Migrated from family_tree_entries"
}
]
}

GET {{URL}}/api/ringing/120891

Response:
{
"ring_scheme": "DEW",
"id": "5cbbbb95-49dc-4df1-a96f-6e153744cfd1",
"date": "2018-03-05",
"lon": 8.75778,
"ringer": "0337",
"age": 5,
"created_at": "2025-09-12T19:36:42.518715",
"species": "01520",
"ring": "120891",
"place": "Offenbach, Carl-Ulrich-Brücke\*[DEED, 5818]",
"lat": 50.11167,
"sex": 0,
"status": null,
"updated_at": "2025-09-12T19:36:42.518715"
}

GET {{URL}}/api/family/relationships/282373

Response:
[
{
"id": "4fef90a4-b7c8-40df-9d48-1ad2f27e3ddf",
"bird1_ring": "282373",
"bird2_ring": "E12872",
"relationship_type": "parent_of",
"year": 2025,
"confidence": null,
"source": null,
"notes": null,
"sighting1_id": null,
"sighting2_id": null,
"ringing1_id": null,
"ringing2_id": "206904f5-c134-4d04-a265-ed30a7dcb7e5",
"created_at": "2025-09-17T15:56:39.578915",
"updated_at": "2025-09-17T15:56:39.578915"
},
{
"id": "d136989d-489f-4e4f-9048-fa5ba22828af",
"bird1_ring": "282373",
"bird2_ring": "282394",
"relationship_type": "breeding_partner",
"year": 2025,
"confidence": null,
"source": null,
"notes": null,
"sighting1_id": "05c4c201-ef8f-49f6-9762-33851f1a848a",
"sighting2_id": "7cf27db2-af0e-445e-bea9-593b3f982ae0",
"ringing1_id": null,
"ringing2_id": null,
"created_at": "2025-09-17T15:47:45.991039",
"updated_at": "2025-09-17T15:47:45.991039"
},
{
"id": "05248381-e4df-4faf-8338-4aa37f466f58",
"bird1_ring": "282373",
"bird2_ring": "ub",
"relationship_type": "breeding_partner",
"year": 2023,
"confidence": null,
"source": "migration",
"notes": "Migrated from family_tree_entries",
"sighting1_id": null,
"sighting2_id": null,
"ringing1_id": null,
"ringing2_id": null,
"created_at": "2025-09-16T19:53:03.178758",
"updated_at": "2025-09-16T19:53:03.178758"
},
{
"id": "c108c7f8-2b68-487e-9050-119925e2f2ca",
"bird1_ring": "ub",
"bird2_ring": "282373",
"relationship_type": "breeding_partner",
"year": 2023,
"confidence": null,
"source": "migration",
"notes": "Migrated from family_tree_entries",
"sighting1_id": null,
"sighting2_id": null,
"ringing1_id": null,
"ringing2_id": null,
"created_at": "2025-09-16T19:53:03.178758",
"updated_at": "2025-09-16T19:53:03.178758"
},
{
"id": "d74f05fb-49ee-44d1-bb5b-98dd98e7ed03",
"bird1_ring": "282373",
"bird2_ring": "ub",
"relationship_type": "breeding_partner",
"year": 2023,
"confidence": null,
"source": "migration",
"notes": "Migrated from family_tree_entries",
"sighting1_id": null,
"sighting2_id": null,
"ringing1_id": null,
"ringing2_id": null,
"created_at": "2025-09-16T19:53:03.178758",
"updated_at": "2025-09-16T19:53:03.178758"
},
{
"id": "e3252dcf-6d2a-4ef5-839d-68d7173cf423",
"bird1_ring": "ub",
"bird2_ring": "282373",
"relationship_type": "breeding_partner",
"year": 2023,
"confidence": null,
"source": "migration",
"notes": "Migrated from family_tree_entries",
"sighting1_id": null,
"sighting2_id": null,
"ringing1_id": null,
"ringing2_id": null,
"created_at": "2025-09-16T19:53:03.178758",
"updated_at": "2025-09-16T19:53:03.178758"
},
{
"id": "b27d67e3-ff58-4f4b-bd23-0c5cb5c8aed3",
"bird1_ring": "282373",
"bird2_ring": "270019",
"relationship_type": "child_of",
"year": 2019,
"confidence": null,
"source": null,
"notes": null,
"sighting1_id": null,
"sighting2_id": null,
"ringing1_id": null,
"ringing2_id": null,
"created_at": "2025-09-17T15:52:52.830883",
"updated_at": "2025-09-17T15:52:52.830883"
}
]

POST {{URL}}/api/ringing

Body:
{
"ring_scheme": "DEW",
"date": "2025-09-17",
"lon": 8.75778,
"ringer": "0337",
"age": 5,
"species": "01520",
"ring": "POSTMAN1",
"place": "Offenbach, Carl-Ulrich-Brücke\*[DEED, 5818]",
"lat": 50.11167,
"sex": 0
}

Response:
{
"ring_scheme": "DEW",
"id": "cbb9989f-1d66-4599-9631-1cb0e33357ac",
"date": "2025-09-17",
"lon": 8.75778,
"ringer": "0337",
"age": 5,
"created_at": "2025-09-17T15:31:35.362260",
"species": "01520",
"ring": "POSTMAN1",
"place": "Offenbach, Carl-Ulrich-Brücke\*[DEED, 5818]",
"lat": 50.11167,
"sex": 0,
"status": null,
"updated_at": "2025-09-17T15:42:55.799850"
}

POST {{URL}}/api/family/relationships

Body:
{
"bird1_ring": "120885",
"bird2_ring": "120891",
"relationship_type": "breeding_partner",
"year": 2025
}

Response:
{
"id": "839daf32-4ba0-4fb5-ab6e-bb8e5a714141",
"bird1_ring": "120885",
"bird2_ring": "120891",
"relationship_type": "breeding_partner",
"year": 2025,
"confidence": null,
"source": null,
"notes": null,
"created_at": "2025-09-17T15:44:03.909302",
"updated_at": "2025-09-17T15:44:03.909302"
}

POST {{URL}}/api/family/relationships

Body:
{
"bird1_ring": "282373",
"bird2_ring": "282394",
"relationship_type": "breeding_partner",
"year": 2025,
"sighting1_id": "05c4c201-ef8f-49f6-9762-33851f1a848a",
"sighting2_id": "7cf27db2-af0e-445e-bea9-593b3f982ae0"
}

Response:
{
"id": "d136989d-489f-4e4f-9048-fa5ba22828af",
"bird1_ring": "282373",
"bird2_ring": "282394",
"relationship_type": "breeding_partner",
"year": 2025,
"confidence": null,
"source": null,
"notes": null,
"created_at": "2025-09-17T15:47:45.991039",
"updated_at": "2025-09-17T15:47:45.991039"
}

POST {{URL}}/api/family/relationships

{
"bird1_ring": "282373",
"bird2_ring": "270019",
"relationship_type": "child_of",
"year": 2019
}

Response:

{
"id": "b27d67e3-ff58-4f4b-bd23-0c5cb5c8aed3",
"bird1_ring": "282373",
"bird2_ring": "270019",
"relationship_type": "child_of",
"year": 2019,
"confidence": null,
"source": null,
"notes": null,
"created_at": "2025-09-17T15:52:52.830883",
"updated_at": "2025-09-17T15:52:52.830883"
}

POST {{URL}}/api/family/relationships

{
"bird1_ring": "282373",
"bird2_ring": "E12872",
"relationship_type": "parent_of",
"year": 2025,
"ringing2_id": "206904f5-c134-4d04-a265-ed30a7dcb7e5"
}

Response:
{
"id": "4fef90a4-b7c8-40df-9d48-1ad2f27e3ddf",
"bird1_ring": "282373",
"bird2_ring": "E12872",
"relationship_type": "parent_of",
"year": 2025,
"confidence": null,
"source": null,
"notes": null,
"created_at": "2025-09-17T15:56:39.578915",
"updated_at": "2025-09-17T15:56:39.578915"
}
