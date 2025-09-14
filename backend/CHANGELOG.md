# Changelog

All notable changes to the Vogelring Backend will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0](https://github.com/antonroesler/vogelring/compare/v1.0.0...v1.1.0) (2025-09-14)


### ✨ Features

* add age selection to SightingForm and update related models ([4ae3180](https://github.com/antonroesler/vogelring/commit/4ae318091d95cb05568ff1681cf465e71db7eae2))
* add api key ([b818c13](https://github.com/antonroesler/vogelring/commit/b818c13529df77d4749562ad266b4c8641c7f261))
* add ClearFieldsSettings component and integrate with NewEntry view ([3e65dd4](https://github.com/antonroesler/vogelring/commit/3e65dd43d96e1d77f1dc99e2c33159a89f32f3e0))
* add CRUD endpoints for ringing data management ([7583821](https://github.com/antonroesler/vogelring/commit/75838218c2253b2b728fc962e65ba40f5c118dac))
* add customizable settings for sightings table ([#23](https://github.com/antonroesler/vogelring/issues/23)) ([3e7a660](https://github.com/antonroesler/vogelring/commit/3e7a660448cc202724c21d8ee8f4e67ad3776767))
* add date ([53f8792](https://github.com/antonroesler/vogelring/commit/53f8792e7d4365a6cfdf270fa46abd31ba6a5ea2))
* add date field to sighting form and enhance entry detail display ([a31e97f](https://github.com/antonroesler/vogelring/commit/a31e97f88156962d3489eadbed32087aa680b263))
* add delete confirmation dialog to EntryDetail view ([8b98042](https://github.com/antonroesler/vogelring/commit/8b98042a411d49157b536a6e45ac2a7dd068361c))
* add environment analysis ([88971f8](https://github.com/antonroesler/vogelring/commit/88971f84dfb8160b7122f06604256f1c514538f9))
* add family tree API endpoints ([968a604](https://github.com/antonroesler/vogelring/commit/968a604e10e6d9e439e185cc5f88911b0499dded))
* add family tree management functionality ([f8d4dff](https://github.com/antonroesler/vogelring/commit/f8d4dffb895d3bb2171fe3ae28f8663250cc4b50))
* add lodash for debouncing and enhance App.vue with search functionality ([c038122](https://github.com/antonroesler/vogelring/commit/c03812278045be177e1529d169c080d6368fb5a4))
* add melded status indicator to SightingsTable component ([d0b0091](https://github.com/antonroesler/vogelring/commit/d0b0091d23515997d92bf42baf8f576f675af05f))
* add MissingRingDetails component for handling unassigned bird rings ([bee6d98](https://github.com/antonroesler/vogelring/commit/bee6d988fdd3135b33bdd61c8109092bf21c35eb))
* add partner field to sightings and update related components ([0b9b83e](https://github.com/antonroesler/vogelring/commit/0b9b83e456c7145de6363e22d7fd26997d4f57f6))
* add partners feature to bird metadata and update BirdDetail.vue ([4d401b9](https://github.com/antonroesler/vogelring/commit/4d401b9f172e2a5ed23c81ded46d6c980201588e))
* add ringing data ([030090c](https://github.com/antonroesler/vogelring/commit/030090cad3773931f27352d1b78ab7d6a6c31402))
* add Ringing view with search, create, update, and delete functionality ([06adf5c](https://github.com/antonroesler/vogelring/commit/06adf5c1984c1791f219a4c2b6b4b449d77585b3))
* add seasonal analysis view with comprehensive bird sighting statistics ([6a983da](https://github.com/antonroesler/vogelring/commit/6a983dabc9f39a63a93dd8738e1a92ecd949b06a))
* add sex attribute to sighting models and form ([8f43388](https://github.com/antonroesler/vogelring/commit/8f433888b39e6c2787875be1c6bd464ada164cdd))
* add sorting for duplicate entries in DataQualityView and clean up sightings update logic ([#31](https://github.com/antonroesler/vogelring/issues/31)) ([a6f66ec](https://github.com/antonroesler/vogelring/commit/a6f66ecbc34c3fe757f2b808b497b102321ffbe3))
* add species autocomplete to SightingForm and API endpoint for species list ([4a82e83](https://github.com/antonroesler/vogelring/commit/4a82e838e151b1aeddc2f5fd32accc8568482ef4))
* analytics endpoint ([4ad84d8](https://github.com/antonroesler/vogelring/commit/4ad84d82fca7f3221f513f2c8d3e57cdab805555))
* api to upsert data ([a09fc3f](https://github.com/antonroesler/vogelring/commit/a09fc3f8fbe954c29c1ec8b74b62848f09ccc7ac))
* authorizer ([f5ecdc5](https://github.com/antonroesler/vogelring/commit/f5ecdc59401e9d7f26554e5484c9bb09b8618482))
* bird detail view ([d3931ea](https://github.com/antonroesler/vogelring/commit/d3931eac74242add897249b577d2ebb6f6a12504))
* dashboard ([8b33004](https://github.com/antonroesler/vogelring/commit/8b3300487c5029e38a53684f24c0cfba8a5a9142))
* deploy to s3 ([f75e3e1](https://github.com/antonroesler/vogelring/commit/f75e3e19aec5a2908eaba22da0513cbc3a607a25))
* different base maps ([15b9295](https://github.com/antonroesler/vogelring/commit/15b9295f54789b07452e87afdd0468695f8e5330))
* display application version in App.vue header ([d73d654](https://github.com/antonroesler/vogelring/commit/d73d65494ae791eb2fc602ac8c222f4f2e9cf161))
* enhance bird data fetching with improved error handling and API configuration ([fdd8f83](https://github.com/antonroesler/vogelring/commit/fdd8f83ef09b7cb81e1eb19fcfe51cd46031989b))
* enhance bird retrieval and details display ([978100a](https://github.com/antonroesler/vogelring/commit/978100ac7b86b9e99deec86876305f9ef53f9043))
* enhance bird suggestions ([46ee3e6](https://github.com/antonroesler/vogelring/commit/46ee3e6ae298430d4bf85789ea41ca070056bf5b))
* enhance DynamoDB interactions for ringing data management ([1f9bcd3](https://github.com/antonroesler/vogelring/commit/1f9bcd3b9fb4894f9af02567e3b14ce76fffa325))
* enhance environment analysis with offset coordinates for sightings and improve popup design ([9c93310](https://github.com/antonroesler/vogelring/commit/9c93310498d390e11beed4886ed58627c5f5fee1))
* enhance FriendsMap and SightingsMap with improved sighting details and filtering ([0f0cfc2](https://github.com/antonroesler/vogelring/commit/0f0cfc2a007c4ae95d93e41675691d5f70be455b))
* enhance FriendsMap with improved marker clustering and zoom behavior ([8b9b6c4](https://github.com/antonroesler/vogelring/commit/8b9b6c4bf573ae94e01317f2da728b74f8beb661))
* enhance frontend with caching, improved suggestions & report ([74231f6](https://github.com/antonroesler/vogelring/commit/74231f6f6a71baafc951a0dac25d2526341e26c4))
* enhance LeafletMap and SightingForm with improved marker handling and coordinate management ([c93756c](https://github.com/antonroesler/vogelring/commit/c93756c0a9dd1e0c6345d0aa8ee0ebab410677fe))
* enhance NewEntry component with success and error notifications ([11b0336](https://github.com/antonroesler/vogelring/commit/11b0336c7b7ce6b75bc92067a0121bcfbc00de0e))
* enhance Ring API with separate reader and writer Lambda functions ([4cf6abc](https://github.com/antonroesler/vogelring/commit/4cf6abcf15b16446a0ad1a417e33d359bc3ec2ca))
* enhance SightingForm and models with new fields for breed size, family size, and pairing type ([0e54116](https://github.com/antonroesler/vogelring/commit/0e54116b60b79d14cb71d96a258e588430d8c66a))
* enhance SightingForm with additional fields and improve suggestion handling ([9b65adf](https://github.com/antonroesler/vogelring/commit/9b65adf641c89aaa0640e420200d15bcbff976b1))
* enhance SightingForm with additional fields and improved layout ([eddc610](https://github.com/antonroesler/vogelring/commit/eddc61080fd405600e997a742c9d22b3cec55200))
* enhance sightings management with improved filtering and pagination ([78ea6b9](https://github.com/antonroesler/vogelring/commit/78ea6b95965af0a239a4b0610944e62e1b75c507))
* enhance SightingsFilter and EntryList with new filtering options ([788973a](https://github.com/antonroesler/vogelring/commit/788973a73709c592a3ac393b7559527e8dbf992b))
* enhance SightingsTable and store with melded state management ([6e89918](https://github.com/antonroesler/vogelring/commit/6e8991882de682db688729c165badf817c8f0abb))
* enhance SightingsTable with configurable pagination options ([be6ee98](https://github.com/antonroesler/vogelring/commit/be6ee9818639179b7e53edacfd486225b01253d0))
* favicon ([e4a835b](https://github.com/antonroesler/vogelring/commit/e4a835bb8a905b4da4d113233c1cdd5b8c1b90ff))
* filters in get sightings endpoint ([68106e6](https://github.com/antonroesler/vogelring/commit/68106e69776b5dc8f4b9722ef104185191b864e6))
* frontend ([6dceadd](https://github.com/antonroesler/vogelring/commit/6dceadd5433c88b91650fe21d35e740618bf05b1))
* frontend redesign ([#12](https://github.com/antonroesler/vogelring/issues/12)) ([7f6604c](https://github.com/antonroesler/vogelring/commit/7f6604c1277d39f8be51fddbe73b141df1802381))
* implement autocomplete suggestions for SightingForm and add new API endpoint ([685fba6](https://github.com/antonroesler/vogelring/commit/685fba67d4cc150271956d41654a2de9012f7080))
* implement debounced fetching of bird suggestions and improve display logic ([be2b2bc](https://github.com/antonroesler/vogelring/commit/be2b2bc325f9a77be5a7a8171e3e4a95debfc4cd))
* implement statistics routing and enhance statistics views ([d25d16e](https://github.com/antonroesler/vogelring/commit/d25d16e2d9a88d7a3ba3b34ff06eed36ea34e302))
* integrate leaflet.markercluster for improved map marker management ([0db1f5b](https://github.com/antonroesler/vogelring/commit/0db1f5b3180d4afc6695b33040f16cb742742805))
* more filter options & reload data only on demand ([986964c](https://github.com/antonroesler/vogelring/commit/986964c38273580974ffe21a2355be1ad9e30a19))
* more info in shareable html report ([206317c](https://github.com/antonroesler/vogelring/commit/206317c0b54d76bffc4ce903868efe7cca24e0c0))
* place suggestion ([04cfb95](https://github.com/antonroesler/vogelring/commit/04cfb95d8be833c3740d9f856b250ab531a89f47))
* radius statistics ([936dadf](https://github.com/antonroesler/vogelring/commit/936dadf8b3a70e03fc6dca8f41bfbffff12e4b9d))
* rate limiter ([4655cad](https://github.com/antonroesler/vogelring/commit/4655cada91a5d35f74fdde4a8243475db68a08f0))
* **ring-api:** read sightings and birds ([343ac01](https://github.com/antonroesler/vogelring/commit/343ac016e56e2116cbb9cffa428665a671cf5114))
* shareable report ([2735b54](https://github.com/antonroesler/vogelring/commit/2735b54bc6fc4c773e97db450e2215f4ab134ff5))
* show lat and lon ([7ef9dac](https://github.com/antonroesler/vogelring/commit/7ef9dacd7b3e36efb31c1eca1c93888f46dcf4e7))
* show other sightings in detail view ([638d01b](https://github.com/antonroesler/vogelring/commit/638d01b7ae6d9313f77ff8ff9b11ed334edab243))
* update BirdDetail.vue to sort partners and increment API version ([c3121cd](https://github.com/antonroesler/vogelring/commit/c3121cdd0ae1717a105f709858f4f2da2074394a))
* update BirdDetail.vue with heatmap visualization for bird sightings ([0cf795f](https://github.com/antonroesler/vogelring/commit/0cf795fcb9b0e2a57e980e9dcd7ed971ebf02fc8))
* update converter to handle new CSV structure and enhance data extraction ([b1a008c](https://github.com/antonroesler/vogelring/commit/b1a008c0224b2284e001610c30913db3f7891688))
* update Sighting model and API version to include new bird status and age fields ([0ca33f4](https://github.com/antonroesler/vogelring/commit/0ca33f4b5b966a4d44caece4f55db9a9a573dffe))
* update SightingForm and models with new bird status option ([06b5efb](https://github.com/antonroesler/vogelring/commit/06b5efb0a7c12a53c5df6a85a6091e6755f37dbc))
* user data separation  ([#13](https://github.com/antonroesler/vogelring/issues/13)) ([193f3c4](https://github.com/antonroesler/vogelring/commit/193f3c45015b3b94be6963da0ce3fc26f42977ec))


### 🐛 Bug Fixes

* allow new values for place ([c21ef8c](https://github.com/antonroesler/vogelring/commit/c21ef8c3a47aeb2c69d8b0f5e20d985833d176d1))
* base map in generated report ([0d22ab7](https://github.com/antonroesler/vogelring/commit/0d22ab77442a12494847b534a0a34e619094f03d))
* click on row event ([e22a788](https://github.com/antonroesler/vogelring/commit/e22a7884260b7a25a0699310ac4353f7b873002f))
* compute lat lon ([52d8348](https://github.com/antonroesler/vogelring/commit/52d8348eb9dd6bb3b766f5ad776a86bb1e7dd7d2))
* convert to add `lat`and `lon` correctly ([a0a5040](https://github.com/antonroesler/vogelring/commit/a0a5040d29ba74d8efeb186756785024da16f979))
* dashboard last 12 month ([a9d30f4](https://github.com/antonroesler/vogelring/commit/a9d30f4105da6d53e9f85b7f170644dab4f9adac))
* fix addition logic in family tree partner entry ([7a467f3](https://github.com/antonroesler/vogelring/commit/7a467f31ea49adc1d81b8c3beb916e2a49b8c30e))
* function name ([d92d78e](https://github.com/antonroesler/vogelring/commit/d92d78edf62acc1b0956e11d28e18f72e4c220a5))
* increase API timeout ([e95737c](https://github.com/antonroesler/vogelring/commit/e95737c49d8b67efeedc22795cc9e1f95ba13bd4))
* json format friends ([7c6eb36](https://github.com/antonroesler/vogelring/commit/7c6eb3664777ac58a557761be86a859c05996e3e))
* load map correctly if no lat/lon for current sighting ([5efaf17](https://github.com/antonroesler/vogelring/commit/5efaf17a2365839345be00ee45eebc7c19368e90))
* map marker ([b36635c](https://github.com/antonroesler/vogelring/commit/b36635c855f22bfea32e4bb4482e901d6b0e9554))
* order in timeline chart ([0821b9e](https://github.com/antonroesler/vogelring/commit/0821b9e29912904648a4a250c9aa7fa38f17cf1a))
* prevent NoneType rings from being included in friend sightings ([1726782](https://github.com/antonroesler/vogelring/commit/172678251d5ef25ac51c664048f5dca13796ba35))
* shareable report functionality: updated API to accept HTML content, modified ShareDialog component for improved user experience, and adjusted backend to handle new report generation logic. Added ShareableReport type for better type safety. ([193b615](https://github.com/antonroesler/vogelring/commit/193b61528db794948795415c0904795c360d091d))
* smaller bug fixes ([25fe1a8](https://github.com/antonroesler/vogelring/commit/25fe1a8965c416a5cde5bd8f21a9c0681284676e))
* typo ([2c1752f](https://github.com/antonroesler/vogelring/commit/2c1752f4f9f9df7d49d68320a6839aabc1159b15))
* ui bug fixes ([#22](https://github.com/antonroesler/vogelring/issues/22)) ([f06cda0](https://github.com/antonroesler/vogelring/commit/f06cda077095358618b2fa9697a8db2de03d3eb2))
* update label for Paar Status to Familien Status [#22](https://github.com/antonroesler/vogelring/issues/22) ([#30](https://github.com/antonroesler/vogelring/issues/30)) ([7959755](https://github.com/antonroesler/vogelring/commit/795975557c1e5856b57b5b8b95e61b6533a087ff))


### 🔧 Miscellaneous

* add gitignore ([c219cd9](https://github.com/antonroesler/vogelring/commit/c219cd910bb70845c363d62b67eb63764e9a31df))
* data conversion ([8ec097c](https://github.com/antonroesler/vogelring/commit/8ec097c3a386de813a70df868cc1a4986e197ae8))
* ignore user file ([2ee8072](https://github.com/antonroesler/vogelring/commit/2ee8072ab260bf4015b2e2b4e52d7f44c1e1c8d1))
* no version bump on each deploy ([b01dd52](https://github.com/antonroesler/vogelring/commit/b01dd52dc6699d6375a1445c71c86672f4db7fe1))
* nothing ([2312836](https://github.com/antonroesler/vogelring/commit/23128367a046e27ff815cfc02deffab32eeb9ff7))
* python setup ([7a39f61](https://github.com/antonroesler/vogelring/commit/7a39f61199f8c2047b1b12c126e5eaff88ea29fb))
* run frontend script ([b81573f](https://github.com/antonroesler/vogelring/commit/b81573f29c3152c594e6a83029b8b162813db889))
* scripts ([a6644cd](https://github.com/antonroesler/vogelring/commit/a6644cd7a4f01939961b7a4a9cf671b499251ad8))
* update aws-lambda-powertools to 3.2.0 ([41c9e02](https://github.com/antonroesler/vogelring/commit/41c9e025602708c6299884419aedeab3e390f0d3))


### ♻️ Code Refactoring

* `src` -&gt; `scripts` ([ad710dc](https://github.com/antonroesler/vogelring/commit/ad710dcadae887c945be5f5655a938052b6edf17))
* comparison statistic ([84f299e](https://github.com/antonroesler/vogelring/commit/84f299e82e95d83fabd2634a15225843b7868a46))
* improve version handling and data processing in API ([1271fac](https://github.com/antonroesler/vogelring/commit/1271fac84d071951ff6c5d9debb0e88e4f2d40a4))
* streamline sighting deletion process and enhance API error handling ([d80ae24](https://github.com/antonroesler/vogelring/commit/d80ae249b67798acf2b9ee573784a1870715fa80))
* theme ([b52f3aa](https://github.com/antonroesler/vogelring/commit/b52f3aad84599b54c7a7288a32afe18ae5cbf50e))
* update BirdMeta interface and enhance BirdDetail and EnvironmentAnalysis views ([4a3cdc5](https://github.com/antonroesler/vogelring/commit/4a3cdc5e89b7c3feadda4032315e2668639462f2))


### 🧪 Tests

* add service and api tests ([5e6738e](https://github.com/antonroesler/vogelring/commit/5e6738e6a7e48a7170a1b4d27b1a005220b5b193))


### 👷 Continuous Integration

* add token to release please ([#28](https://github.com/antonroesler/vogelring/issues/28)) ([9ea4066](https://github.com/antonroesler/vogelring/commit/9ea406633aa44fbe22a53488c6eda55920e873da))
* releaseing ([#26](https://github.com/antonroesler/vogelring/issues/26)) ([8f386c1](https://github.com/antonroesler/vogelring/commit/8f386c1874f431d98321c7fd6bf49d80bad5984e))
* update release workflow branch from main to master ([#27](https://github.com/antonroesler/vogelring/issues/27)) ([e0879c5](https://github.com/antonroesler/vogelring/commit/e0879c57ff6014d2f92672595081addcc2f3de8e))
* update release-please config and changelog ([#32](https://github.com/antonroesler/vogelring/issues/32)) ([68f8d33](https://github.com/antonroesler/vogelring/commit/68f8d339e8265f065bb5580344d287fb683057d7))

## [1.0.0] - 2025-01-01

### Features

- Initial release of Vogelring
