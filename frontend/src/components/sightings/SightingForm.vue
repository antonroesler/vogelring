<template>
  <v-form @submit.prevent="saveSighting">
    <!-- Group 1: Date and Place -->
    <v-row dense align="center" class="header-row">
      <v-col>
        <v-card-subtitle class="px-0">Datum und Ort</v-card-subtitle>
      </v-col>
      <v-col cols="auto">
        <v-btn
          variant="text"
          color="secondary"
          density="comfortable"
          class="extra-fields-btn"
          @click="showAdditionalFields = !showAdditionalFields"
        >
          Extra Felder
          <v-icon :icon="showAdditionalFields ? 'mdi-chevron-up' : 'mdi-chevron-down'" class="ml-1"></v-icon>
        </v-btn>
      </v-col>
    </v-row>
    <v-row dense>
      <!-- First row -->
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.date"
          label="Datum"
          type="date"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-autocomplete
          v-if="showPlaceSuggestions"
          v-model="localSighting.place"
          :items="filteredPlaces"
          label="Ort"
          @update:search="filterPlaces"
          :loading="!suggestions.places.length"
          :no-data-text="'Keine Orte verfügbar'"
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
        <v-text-field
          v-else
          v-model="localSighting.place"
          label="Ort"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-autocomplete
          v-model="localSighting.habitat"
          :items="filteredHabitats"
          label="Habitat"
          @update:search="filterHabitats"
          :loading="!suggestions.habitats.length"
          :no-data-text="'Keine Habitate verfügbar'"
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
      </v-col>
    </v-row>

    <!-- Additional fields -->
    <v-row dense v-if="showAdditionalFields">
      <v-col cols="12" sm="4" md="4">
        <!-- Empty column -->
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.area"
          label="Kleinfläche"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-autocomplete
          v-model="localSighting.field_fruit"
          :items="filteredFieldFruits"
          label="Feldfrucht"
          @update:search="filterFieldFruits"
          :loading="!suggestions.field_fruits.length"
          :no-data-text="'Keine Feldfrüchte verfügbar'"
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
      </v-col>
    </v-row>

    <!-- Group 2: Bird Identification -->
    <v-card-subtitle class="px-0 mt-4">Vogelidentifikation</v-card-subtitle>
    <v-row dense>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.reading"
          label="Ablesung"
          density="comfortable"
        >
          <template v-if="showBirdSuggestions" v-slot:append-inner>
            <bird-suggestions
              :reading="localSighting.reading || ''"
              @select="handleSuggestionSelect"
            ></bird-suggestions>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.ring"
          label="Ring"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-autocomplete
          v-model="localSighting.species"
          :items="filteredSpecies"
          label="Spezies"
          @update:search="filterSpecies"
          :loading="!suggestions.species.length"
          hide-no-data
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
      </v-col>
    </v-row>

    <!-- Group 3: Additional Information -->
    <v-card-subtitle class="px-0 mt-4">Zusätzliche Informationen</v-card-subtitle>
    <v-row dense>
      <!-- First row -->
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.partner"
          label="Partner"
          density="comfortable"
        >
          <template v-if="showBirdSuggestions" v-slot:append-inner>
            <bird-suggestions
              :reading="localSighting.partner || ''"
              @select="handlePartnerSelect"
            ></bird-suggestions>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.small_group_size"
          label="Kleingruppe"
          type="number"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.large_group_size"
          label="Großgruppe"
          type="number"
          density="comfortable"
        ></v-text-field>
      </v-col>

      <!-- Add new row for breed_size and family_size -->
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.breed_size"
          label="Nicht flügge Junge"
          type="number"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.family_size"
          label="Flügge Junge"
          type="number"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-select
          v-model="localSighting.pair"
          :items="pairItems"
          label="Paar Status"
          density="comfortable"
          clearable
        ></v-select>
      </v-col>

      <!-- Second row -->
      <v-col cols="12" sm="4" md="4">
        <v-select
          v-model="localSighting.status"
          :items="statusItems"
          label="Status"
          density="comfortable"
          clearable
        ></v-select>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-select
          v-model="localSighting.age"
          :items="ageItems"
          label="Alter"
          density="comfortable"
          clearable
        ></v-select>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-select
          v-model="localSighting.sex"
          :items="sexItems"
          label="Geschlecht"
          density="comfortable"
          clearable
        ></v-select>
      </v-col>

      <!-- Third row -->
      <v-col cols="12" sm="4" md="4">
        <v-autocomplete
          v-model="localSighting.melder"
          :items="filteredMelders"
          label="Melder"
          @update:search="filterMelders"
          :loading="!suggestions.melders.length"
          :no-data-text="'Keine Melder verfügbar'"
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-checkbox
          v-model="localSighting.melded"
          label="Gemeldet"
          density="comfortable"
        ></v-checkbox>
      </v-col>
    </v-row>

    <!-- Comments -->
    <v-card-subtitle class="px-0 mt-4">Kommentar</v-card-subtitle>
    <v-row>
      <v-col cols="12">
        <v-textarea
          v-model="localSighting.comment"
          label="Kommentare"
          density="comfortable"
        ></v-textarea>
      </v-col>
    </v-row>

    <!-- Map -->
    <v-card-subtitle class="px-0 mt-4">Standort</v-card-subtitle>
    <v-row>
      <v-col cols="12">
        <leaflet-map
          v-model:latitude="latitude"
          v-model:longitude="longitude"
          :show-default-marker="false"
          @marker-placed="handleMarkerPlaced"
        ></leaflet-map>
        
        <!-- Add location accuracy toggle when coordinates are set -->
        <v-row v-if="hasCoordinates" class="mt-2" dense>
          <v-col cols="12">
            <v-checkbox
              v-model="localSighting.is_exact_location"
              label="Exakter Standort"
              density="comfortable"
              hint="Deaktivieren Sie diese Option, wenn der Standort nicht genau ist"
            ></v-checkbox>
          </v-col>
        </v-row>

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

    <v-card-actions class="mt-4">
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        type="submit"
        :loading="loading"
        size="large"
        variant="elevated"
        class="px-8"
        :prepend-icon="isNewEntry ? 'mdi-content-save' : undefined"
      >
        Speichern
      </v-btn>
    </v-card-actions>
  </v-form>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import type { Sighting, BirdMeta, SuggestionLists } from '@/types';
