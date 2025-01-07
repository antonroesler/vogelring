<template>
  <div>
    <v-row>
      <v-col cols="12" class="d-flex align-center">
        <v-btn
          icon="mdi-arrow-left"
          variant="text"
          @click="handleBack"
          class="me-2"
        ></v-btn>
        <h1 class="text-h4">Eintrag Details</h1>
        <v-spacer></v-spacer>
        <v-dialog v-model="showDeleteDialog" max-width="400">
          <v-card>
            <v-card-title class="text-h5">
              Eintrag löschen
            </v-card-title>
            <v-card-text>
              Möchten Sie diesen Eintrag wirklich löschen?
            </v-card-text>
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                color="grey-darken-1"
                variant="text"
                @click="showDeleteDialog = false"
              >
                Abbrechen
              </v-btn>
              <v-btn
                color="error"
                variant="text"
                @click="confirmDelete"
                :loading="isDeleting"
              >
                Löschen
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <share-dialog :generate-html="generateStaticHTML" :get-urls="getShareableReportUrls" />
        <v-btn
          color="error"
          variant="text"
          class="ml-2"
          @click="showDeleteDialog = true"
        >
          <v-icon icon="mdi-delete" color="error"></v-icon>
          <v-tooltip activator="parent" location="bottom">
            Eintrag löschen
          </v-tooltip>
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            Sichtung bearbeiten
            <v-spacer></v-spacer>
            <span v-if="sighting?.excel_id" class="text-caption text-medium-emphasis">
              Excel ID: {{ sighting.excel_id }}
            </span>
          </v-card-title>
          <v-card-text>
            <sighting-form
              v-if="sighting"
              :sighting="sighting"
              :loading="loading"
              :is-new-entry="false"
              :show-bird-suggestions="false"
              :show-place-suggestions="false"
              :show-coordinates="false"
              @submit="updateSighting"
            />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <bird-details
          v-if="sighting?.ring"
          :bird="birdDetails"
          :ringingData="ringingData"
          class="mb-4"
        ></bird-details>
        <missing-ring-details
          v-else-if="sighting?.reading"
          :reading="sighting.reading"
          :sighting="sighting"
          class="mb-4"
        ></missing-ring-details>
      </v-col>

      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title>Sichtungen Karte</v-card-title>
          <v-card-text>
            <sightings-map
              v-if="sighting"
              :current-sighting="sighting"
              :other-sightings="birdDetails?.sightings"
              :ringing-data="ringingData"
            ></sightings-map>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title>Andere Sichtungen dieses Vogels</v-card-title>
          <v-card-text>
            <sightings-table
              v-if="otherSightings.length > 0"
              :sightings="otherSightings"
              :loading="false"
              @deleted="handleSightingDeleted"
            ></sightings-table>
            <v-alert
              v-else
              type="info"
              variant="tonal"
            >
              Keine weiteren Sichtungen gefunden
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar
      v-model="showSnackbar"
      color="success"
    >
      Eintrag erfolgreich gespeichert
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import type { Sighting, BirdMeta, Ringing } from '@/types';
import * as api from '@/api';
import SightingForm from '@/components/sightings/SightingForm.vue';
import BirdDetails from '@/components/birds/BirdDetails.vue';
import SightingsMap from '@/components/map/SightingsMap.vue';
import SightingsTable from '@/components/sightings/SightingsTable.vue';
import { useSightingsStore } from '@/stores/sightings';
import { useTheme } from 'vuetify';
import ShareDialog from '@/components/dialogs/ShareDialog.vue';
import MissingRingDetails from '@/components/birds/MissingRingDetails.vue';

const route = useRoute();
const router = useRouter();
const sighting = ref<Sighting | null>(null);
const birdDetails = ref<BirdMeta | null>(null);
const loading = ref(false);
const showSnackbar = ref(false);
const store = useSightingsStore();
const theme = useTheme();
const ringingData = ref<Ringing | null>(null);
const isLoadingRinging = ref(false);
const showDeleteDialog = ref(false);
const isDeleting = ref(false);

