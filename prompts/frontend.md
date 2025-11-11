You are a senior frontend dev. You work on vogelring. A single user bird ring database of sightings and ringings. We recently migrated from a serverless system to server and from DynamoDB to a postrgres database. We just adapted out Family relationship models to the new DB. You might see references to the old FamilyTree Model in the frontend, if you see them remove them.

We have the following relations:
Ist Brutpartner von
Ist Kind von
Ist Elternteil von
Ist Nestgeschwister von

Note that these relation ships SHALL be able to exist independent from Sightings or Ringings. But can be also mapped to either.
Each relationship sets two rings (str) in relation ship, for those rings, ringing data might exist or not.
A relationship also includes at least a year, for when it was valid, as partners change (sometime even within on year) and its relevant for the Nestgeschwister relation to know in which year.
Users (in the frontend mask) SHALL be able to create relationships for a sighting, then, the relationship is connected to two sightings (as two birds have been seen in a relationship, two sightings will be created and one relationship will be created, mapping those two rings and is connetcted to both sightings)
This means that even for one year and two birds that are partners there can be many entries for that exact relationship fro different sightings.
There shall be some application object level abstractions, for example to easily and simple get all the partners of one bird with no duplications (per year) for example.
Similarly a relationship can also be created together with a ringing. E.g. A user might enter a ringing of bird a with 5 chicks. That creates in total 6 ringing entries and quite a bunch of relation ships: 5 Ist Elternteil von, 5 Ist Kind von and then one Ist Nestgeschwister von for each chick to all the others.

We will build all that into that application. Take a look at the api. Take a look at the samples i provided. Then finish by adjusting the frontend (Add the option to add children / partner to a ringing (for children user also ust set thte ringing age)). Same for sightings, add a component that allows the insertion of an entire family sighting and that creates the respective relationships in the back. Then for the bird detail view we shall be able to show some sort of family tree for a bird, and quickly visit its parents, siblings, or childrens.

It is your task to extent the frontend. Make the new models available in the code. Adapt the UI:

- Int the bird detail page, add a component that visualizes the family tree and lets the user to quickly jump to the related birds or ringing / sighting events that are connected to relationship
- When creating sightings, let users add a relationship as described above
- Same for ringings

/context add /Users/anton/Projects/vogelring/backend/src/api/routers/family.py /Users/anton/Projects/vogelring/sample_api_calls.md /Users/anton/Projects/vogelring/backend/src/database/family_repository.py /Users/anton/Projects/vogelring/backend/src/api/routers/ringings.py /Users/anton/Projects/vogelring/backend/src/api/routers/sightings.py /Users/anton/Projects/vogelring/frontend/src/**/\*.ts /Users/anton/Projects/vogelring/frontend/src/**/_.vue /Users/anton/Projects/vogelring/frontend/_.html /Users/anton/Projects/vogelring/frontend/\*.json

Remeber your task: (You are almost done but just keep in mind waht was to do): You are a senior frontend dev. You work on vogelring. A single user bird ring database of sightings and ringings. We recently migrated from a serverless system to server and from DynamoDB to a postrgres database. We just adapted out Family relationship models to the new DB. You might see references to the old FamilyTree Model in the frontend, if you see them remove them.

We have the following relations:
Ist Brutpartner von
Ist Kind von
Ist Elternteil von
Ist Nestgeschwister von

Note that these relation ships SHALL be able to exist independent from Sightings or Ringings. But can be also mapped to either.
Each relationship sets two rings (str) in relation ship, for those rings, ringing data might exist or not.
A relationship also includes at least a year, for when it was valid, as partners change (sometime even within on year) and its relevant for the Nestgeschwister relation to know in which year.
Users (in the frontend mask) SHALL be able to create relationships for a sighting, then, the relationship is connected to two sightings (as two birds have been seen in a relationship, two sightings will be created and one relationship will be created, mapping those two rings and is connetcted to both sightings)
This means that even for one year and two birds that are partners there can be many entries for that exact relationship fro different sightings.
There shall be some application object level abstractions, for example to easily and simple get all the partners of one bird with no duplications (per year) for example.
Similarly a relationship can also be created together with a ringing. E.g. A user might enter a ringing of bird a with 5 chicks. That creates in total 6 ringing entries and quite a bunch of relation ships: 5 Ist Elternteil von, 5 Ist Kind von and then one Ist Nestgeschwister von for each chick to all the others.

