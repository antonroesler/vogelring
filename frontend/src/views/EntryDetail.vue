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
              :use-store-pagination="false"
              :default-page="1"
              :default-items-per-page="10"
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
    // Check if coordinates have changed
    if (sighting.value && (
      updatedSighting.lat !== sighting.value.lat || 
      updatedSighting.lon !== sighting.value.lon
    )) {
      updatedSighting.is_exact_location = true;
    }
    
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
    <title>Sichtungsbericht ${sighting.value?.id}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/vuetify@3.3.3/dist/vuetify.min.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@mdi/font@latest/css/materialdesignicons.min.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"><\/script>
    <style>
      :root {
        --primary-color: #2c3e50;
        --border-color: #dee2e6;
        --header-bg: #f8f9fa;
      }
      body {
        font-family: "Helvetica Neue", Arial, sans-serif;
        line-height: 1.5;
        color: var(--primary-color);
        max-width: 1200px;
        margin: 0 auto;
        padding: 16px;
      }
      .report-header {
        background: var(--header-bg);
        padding: 20px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
      }
      .report-title {
        margin-bottom: 8px;
      }
      .report-subtitle {
        color: var(--primary-color);
        font-size: 1.2em;
        font-weight: normal;
        margin: 4px 0 16px 0;
        border-bottom: none;
        padding: 0;
        margin-top: 0;
      }
      .report-meta {
        color: #666;
        font-size: 0.9em;
        padding-top: 16px;
        margin-top: 16px;
        border-top: 1px solid var(--border-color);
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 8px;
      }
      .meta-item {
        display: flex;
        align-items: center;
      }
      .meta-label {
        font-weight: 500;
        margin-right: 8px;
        color: var(--primary-color);
      }
      h1, h2, h3 {
        color: var(--primary-color);
        margin: 0;
      }
      h1 {
        font-size: 1.6em;
        font-weight: 500;
      }
      h2 {
        font-size: 1.3em;
        padding: 12px 0;
        margin-top: 24px;
        border-bottom: 2px solid var(--border-color);
      }
      table {
        width: 100%;
        border-collapse: collapse;
        margin: 12px 0;
        font-size: 0.95em;
      }
      th, td {
        border: 1px solid var(--border-color);
        padding: 8px;
        text-align: left;
      }
      th {
        background: var(--header-bg);
        font-weight: 500;
      }
      .map-container {
        margin: 16px 0;
        border: 1px solid var(--border-color);
        padding: 12px;
        border-radius: 4px;
      }
      #map {
        height: 500px;
        margin-bottom: 12px;
        border-radius: 4px;
      }
      .map-legend {
        background: white;
        padding: 12px;
        border: 1px solid var(--border-color);
        font-size: 0.9em;
        border-radius: 4px;
      }
      .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 4px;
      }
      .legend-color {
        width: 16px;
        height: 16px;
        margin-right: 8px;
        border: 1px solid var(--border-color);
        border-radius: 50%;
      }
      .section {
        margin-bottom: 24px;
      }
      .field-label {
        font-weight: 500;
        min-width: 150px;
        color: var(--primary-color);
      }
      .coordinates {
        font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
      }
      @media print {
        body {
          padding: 0;
        }
        .map-container {
          page-break-inside: avoid;
        }
      }
    </style>
  </head>
  <body>
    <div class="report-header">
      <h1 class="report-title">Sichtungsbericht</h1>
      <h2 class="report-subtitle">
        für ${sighting.value?.ring || sighting.value?.reading || '-'} 
        am ${sighting.value?.date ? formatDate(sighting.value.date) : '-'}
        ${sighting.value?.place ? `(${sighting.value.place})` : ''}
      </h2>
      <div class="report-meta">
        <div class="meta-item">
          <span class="meta-label">ID:</span>
          <span>${sighting.value?.id || '-'}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Erstellt am:</span>
          <span>${new Date().toLocaleDateString('de-DE')}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Gültig bis:</span>
          <span>${new Date(Date.now() + (86400000 * 30)).toLocaleDateString('de-DE')}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h2>1. Sichtungsdetails</h2>
      <table>
        <tr>
          <td class="field-label">Datum</td>
          <td>${formatDate(sighting.value?.date || '')}</td>
        </tr>
        <tr>
          <td class="field-label">Ablesung</td>
          <td>${sighting.value?.reading || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Ring</td>
          <td>${sighting.value?.ring || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Spezies</td>
          <td>${sighting.value?.species || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Ort</td>
          <td>${sighting.value?.place || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Bereich</td>
          <td>${sighting.value?.area || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Habitat</td>
          <td>${sighting.value?.habitat || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Feldobst</td>
          <td>${sighting.value?.field_fruit || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Gruppengröße</td>
          <td>${sighting.value?.group_size || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Kleine Gruppe</td>
          <td>${sighting.value?.small_group_size || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Große Gruppe</td>
          <td>${sighting.value?.large_group_size || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Status</td>
          <td>${sighting.value?.status || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Alter</td>
          <td>${sighting.value?.age || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Brutgröße</td>
          <td>${sighting.value?.breed_size || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Familienstand</td>
          <td>${sighting.value?.pair || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Geschlecht</td>
          <td>${sighting.value?.sex || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Koordinaten</td>
          <td class="coordinates">${sighting.value?.lat ? `${sighting.value.lat}, ${sighting.value.lon}` : '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Melder</td>
          <td>${sighting.value?.melder || '-'}</td>
        </tr>
        <tr>
          <td class="field-label">Kommentar</td>
          <td>${sighting.value?.comment || '-'}</td>
        </tr>
      </table>
    </div>

    ${birdDetails.value ? `
      <div class="section">
        <h2>2. Vogelhistorie</h2>
        <table>
          <tr>
            <td class="field-label">Ring</td>
            <td>${birdDetails.value.ring || '-'}</td>
          </tr>
          <tr>
            <td class="field-label">Spezies</td>
            <td>${birdDetails.value.species || '-'}</td>
          </tr>
          <tr>
            <td class="field-label">Erste Sichtung</td>
            <td>${birdDetails.value.first_seen ? formatDate(birdDetails.value.first_seen) : '-'}</td>
          </tr>
          <tr>
            <td class="field-label">Letzte Sichtung</td>
            <td>${birdDetails.value.last_seen ? formatDate(birdDetails.value.last_seen) : '-'}</td>
          </tr>
          <tr>
            <td class="field-label">Anzahl Sichtungen</td>
            <td>${birdDetails.value.sighting_count}</td>
          </tr>
        </table>
      </div>
    ` : ''}

    ${ringingData.value ? `
      <div class="section">
        <h2>3. Beringungsdaten</h2>
        <table>
          <tr>
            <td class="field-label">Beringungsdatum</td>
            <td>${formatDate(ringingData.value.date)}</td>
          </tr>
          <tr>
            <td class="field-label">Beringungsort</td>
            <td>${ringingData.value.place}</td>
          </tr>
          <tr>
            <td class="field-label">Beringer</td>
            <td>${ringingData.value.ringer}</td>
          </tr>
          <tr>
            <td class="field-label">Ring Schema</td>
            <td>${ringingData.value.ring_scheme}</td>
          </tr>
          <tr>
            <td class="field-label">Alter bei Beringung</td>
            <td>${formatAge(ringingData.value.age)}</td>
          </tr>
          <tr>
            <td class="field-label">Geschlecht</td>
            <td>${formatSex(ringingData.value.sex)}</td>
          </tr>
        </table>
      </div>
    ` : ''}

    <div class="section">
      <h2>4. Sichtungskarte</h2>
      <div class="map-container">
        <div id="map"></div>
        <div class="map-legend">
          <div class="legend-item">
            <div class="legend-color" style="background-color: #FF4444;"></div>
            <span>Aktuelle Sichtung</span>
          </div>
          <div class="legend-item">
            <div class="legend-color" style="background-color: #FFB300;"></div>
            <span>Vergangene Sichtung</span>
          </div>
          ${ringingData.value ? `
            <div class="legend-item">
              <div class="legend-color" style="background-color: #4CAF50;"></div>
              <span>Beringungsort</span>
            </div>
          ` : ''}
        </div>
      </div>
    </div>

    ${otherSightings.value.length > 0 ? `
      <div class="section">
        <h2>5. Weitere Sichtungen</h2>
        <table>
          <thead>
            <tr>
              <th>Datum</th>
              <th>Ort</th>
              <th>Ring</th>
              <th>Spezies</th>
              <th>Status</th>
              <th>Alter</th>
            </tr>
          </thead>
          <tbody>
            ${otherSightings.value.map(s => `
              <tr>
                <td>${s.date ? formatDate(s.date) : '-'}</td>
                <td>${s.place || '-'}</td>
                <td>${s.ring || '-'}</td>
                <td>${s.species || '-'}</td>
                <td>${s.status || '-'}</td>
                <td>${s.age || '-'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    ` : ''}

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
          .bindPopup(\`Aktuelle Sichtung (${sighting.value?.date ? formatDate(sighting.value.date) : '-'})\`);

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
              .bindPopup(\`Sichtung am \${s.date ? new Date(s.date).toLocaleDateString('de-DE', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
              }) : '-'}\`);
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