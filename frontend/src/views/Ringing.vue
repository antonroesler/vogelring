<template>
  <div>
    <v-tabs v-model="activeTab" color="primary">
      <v-tab value="search">Beringung suchen</v-tab>
      <v-tab value="add">Neue Beringung</v-tab>
      <v-tab value="list">Eintragliste</v-tab>
    </v-tabs>

    <v-window v-model="activeTab" class="mt-4">
      <!-- Search Tab -->
      <v-window-item value="search">
        <v-card>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="searchRing"
                  label="Ringnummer"
                  placeholder="Ringnummer eingeben"
                  @keyup.enter="searchRinging"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6" class="d-flex align-center">
                <v-btn
                  color="primary"
                  @click="searchRinging"
                  :loading="isSearching"
                  :disabled="!searchRing"
                >
                  Suchen
                </v-btn>
              </v-col>
            </v-row>

            <!-- Search Results -->
            <v-alert
              v-if="searchError"
              type="error"
              class="mt-4"
            >
              {{ searchError }}
            </v-alert>

            <v-card
              v-if="foundRinging"
              class="mt-4"
              variant="outlined"
            >
              <v-card-text>
                <v-list>
                  <v-list-item>
                    <v-list-item-title>Ring</v-list-item-title>
                    <v-list-item-subtitle>{{ foundRinging.ring }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Ring Schema</v-list-item-title>
                    <v-list-item-subtitle>{{ foundRinging.ring_scheme }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Spezies</v-list-item-title>
                    <v-list-item-subtitle>{{ foundRinging.species }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Datum</v-list-item-title>
                    <v-list-item-subtitle>{{ formatDate(foundRinging.date) }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Ort</v-list-item-title>
                    <v-list-item-subtitle>{{ foundRinging.place }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Beringer</v-list-item-title>
                    <v-list-item-subtitle>{{ foundRinging.ringer }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Alter</v-list-item-title>
                    <v-list-item-subtitle>{{ formatAge(foundRinging.age) }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Geschlecht</v-list-item-title>
                    <v-list-item-subtitle>{{ formatSex(foundRinging.sex) }}</v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="foundRinging.status">
                    <v-list-item-title>Status</v-list-item-title>
                    <v-list-item-subtitle>
                      <v-chip
                        v-if="foundRinging.status"
                        :color="getBirdStatusColor(foundRinging.status)"
                        size="small"
                        variant="tonal"
                      >
                        <v-icon 
                          v-if="getBirdStatusIcon(foundRinging.status)"
                          :icon="getBirdStatusIcon(foundRinging.status)"
                          size="x-small"
                          class="mr-1"
                        ></v-icon>
                        {{ formatBirdStatus(foundRinging.status) }}
                      </v-chip>
                      <span v-else>-</span>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item>
                    <v-list-item-title>Koordinaten</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ formatCoordinates(foundRinging.lat, foundRinging.lon) }}
                      <v-btn
                        icon="mdi-map-marker"
                        size="small"
                        variant="text"
                        density="compact"
                        :href="getGoogleMapsLink(foundRinging.lat, foundRinging.lon)"
                        target="_blank"
                        class="ms-2"
                        v-tooltip="'In Google Maps öffnen'"
                      ></v-btn>
                    </v-list-item-subtitle>
                  </v-list-item>
                  <v-list-item v-if="foundRinging.comment">
                    <v-list-item-title>Kommentar</v-list-item-title>
                    <v-list-item-subtitle>{{ foundRinging.comment }}</v-list-item-subtitle>
                  </v-list-item>
                </v-list>

                <v-card-actions>
                  <v-spacer></v-spacer>
                  <v-btn
                    color="error"
                    variant="outlined"
                    @click="confirmDelete"
                    :loading="isDeleting"
                  >
                    Beringung löschen
                  </v-btn>
                </v-card-actions>
              </v-card-text>
            </v-card>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- Add Tab -->
      <v-window-item value="add">
        <v-card>
          <v-card-text>
            <v-form ref="form" v-model="isFormValid" @submit.prevent="submitForm">
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="newRinging.ring"
                    label="Ringnummer*"
                    :rules="[v => !!v || 'Ringnummer ist erforderlich']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="newRinging.ring_scheme"
                    label="Ring Schema*"
                    :rules="[v => !!v || 'Ring Schema ist erforderlich']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-autocomplete
                    v-model="newRinging.species"
                    :items="filteredSpecies"
                    label="Spezies*"
                    @update:search="filterSpecies"
                    :loading="!suggestions.species.length"
                    :no-data-text="'Keine Spezies verfügbar'"
                    autocomplete="off"
                    :rules="[v => !!v || 'Spezies ist erforderlich']"
                    :filter="() => true"
                    :return-object="false"
                    density="comfortable"
                  ></v-autocomplete>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="newRinging.date"
                    label="Datum*"
                    type="date"
                    :rules="[v => !!v || 'Datum ist erforderlich']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-autocomplete
                    v-model="newRinging.place"
                    :items="filteredPlaces"
                    label="Ort*"
                    @update:search="filterPlaces"
                    :loading="!suggestions.places.length"
                    :no-data-text="'Keine Orte verfügbar'"
                    autocomplete="off"
                    :rules="[v => !!v || 'Ort ist erforderlich']"
                    :filter="() => true"
                    :return-object="false"
                    density="comfortable"
                  ></v-autocomplete>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="newRinging.ringer"
                    label="Beringer*"
                    :rules="[v => !!v || 'Beringer ist erforderlich']"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="newRinging.age"
                    label="Alter*"
                    :items="ageOptions"
                    item-title="text"
                    item-value="value"
                    :rules="[v => v !== undefined || 'Alter ist erforderlich']"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="newRinging.sex"
                    label="Geschlecht*"
                    :items="sexOptions"
                    item-title="text"
                    item-value="value"
                    :rules="[v => v !== undefined || 'Geschlecht ist erforderlich']"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="newRinging.status"
                    label="Status"
                    :items="statusOptions"
                    item-title="text"
                    item-value="value"
                    clearable
                  ></v-select>
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="newRinging.comment"
                    label="Kommentar"
                    placeholder="Zusätzliche Notizen zur Beringung..."
                    rows="3"
                    auto-grow
                    clearable
                  ></v-textarea>
                </v-col>
              </v-row>

              <!-- Parent Fields Section -->
              <v-card-subtitle class="px-0 mt-4">Eltern (optional)</v-card-subtitle>
              <v-row>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="parent1Ring"
                    label="Elternteil 1 Ring"
                    hint="Optional: Ring des ersten Elternteils"
                    persistent-hint
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="parent1Sex"
                    label="Geschlecht Elternteil 1"
                    :items="parentSexOptions"
                    item-title="text"
                    item-value="value"
                    :disabled="!parent1Ring"
                  ></v-select>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="parent2Ring"
                    label="Elternteil 2 Ring"
                    hint="Optional: Ring des zweiten Elternteils"
                    persistent-hint
                  ></v-text-field>
                </v-col>
                <v-col cols="12" sm="6">
                  <v-select
                    v-model="parent2Sex"
                    label="Geschlecht Elternteil 2"
                    :items="parentSexOptions"
                    item-title="text"
                    item-value="value"
                    :disabled="!parent2Ring"
                  ></v-select>
                </v-col>
              </v-row>

              <!-- Map Section -->
              <v-card-subtitle class="px-0 mt-4">Standort*</v-card-subtitle>
              <v-row>
                <v-col cols="12">
                  <leaflet-map
                    v-model:latitude="latitude"
                    v-model:longitude="longitude"
                    :show-default-marker="false"
                    @marker-placed="handleMarkerPlaced"
                  ></leaflet-map>
                  
                  <v-row v-if="showCoordinates && hasCoordinates" class="mt-2" dense>
                    <v-col cols="6">
                      <v-text-field
                        v-model="latitude"
                        label="Breitengrad"
                        readonly
                        density="compact"
                      ></v-text-field>
                    </v-col>
                    <v-col cols="6">
                      <v-text-field
                        v-model="longitude"
                        label="Längengrad"
                        readonly
                        density="compact"
                      ></v-text-field>
                    </v-col>
                  </v-row>
                </v-col>
              </v-row>

              <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn
                  color="primary"
                  type="submit"
                  :loading="isSubmitting"
                  :disabled="!isFormValid"
                >
                  {{ isUpdateMode ? 'Beringung aktualisieren' : 'Beringung speichern' }}
                </v-btn>
              </v-card-actions>
            </v-form>
          </v-card-text>
        </v-card>
      </v-window-item>

      <!-- Entry List Tab -->
      <v-window-item value="list">
        <ringing-entry-list />
      </v-window-item>
    </v-window>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>Beringung löschen</v-card-title>
        <v-card-text>
          Möchten Sie diese Beringung wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="showDeleteDialog = false">Abbrechen</v-btn>
          <v-btn color="error" @click="deleteRingingData" :loading="isDeleting">Löschen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
    >
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="snackbar.show = false"
        >
          Schließen
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted } from 'vue';
import { format } from 'date-fns';
import { formatBirdStatus, getBirdStatusColor, getBirdStatusIcon } from '@/utils/statusUtils';
import type { Ringing } from '@/types';
import { BirdStatus } from '@/types';
import * as api from '@/api';
import LeafletMap from '@/components/map/LeafletMap.vue';
import RingingEntryList from '@/views/RingingEntryList.vue';
import { getRingingAgeOptions, formatRingingAge } from '@/utils/ageMapping';

const activeTab = ref('search');
const searchRing = ref('');
const foundRinging = ref<Ringing | null>(null);
const isSearching = ref(false);
const isDeleting = ref(false);
const isSubmitting = ref(false);
const searchError = ref('');
const showDeleteDialog = ref(false);
const form = ref();
const isFormValid = ref(false);
const isUpdateMode = ref(false);

// Parent fields
const parent1Ring = ref('');
const parent1Sex = ref<'M' | 'W' | 'U'>('U');
const parent2Ring = ref('');
const parent2Sex = ref<'M' | 'W' | 'U'>('U');

const snackbar = reactive({
  show: false,
  text: '',
  color: 'success'
});

const suggestions = ref<{places: string[], species: string[]}>({
  places: [],
  species: []
});

const filteredPlaces = ref<string[]>([]);
const filteredSpecies = ref<string[]>([]);

const showCoordinates = ref(true);

// Define newRinging BEFORE any functions that might use it
const newRinging = reactive({
  ring: '',
  ring_scheme: '',
  species: '',
  date: '',
  place: '',
  ringer: '',
  age: undefined as number | undefined,
  sex: undefined as number | undefined,
  status: undefined as string | undefined,
  comment: '',
  lat: undefined as number | undefined,
  lon: undefined as number | undefined
});

const hasCoordinates = computed(() => {
  return typeof latitude.value === 'number' && 
         typeof longitude.value === 'number' &&
         !isNaN(latitude.value) && 
         !isNaN(longitude.value);
});

const handleMarkerPlaced = () => {
  // Update the form validation when marker is placed
  form.value?.validate();
};

const latitude = computed({
  get: () => newRinging.lat,
  set: (val) => {
    newRinging.lat = val;
  }
});

const longitude = computed({
  get: () => newRinging.lon,
  set: (val) => {
    newRinging.lon = val;
  }
});

// Load suggestions when component mounts
onMounted(async () => {
  try {
    const response = await api.api.get('/suggestions');
    suggestions.value = {
      places: Array.isArray(response.data.places) ? response.data.places : [],
      species: Array.isArray(response.data.species) ? response.data.species : []
    };
    filteredPlaces.value = suggestions.value.places;
    filteredSpecies.value = suggestions.value.species;
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    showNotification('Fehler beim Laden der Vorschläge', true);
  }
});

const createFilter = (field: keyof typeof suggestions.value) => {
  return (input: string) => {
    const targetRef = computed(() => {
      switch(field) {
        case 'places': return filteredPlaces;
        case 'species': return filteredSpecies;
        default: return { value: [] };
      }
    });

    const sourceArray = suggestions.value[field] || [];

    if (!input) {
      targetRef.value.value = sourceArray;
      return;
    }
    
    const searchTerm = input.toLowerCase().trim();
    const filtered = sourceArray
      .filter(item => item && item.toLowerCase().includes(searchTerm))
      .slice(0, 5);
    
    if (searchTerm && !filtered.includes(input)) {
      filtered.unshift(input);
    }
    
    targetRef.value.value = filtered;
  };
};

const filterPlaces = createFilter('places');
const filterSpecies = createFilter('species');

// Watch for changes in the ring number field in the add/edit form
watch(() => newRinging.ring, async (newValue) => {
  if (!newValue) return;
  
  try {
    const existingRinging = await api.getRingingByRing(newValue);
    if (existingRinging) {
      // Prefill form with existing data
      Object.assign(newRinging, {
        ...existingRinging,
        date: existingRinging.date.split('T')[0] // Format date for input field
      });
      isUpdateMode.value = true;
      showNotification('Beringung gefunden. Daten wurden vorausgefüllt.', false);
    } else {
      isUpdateMode.value = false;
    }
  } catch (error) {
    console.error('Error checking ring:', error);
  }
});

const ageOptions = getRingingAgeOptions(true);

const sexOptions = [
  { text: 'Männlich (1)', value: 1 },
  { text: 'Weiblich (2)', value: 2 },
  { text: 'Unbekannt (0)', value: 0 }
];

const statusOptions = [
  { text: 'Brutvogel', value: 'BV' },
  { text: 'Mausergast', value: 'MG' },
  { text: 'Nichtbrüter', value: 'NB' },
  { text: 'Reviervogel', value: 'RV' },
  { text: 'Totfund', value: 'TF' }
];

const parentSexOptions = [
  { text: 'Männlich', value: 'M' },
  { text: 'Weiblich', value: 'W' },
  { text: 'Unbekannt', value: 'U' }
];

const formatDate = (date: string) => {
  return format(new Date(date), 'dd.MM.yyyy');
};

const formatAge = (age: number) => {
  return formatRingingAge(age, true);
};

const formatSex = (sex: number) => {
  const option = sexOptions.find(opt => opt.value === sex);
  return option ? option.text : `Code ${sex}`;
};


const formatCoordinates = (lat: number, lon: number) => {
  return `${lat.toFixed(6)}°, ${lon.toFixed(6)}°`;
};

const getGoogleMapsLink = (lat: number, lon: number) => {
  return `https://www.google.com/maps?q=${lat},${lon}`;
};

const searchRinging = async () => {
  if (!searchRing.value) return;

  isSearching.value = true;
  searchError.value = '';
  foundRinging.value = null;

  try {
    const result = await api.getRingingByRing(searchRing.value);
    if (result) {
      foundRinging.value = result;
      showNotification('Beringung gefunden.');
    } else {
      searchError.value = 'Keine Beringung mit dieser Ringnummer gefunden.';
    }
  } catch (error) {
    console.error('Error searching ringing:', error);
    searchError.value = 'Fehler beim Suchen der Beringung.';
    showNotification('Fehler beim Suchen der Beringung.', true);
  } finally {
    isSearching.value = false;
  }
};

const confirmDelete = () => {
  showDeleteDialog.value = true;
};

const deleteRingingData = async () => {
  if (!foundRinging.value) return;

  isDeleting.value = true;
  try {
    await api.deleteRinging(foundRinging.value.ring);
    foundRinging.value = null;
    searchRing.value = '';
    showDeleteDialog.value = false;
    showNotification('Beringung wurde erfolgreich gelöscht.');
  } catch (error) {
    console.error('Error deleting ringing:', error);
    showNotification('Fehler beim Löschen der Beringung.', true);
  } finally {
    isDeleting.value = false;
  }
};

const showNotification = (text: string, isError = false) => {
  snackbar.text = text;
  snackbar.color = isError ? 'error' : 'success';
  snackbar.show = true;
};

const submitForm = async () => {
  const formValue = form.value;
  if (!formValue) return;

  const { valid } = await formValue.validate();
  if (!valid) return;

  isSubmitting.value = true;
  try {
    // First, create or update the ringing
    const ringingData = {
      ...newRinging,
      status: newRinging.status as BirdStatus | undefined
    };
    
    if (isUpdateMode.value) {
      await api.updateRinging(ringingData);
      showNotification('Beringung wurde erfolgreich aktualisiert.');
    } else {
      await api.createRinging(ringingData);
      showNotification('Beringung wurde erfolgreich erstellt.');
    }

    // Then, add parent relationships if provided
    const currentYear = new Date().getFullYear();
    
    // Get the created ringing ID once if we have parent relationships to create
    let ringingId: string | undefined = undefined;
    if (parent1Ring.value || parent2Ring.value) {
      try {
        const createdRinging = await api.getRingingByRing(newRinging.ring);
        ringingId = createdRinging?.id;
      } catch (error) {
        console.error('Error fetching created ringing:', error);
      }
    }
    
    if (parent1Ring.value) {
      try {
        await api.createRelationship({
          bird1_ring: parent1Ring.value,
          bird2_ring: newRinging.ring,
          relationship_type: 'parent_of',
          year: currentYear,
          ringing2_id: ringingId
        });
        await api.createRelationship({
          bird1_ring: newRinging.ring,
          bird2_ring: parent1Ring.value,
          relationship_type: 'child_of',
          year: currentYear,
          ringing1_id: ringingId
        });
        showNotification(`Eltern-Kind-Beziehung zu ${parent1Ring.value} hinzugefügt.`);
      } catch (error) {
        console.error('Error adding parent 1 relationship:', error);
        showNotification(`Warnung: Beziehung zu ${parent1Ring.value} konnte nicht hinzugefügt werden.`, true);
      }
    }

    if (parent2Ring.value) {
      try {
        await api.createRelationship({
          bird1_ring: parent2Ring.value,
          bird2_ring: newRinging.ring,
          relationship_type: 'parent_of',
          year: currentYear,
          ringing2_id: ringingId
        });
        await api.createRelationship({
          bird1_ring: newRinging.ring,
          bird2_ring: parent2Ring.value,
          relationship_type: 'child_of',
          year: currentYear,
          ringing1_id: ringingId
        });
        showNotification(`Eltern-Kind-Beziehung zu ${parent2Ring.value} hinzugefügt.`);
      } catch (error) {
        console.error('Error adding parent 2 relationship:', error);
        showNotification(`Warnung: Beziehung zu ${parent2Ring.value} konnte nicht hinzugefügt werden.`, true);
      }
    }
    
    // Store current values that should be preserved
    const preservedValues = {
      date: newRinging.date,
      ringer: newRinging.ringer,
      ring_scheme: newRinging.ring_scheme,
      place: newRinging.place,
      species: newRinging.species,
      lat: newRinging.lat,
      lon: newRinging.lon,
      status: newRinging.status
    };
    
    // Reset form
    formValue.reset();
    
    // Restore preserved values
    Object.assign(newRinging, {
      ring: '',
      ring_scheme: preservedValues.ring_scheme,
      species: preservedValues.species,
      date: preservedValues.date,
      place: preservedValues.place,
      ringer: preservedValues.ringer,
      age: undefined,
      sex: undefined,
      status: preservedValues.status,
      comment: '',
      lat: preservedValues.lat,
      lon: preservedValues.lon
    });

    // Reset parent fields
    parent1Ring.value = '';
    parent1Sex.value = 'U';
    parent2Ring.value = '';
    parent2Sex.value = 'U';
    
    isUpdateMode.value = false;
  } catch (error) {
    console.error('Error saving ringing:', error);
    showNotification(
      `Fehler beim ${isUpdateMode.value ? 'Aktualisieren' : 'Erstellen'} der Beringung.`,
      true
    );
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.v-list-item-subtitle {
  display: flex;
  align-items: center;
}
</style>