const loadSighting = async () => {
  const id = route.params.id as string;
  try {
    sighting.value = await api.getSightingById(id);
    if (sighting.value?.ring) {
      birdDetails.value = await api.getBirdByRing(sighting.value.ring);
      await loadRingingData(sighting.value.ring);
    }
  } catch (error) {
    console.error('Error loading sighting:', error);
  }
};

const updateSighting = async (updatedSighting: Partial<Sighting>) => {
  loading.value = true;
  try {
    await store.updateSighting(updatedSighting);
    showSnackbar.value = true;
    await loadSighting(); // Reload the current sighting details
  } catch (error) {
    console.error('Error updating sighting:', error);
  } finally {
    loading.value = false;
  }
};

// Compute other sightings, excluding the current one
const otherSightings = computed(() => {
  if (!birdDetails.value?.sightings || !sighting.value) {
    return [];
  }
  return birdDetails.value.sightings.filter(s => s.id !== sighting.value?.id);
});

const handleSightingDeleted = async (id: string) => {
  try {
    await store.deleteSighting(id);
    showSnackbar.value = true;
    await loadSighting(); // Reload the current sighting and bird details
  } catch (error) {
    console.error('Error deleting sighting:', error);
  }
};

// Add a watch on the route params
watch(
  () => route.params.id,
  (newId) => {
    if (newId) {
      loadSighting();
    }
  }
);

onMounted(loadSighting);