We will build all that into that application. Take a look at the api. Take a look at the samples i provided. Then finish by adjusting the frontend (Add the option to add children / partner to a ringing (for children user also ust set thte ringing age)). Same for sightings, add a component that allows the insertion of an entire family sighting and that creates the respective relationships in the back. Then for the bird detail view we shall be able to show some sort of family tree for a bird, and quickly visit its parents, siblings, or childrens.

It is your task to extent the frontend. Make the new models available in the code. Adapt the UI:

- Int the bird detail page, add a component that visualizes the family tree and lets the user to quickly jump to the related birds or ringing / sighting events that are connected to relationship
- When creating sightings, let users add a relationship as described above
- Same for ringings

Then came Task 2 after 1 was done:

1. Partner: Partner is already part of the base form and thus it is not necessary to add partner to the family Modal. 2. THe Modal: I would like to not have a modal tha pop up over the rest, rather id like to have it this way: unter kommenta and above the map, users can click a button to add a rows (one click one row) in each row there is as we have it now a ring of a child and a age selector. 3. Now we need a confirmation dialog that appears when the user clicks save. Because what happens per default is that the sighting that the user wants to create gets created, but vogelring is smart and can figure out that if the user gave a parter (that is not ub or UB or unberingt as ring value) then there shall be a sighting for the partner too with otherwise identical infos. Same for the kids. But this needs to be confirmed by the user. So before saving, if there is a partner and or kids, we need a confirmation dialog with short summary of what will be created and a back button that goes back to the page and let the user edit.

Now i have this Problem:

When i click the Familie erstellen button in "Familie erstellen - Bestätigung Folgende Sichtungen werden erstellt:..." i get this: SightingForm.BWFZytWB.js:1
Error creating family sighting: TypeError: le.createSighting is not a function
at Ie (SightingForm.BWFZytWB.js:1:16220)
at Rd (index.CbnF75f9.js:14:1387)
at Gr (index.CbnF75f9.js:14:1458)
at f$ (index.CbnF75f9.js:15:33387)
at d (SightingForm.BWFZytWB.js:1:9709)
at index.CbnF75f9.js:19:8805
at Rd (index.CbnF75f9.js:14:1387)
at Gr (index.CbnF75f9.js:14:1458)
at Gr (index.CbnF75f9.js:14:1568)
at HTMLButtonElement.n (index.CbnF75f9.js:19:8589)
Ie @ SightingForm.BWFZytWB.js:1
Rd @ index.CbnF75f9.js:14
Gr @ index.CbnF75f9.js:14
f$ @ index.CbnF75f9.js:15
d @ SightingForm.BWFZytWB.js:1
(anonymous) @ index.CbnF75f9.js:19
Rd @ index.CbnF75f9.js:14
Gr @ index.CbnF75f9.js:14
Gr @ index.CbnF75f9.js:14
n @ index.CbnF75f9.js:19

no network requests were sent.

---

Good that does. But still issues: The api calls are actually made when the Speichern button is pressed. Then the confirmation modal opens and nothing happens when the confirmation button is pressed, that of course makes no sense, the api calls shall only be made when the button in the confirmation modal are made, thats what this whole thing is for right :D
2: The partner field of course have to be switched.
If user puts in Ring A and Partner B then in the partner sighting (currently) the sighting is Ring B and Partner B (but of course it shall be Partner A). The reading (ablesung) shall be empty for partner (and for children too). The comment shall be set to: "Diese Sichtung wurde automatisch generiert" (for partner and children). For children the Partner field shall of course be empty. 

---

Into the child row add the following fields, and do NOT overtake from parent sighting: 
- Geschlecht

For children, is parent field Familien Status is set to value "Verpaart" then set it as empty, and do NOT overtake from parent sighting, otherwise overtake the value 

For children set as empty, and do NOT overtake from parent sighting: 
- Status 
- Nicht Flügge Junge
- Flügge Junge

For Parters: if Geschlecht (sex) is set to M then set Partner to W and revers, if empty then also empty for partner.


Now it seems like the api calls to /api/family/relationship are missing. 