import { BirdStatus, BirdAge, PairType } from '@/types';
import LeafletMap from '@/components/map/LeafletMap.vue';
import BirdSuggestions from '@/components/birds/BirdSuggestions.vue';
import { api } from '@/api';

const props = defineProps<{
  sighting: Partial<Sighting>;
  loading?: boolean;
  isNewEntry?: boolean;
  showBirdSuggestions?: boolean;
  showPlaceSuggestions?: boolean;
  showCoordinates?: boolean;
}>();

const emit = defineEmits<{
  'submit': [sighting: Partial<Sighting>];
}>();

const localSighting = ref<Partial<Sighting>>({ ...props.sighting });
const suggestions = ref<SuggestionLists>({
  places: [],
  species: [],
  habitats: [],
  melders: [],
  field_fruits: []
});

const filteredPlaces = ref<string[]>([]);
const filteredSpecies = ref<string[]>([]);
const filteredHabitats = ref<string[]>([]);
const filteredMelders = ref<string[]>([]);
const filteredFieldFruits = ref<string[]>([]);

const statusItems = [
  { title: 'Brutvogel', value: BirdStatus.BV },
  { title: 'Mausergast', value: BirdStatus.MG },
  { title: 'Nichtbrüter', value: BirdStatus.NB },
  { title: 'Reviervogel', value: BirdStatus.RV }
];

const ageItems = [
  { title: 'Adult', value: BirdAge.AD },
  { title: 'Diesjährig', value: BirdAge.DJ },
  { title: 'Vorjährig', value: BirdAge.VJ },
  { title: 'Juvenil', value: BirdAge.JUV }
];

const sexItems = [
  { title: 'Männlich', value: 'M' },
  { title: 'Weiblich', value: 'W' }
];

const pairItems = [
  { title: 'Verpaart', value: PairType.PAIRED },
  { title: 'Familie', value: PairType.FAMILY },
  { title: 'Schule', value: PairType.SCHOOL }
];

const showAdditionalFields = ref(false);