const generateStaticHTML = () => {
  // Helper function for date formatting
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  // Base maps configuration
  const baseMaps = {
    osm: {
      name: 'Standard',
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '© OpenStreetMap contributors'
    },
    cartoLight: {
      name: 'Hell',
      url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
      attribution: '© OpenStreetMap contributors, © CARTO'
    },
    cartoDark: {
      name: 'Dunkel',
      url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
      attribution: '© OpenStreetMap contributors, © CARTO'
    }
  };

  return `<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sighting ${sighting.value?.id}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vuetify@3.3.3/dist/vuetify.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@mdi/font@latest/css/materialdesignicons.min.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"><\/script>
    <style>
      .v-application {
        background: #fff;
        color: rgba(0, 0, 0, 0.87);
      }
      .v-card {
        border: 1px solid #E0E0E0 !important;
        box-shadow: none !important;
        margin-bottom: 16px;
      }
      .v-card-title {
        padding: 16px;
        font-size: 1.25rem;
        font-weight: 500;
      }
      .v-card-text {
        padding: 16px;
      }
      .container {
        padding: 16px;
        max-width: 1280px;
        margin: 0 auto;
      }
      .v-row {
        display: flex;
        flex-wrap: wrap;
        margin: -12px;
      }
      .v-col {
        padding: 12px;
      }
      .v-col-12 {
        flex: 0 0 100%;
        max-width: 100%;
      }
      @media (min-width: 960px) {
        .md-8 {
          flex: 0 0 66.666667%;
          max-width: 66.666667%;
        }
        .md-4 {
          flex: 0 0 33.333333%;
          max-width: 33.333333%;
        }
      }
      .v-table {
        width: 100%;
        border-collapse: collapse;
      }
      .v-table th, .v-table td {
        padding: 8px;
        text-align: left;
        border-bottom: 1px solid #E0E0E0;
      }
      #map {
        height: 400px;
        margin-bottom: 20px;
        z-index: 0;
      }
      .map-controls {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: white;
        padding: 5px;
        border-radius: 4px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      }
      .map-controls select {
        padding: 4px;
        border-radius: 4px;
        border: 1px solid #ccc;
      }
    </style>
  </head>
  <body>
    <div class="v-application">
      <div class="v-main">
        <div class="container">
          <h1 class="text-h4 mb-4">Eintrag Details</h1>
          
          <div class="v-row">
            <div class="v-col v-col-12 md-8">
              <div class="v-card">
                <div class="v-card-title">Sichtung Details</div>
                <div class="v-card-text">
                  <div class="v-row">
                    <div class="v-col v-col-12 md-6">
                      <p><strong>Ablesung:</strong> ${sighting.value?.reading || '-'}</p>
                      <p><strong>Ring:</strong> ${sighting.value?.ring || '-'}</p>
                      <p><strong>Spezies:</strong> ${sighting.value?.species || '-'}</p>
                      <p><strong>Ort:</strong> ${sighting.value?.place || '-'}</p>
                    </div>
                    <div class="v-col v-col-12 md-6">
                      <p><strong>Gruppengröße:</strong> ${sighting.value?.group_size || '-'}</p>
                      <p><strong>Melder:</strong> ${sighting.value?.melder || '-'}</p>
                      <p><strong>Gemeldet:</strong> ${sighting.value?.melded ? 'Ja' : 'Nein'}</p>
                      <p><strong>Kommentare:</strong> ${sighting.value?.comment || '-'}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            ${birdDetails.value ? `
              <div class="v-col v-col-12 md-4">
                <div class="v-card">
                  <div class="v-card-title">Vogel Details</div>
                  <div class="v-card-text">
                    <p><strong>Ring:</strong> ${birdDetails.value.ring || '-'}</p>
                    <p><strong>Spezies:</strong> ${birdDetails.value.species || '-'}</p>
                    <p><strong>Erste Sichtung:</strong> ${birdDetails.value.first_seen ? formatDate(birdDetails.value.first_seen) : '-'}</p>
                    <p><strong>Letzte Sichtung:</strong> ${birdDetails.value.last_seen ? formatDate(birdDetails.value.last_seen) : '-'}</p>
                  </div>
                </div>
                ${ringingData.value ? `
                  <div class="v-card mt-4">
                    <div class="v-card-title">Beringungsdaten</div>
                    <div class="v-card-text">
                      <p><strong>Beringungsdatum:</strong> ${formatDate(ringingData.value.date)}</p>
                      <p><strong>Beringungsort:</strong> ${ringingData.value.place}</p>
                      <p><strong>Beringer:</strong> ${ringingData.value.ringer}</p>
                      <p><strong>Ring Schema:</strong> ${ringingData.value.ring_scheme}</p>
                      <p><strong>Alter bei Beringung:</strong> ${formatAge(ringingData.value.age)}</p>
                      <p><strong>Geschlecht:</strong> ${formatSex(ringingData.value.sex)}</p>
                    </div>
                  </div>
                ` : ''}
              </div>
            ` : ''}
          </div>

          <div id="map"></div>

          ${otherSightings.value.length > 0 ? `
            <div class="v-card">
              <div class="v-card-title">Andere Sichtungen</div>
              <div class="v-card-text">
                <table class="v-table">
                  <thead>
                    <tr>
                      <th>Datum</th>
                      <th>Ort</th>
                      <th>Ring</th>
                      <th>Spezies</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${otherSightings.value.map(s => `
                      <tr>
                        <td>${formatDate(s.date)}</td>
                        <td>${s.place || '-'}</td>
                        <td>${s.ring || '-'}</td>
                        <td>${s.species || '-'}</td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    </div>

    <script>
      window.onload = function() {
        // Base maps configuration
        const baseMaps = {
          osm: {
            name: 'Standard',
            url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            attribution: '© OpenStreetMap contributors'
          },
          cartoLight: {
            name: 'Hell',
            url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
            attribution: '© OpenStreetMap contributors, © CARTO'
          },
          cartoDark: {
            name: 'Dunkel',
            url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
            attribution: '© OpenStreetMap contributors, © CARTO'
          }
        };

        // Create map controls
        const mapControls = document.createElement('div');
        mapControls.className = 'map-controls';
        const select = document.createElement('select');
        select.innerHTML = \`
          <option value="osm">Standard</option>
          <option value="cartoLight">Hell</option>
          <option value="cartoDark">Dunkel</option>
        \`;
        mapControls.appendChild(select);
        document.getElementById('map').appendChild(mapControls);

        const map = L.map('map').setView([${sighting.value?.lat || 50.1109}, ${sighting.value?.lon || 8.6821}], 13);
        let currentLayer = L.tileLayer(baseMaps.osm.url, {
          attribution: baseMaps.osm.attribution
        }).addTo(map);

        // Handle base map changes
        select.onchange = function(e) {
          const selectedMap = baseMaps[e.target.value];
          if (currentLayer) {
            map.removeLayer(currentLayer);
          }
          currentLayer = L.tileLayer(selectedMap.url, {
            attribution: selectedMap.attribution
          }).addTo(map);
        };

        // Define custom icons
        const currentIcon = L.divIcon({
          html: '<div style="background-color: #FF4444; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white;"></div>',
          className: 'custom-div-icon',
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });

        const otherIcon = L.divIcon({
          html: '<div style="background-color: #FFB300; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>',
          className: 'custom-div-icon',
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        });

        const ringingIcon = L.divIcon({
          html: '<div style="background-color: #4CAF50; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white;"></div>',
          className: 'custom-div-icon',
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });

        // Add current sighting marker
        L.marker(
          [${sighting.value?.lat || 50.1109}, ${sighting.value?.lon || 8.6821}],
          { icon: currentIcon }
        )
          .addTo(map)
          .bindPopup(\`Aktuelle Sichtung (${formatDate(sighting.value?.date)})\`);

        // Add ringing marker if available
        ${ringingData.value ? `
          L.marker([${ringingData.value.lat}, ${ringingData.value.lon}], { icon: ringingIcon })
            .addTo(map)
            .bindPopup(\`Beringungsort (${formatDate(ringingData.value.date)})\`);
        ` : ''}

        // Add other sightings markers
        ${JSON.stringify(otherSightings.value)}.forEach(s => {
          if (s.lat && s.lon) {
            L.marker([s.lat, s.lon], { icon: otherIcon })
              .addTo(map)
              .bindPopup(\`Sichtung am \${new Date(s.date).toLocaleDateString('de-DE', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
              })}\`);
          }
        });

        // Add CSS for markers
        const style = document.createElement('style');
        style.textContent = \`
          .custom-div-icon {
            background: none !important;
            border: none !important;
          }
          .custom-div-icon div {
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
          }
        \`;
        document.head.appendChild(style);
      };
    <\/script>
  </body>
</html>`;
};

const loadRingingData = async (ring: string) => {
  isLoadingRinging.value = true;
  try {
    ringingData.value = await api.getRingingByRing(ring);
  } catch (error) {
    console.error('Error loading ringing data:', error);
  } finally {
    isLoadingRinging.value = false;
  }
};

const formatAge = (age: number) => {
  switch (age) {
    case 1: return 'Nestling / nicht voll flugfähiges Küken (1)';
    case 2: return 'Fängling (2)';
    case 3: return 'diesjährig (3)';
    case 4: return 'nicht diesjährig (4)';
    case 5: return 'vorjährig (5)';
    case 6: return 'älter als vorjährig (6)';
    case 7: return 'im 3. Kalender Jahr (7)';
    case 8: return 'über 3 Jahre alt (8)';
    case 9: return 'im 4. Kalenderjahr (9)';
    case 10: return 'über 4 Jahre alt (10)';
    case 11: return 'im 5. Kalenderjahr (11)';
    case 12: return 'über 5 Jahre alt (12)';
    default: return `Code ${age}`;
  }
};

const formatSex = (sex: number) => {
  switch (sex) {
    case 1: return 'Männlich (1)';
    case 2: return 'Weiblich (2)';
    case 0: return 'Unbekannt (0)';
    default: return `Code ${sex}`;
  }
};

const getShareableReportUrls = async (days: number) => {
  try {
    const htmlContent = generateStaticHTML();
    console.log('Generated HTML content:', htmlContent?.substring(0, 100) + '...');  // Log first 100 chars
    return await api.getShareableReportUrls(days, htmlContent);
  } catch (error) {
    console.error('Error generating shareable report:', error);
    throw error;
  }
};

const confirmDelete = async () => {
  if (!sighting.value?.id) return;
  
  isDeleting.value = true;
  try {
    await store.deleteSighting(sighting.value.id);
    showDeleteDialog.value = false;
    // Navigate back to the entries list
    router.push('/entries');
  } catch (error) {
    console.error('Error deleting sighting:', error);
  } finally {
    isDeleting.value = false;
  }
};

const handleBack = () => {
  router.push({
    path: '/entries',
    query: { from: 'detail' }
  });
};
</script>