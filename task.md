This is vogelring, it is a web app that runs on AWS. The frontend on S3 + Cloudfront and the backend on lambda (there is one write and one reader function; this is due to the fact that i dont use a DB, to keep cost at a bare minimum and instead read and write to a file) i now have my own server up and running on a raspberry pi 5, with cloudflare tunnels set up. So you job is to migrate this application to my pi. Most importantly the backend which is optimizied from an aws lambda funtion and serverless in general. We also shall now implement a simple database that we also run on the pi, everything with docker compose. 

Now keep things simple. We do not require comprehensive testing, but some happy path api test would be great. 

Note that we do not need to over complicate things. This is meant as a single user application (all code that refers to multiple users may be removed in the refactoring, there was the idea to have multiple users, but we dont need this anymore). This app was build to replace an excel file from my dad. 



Note that we actually do use a db (dynamo) for the ringings. Each ringing is a event where a bird gets a ring on its foot. There are about 6000 ringing records, and db is growing very slowly, so you dont need to worry about sacle and simple db will do just fine). Then we have sightings (currently stored as a pickle file, which is loaded into memory of the lambda, this is the main data of the application). Each Sightings is one event where a bird with a ring is seen, note that it is possible that this bird exists or does not exist in the ringing table). 



Note that the frontend uses field suggestions and autocomplete so it needs to be ensured that the db can be queried quickly in all columns. 



There are about 8000 sightings and this is also only growing slowly, like a few hundered a year, so no worries about scale. 



Let us start with this. There is more to come later, but let us now only focus on this. In this branch we are on you can remove all the aws sam stuff too, as we do not need it anymore, but do not destroy any infra, just rewrite it so that everything runs locally with docker compose. 