onMounted(async () => {
  try {
    const response = await api.get('/suggestions');
    suggestions.value = {
      places: Array.isArray(response.data.places) ? response.data.places : [],
      species: Array.isArray(response.data.species) ? response.data.species : [],
      habitats: Array.isArray(response.data.habitats) ? response.data.habitats : [],
      melders: Array.isArray(response.data.melders) ? response.data.melders : [],
      field_fruits: Array.isArray(response.data.field_fruits) ? response.data.field_fruits : []
    };

    filteredPlaces.value = suggestions.value.places;
    filteredSpecies.value = suggestions.value.species;
    filteredHabitats.value = suggestions.value.habitats;
    filteredMelders.value = suggestions.value.melders;
    filteredFieldFruits.value = suggestions.value.field_fruits;
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    suggestions.value = {
      places: [],
      species: [],
      habitats: [],
      melders: [],
      field_fruits: []
    };
    filteredPlaces.value = [];
    filteredSpecies.value = [];
    filteredHabitats.value = [];
    filteredMelders.value = [];
    filteredFieldFruits.value = [];
  }
});

watch(() => props.sighting, (newSighting) => {
  localSighting.value = { ...newSighting };
}, { deep: true });

const createFilter = (field: keyof typeof suggestions.value) => {
  return (input: string) => {
    const targetRef = computed(() => {
      switch(field) {
        case 'places': return filteredPlaces;
        case 'species': return filteredSpecies;
        case 'habitats': return filteredHabitats;
        case 'melders': return filteredMelders;
        case 'field_fruits': return filteredFieldFruits;
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
const filterHabitats = createFilter('habitats');
const filterMelders = createFilter('melders');
const filterFieldFruits = createFilter('field_fruits');

const handleSuggestionSelect = (suggestion: BirdMeta) => {
  localSighting.value.ring = suggestion.ring;
  localSighting.value.species = suggestion.species;
};

const handlePartnerSelect = (suggestion: BirdMeta) => {
  localSighting.value.partner = suggestion.ring;
};

const saveSighting = () => {
  emit('submit', localSighting.value);
};

const hasCoordinates = computed(() => {
  return typeof latitude.value === 'number' && 
         typeof longitude.value === 'number' &&
         !isNaN(latitude.value) && 
         !isNaN(longitude.value);
});

const handleMarkerPlaced = () => {
  if (!localSighting.value.is_exact_location) {
    localSighting.value.is_exact_location = true;
  }
};

const latitude = computed({
  get: () => localSighting.value.lat ?? null,
  set: (val) => {
    localSighting.value.lat = val;
    if (val === null) {
      localSighting.value.is_exact_location = false;
    }
  }
});

const longitude = computed({
  get: () => localSighting.value.lon ?? null,
  set: (val) => {
    localSighting.value.lon = val;
    if (val === null) {
      localSighting.value.is_exact_location = false;
    }
  }
});
</script>

<style scoped>
.v-expansion-panels {
  box-shadow: none !important;
  background: transparent !important;
  padding: 0 !important;
}

.v-expansion-panel {
  background: transparent !important;
  margin: 0 !important;
  border: none !important;
}

.minimal-panel-title {
  padding: 0 !important;
  min-height: 24px !important;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.v-expansion-panel-text__wrapper {
  padding: 0 !important;
}

/* Hide the v-input__details div for all input fields */
.v-input__details {
  display: none !important;
}

/* Updated styles to remove all spacing from input details */
:deep(.v-input__details),
:deep(.v-messages),
:deep(.v-field__outline) {
  display: none !important;
  margin: 0 !important;
  padding: 0 !important;
  min-height: 0 !important;
  height: 0 !important;
}

/* Adjust input field spacing */
:deep(.v-field) {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

:deep(.v-input) {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}

.header-row {
  margin: 0;
}

.extra-fields-btn {
  font-size: 0.875rem;
  text-transform: none;
  letter-spacing: normal;
}

/* Remove default button styles */
:deep(.extra-fields-btn.v-btn--variant-text) {
  opacity: 0.7;
}

:deep(.extra-fields-btn.v-btn--variant-text:hover) {
  opacity: 1;
  background: transparent;
}
</style>