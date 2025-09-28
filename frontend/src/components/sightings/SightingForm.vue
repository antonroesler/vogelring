<template>
  <v-form @submit.prevent="handleSubmit">
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
          v-model="smallGroupSizeInput"
          label="Kleingruppe"
          type="number"
          density="comfortable"
          @input="handleNumericInput('small_group_size', $event)"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="largeGroupSizeInput"
          label="Großgruppe"
          type="number"
          density="comfortable"
          @input="handleNumericInput('large_group_size', $event)"
        ></v-text-field>
      </v-col>

      <!-- Add new row for breed_size and family_size -->
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="breedSizeInput"
          label="Nicht flügge Junge"
          type="number"
          density="comfortable"
          @input="handleNumericInput('breed_size', $event)"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="familySizeInput"
          label="Flügge Junge"
          type="number"
          density="comfortable"
          @input="handleNumericInput('family_size', $event)"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-select
          v-model="localSighting.pair"
          :items="pairItems"
          label="Familien Status"
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

    <!-- Children Form -->
    <children-form
      v-if="isNewEntry"
      v-model:children="children"
    />

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
        class="px-8 submit-btn"
        :prepend-icon="isNewEntry ? 'mdi-content-save' : undefined"
      >
        Speichern
      </v-btn>
    </v-card-actions>
  </v-form>

  <!-- Missing Ring Dialog -->
  <missing-ring-dialog
    v-model="showMissingRingDialog"
    :reading="localSighting.reading"
    @copy-from-reading="handleCopyFromReading"
    @continue-without-ring="handleContinueWithoutRing"
    @cancel="handleCancelRingDialog"
  />

  <!-- Missing Species Dialog -->
  <missing-species-dialog
    v-model="showMissingSpeciesDialog"
    :ring="localSighting.ring"
    @use-suggested-species="handleUseSuggestedSpecies"
    @continue-without-species="handleContinueWithoutSpecies"
    @cancel="handleCancelSpeciesDialog"
  />

  <!-- Family Confirmation Dialog -->
  <family-confirmation-dialog
    v-model="showFamilyConfirmationDialog"
    :main-sighting="pendingSighting || {}"
    :partner-sighting="getPartnerSighting()"
    :child-sightings="getChildSightings()"
    @confirm="handleFamilyConfirm"
    @cancel="handleFamilyCancel"
  />
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import type { Sighting, SuggestionBird, SuggestionLists } from '@/types';
import { BirdStatus, BirdAge, PairType } from '@/types';
import LeafletMap from '@/components/map/LeafletMap.vue';
import BirdSuggestions from '@/components/birds/BirdSuggestions.vue';
import MissingRingDialog from '@/components/dialogs/MissingRingDialog.vue';
import MissingSpeciesDialog from '@/components/dialogs/MissingSpeciesDialog.vue';
import ChildrenForm from '@/components/sightings/ChildrenForm.vue';
import FamilyConfirmationDialog from '@/components/dialogs/FamilyConfirmationDialog.vue';
import { api, createSighting } from '@/api';
import { cleanSightingData, toNumberOrNull } from '@/utils/formValidation';
import { createClearedSighting, createDefaultSighting } from '@/utils/fieldClearingUtils';
import * as apiRelationships from '@/api';

const props = defineProps<{
  sighting: Partial<Sighting>;
  loading?: boolean;
  isNewEntry?: boolean;
  showBirdSuggestions?: boolean;
  showPlaceSuggestions?: boolean;
  showCoordinates?: boolean;
  clearFieldsSettings?: Record<string, boolean>;
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

// Separate input refs for numeric fields to handle display vs actual values
const smallGroupSizeInput = ref<string>('');
const largeGroupSizeInput = ref<string>('');
const breedSizeInput = ref<string>('');
const familySizeInput = ref<string>('');

// Dialog state
const showMissingRingDialog = ref(false);
const showMissingSpeciesDialog = ref(false);
const showFamilyConfirmationDialog = ref(false);
const pendingSighting = ref<Partial<Sighting> | null>(null);
const children = ref<Array<{ ring: string; age?: number }>>([]);

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

// Initialize input fields with current values
const initializeNumericInputs = () => {
  smallGroupSizeInput.value = localSighting.value.small_group_size?.toString() || '';
  largeGroupSizeInput.value = localSighting.value.large_group_size?.toString() || '';
  breedSizeInput.value = localSighting.value.breed_size?.toString() || '';
  familySizeInput.value = localSighting.value.family_size?.toString() || '';
};

// Handle numeric input changes using the utility function
const handleNumericInput = (field: string, event: Event) => {
  const inputElement = event.target as HTMLInputElement;
  const value = toNumberOrNull(inputElement.value);
  (localSighting.value as any)[field] = value;
};

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

  // Initialize numeric inputs
  initializeNumericInputs();
});

watch(() => props.sighting, (newSighting) => {
  localSighting.value = { ...newSighting };
  initializeNumericInputs();
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

const handleSuggestionSelect = (suggestion: SuggestionBird) => {
  localSighting.value.ring = suggestion.ring;
  localSighting.value.species = suggestion.species;
};

const handlePartnerSelect = (suggestion: SuggestionBird) => {
  localSighting.value.partner = suggestion.ring;
};

const handleSubmit = () => {
  // Clean the data first
  const cleanedSighting = cleanSightingData(localSighting.value);
  
  // Check if we need to show dialogs for missing data
  const missingRing = !cleanedSighting.ring;
  const missingSpecies = !cleanedSighting.species;
  
  if (props.isNewEntry && (missingRing || missingSpecies)) {
    // Store the pending sighting
    pendingSighting.value = cleanedSighting;
    
    // Show ring dialog first if ring is missing
    if (missingRing) {
      showMissingRingDialog.value = true;
      return;
    }
    
    // If ring is present but species is missing, show species dialog
    if (missingSpecies) {
      showMissingSpeciesDialog.value = true;
      return;
    }
  }
  
  // Check if we need family confirmation for new entries
  if (props.isNewEntry) {
    const hasPartner = cleanedSighting.partner && 
      cleanedSighting.partner.toLowerCase() !== 'ub' && 
      cleanedSighting.partner.toLowerCase() !== 'unberingt';
    const hasChildren = children.value.some(child => child.ring);
    
    if (hasPartner || hasChildren) {
      pendingSighting.value = cleanedSighting;
      showFamilyConfirmationDialog.value = true;
      return;
    }
  }
  
  // If no dialogs needed or not a new entry, submit directly
  emit('submit', cleanedSighting);
};

// Ring dialog handlers
const handleCopyFromReading = () => {
  if (pendingSighting.value && localSighting.value.reading) {
    localSighting.value.ring = localSighting.value.reading;
    pendingSighting.value.ring = localSighting.value.reading;
    
    // Check if we still need to show species dialog
    if (!pendingSighting.value.species) {
      showMissingSpeciesDialog.value = true;
    } else {
      emit('submit', pendingSighting.value);
      pendingSighting.value = null;
    }
  }
};

const handleContinueWithoutRing = () => {
  if (pendingSighting.value) {
    // Check if we still need to show species dialog
    if (!pendingSighting.value.species) {
      showMissingSpeciesDialog.value = true;
    } else {
      emit('submit', pendingSighting.value);
      pendingSighting.value = null;
    }
  }
};

const handleCancelRingDialog = () => {
  pendingSighting.value = null;
};

// Species dialog handlers
const handleUseSuggestedSpecies = (species: string) => {
  if (pendingSighting.value) {
    localSighting.value.species = species;
    pendingSighting.value.species = species;
    emit('submit', pendingSighting.value);
    pendingSighting.value = null;
  }
};

const handleContinueWithoutSpecies = () => {
  if (pendingSighting.value) {
    emit('submit', pendingSighting.value);
    pendingSighting.value = null;
  }
};

const handleCancelSpeciesDialog = () => {
  pendingSighting.value = null;
};

const getPartnerSighting = () => {
  if (!pendingSighting.value?.partner || 
      pendingSighting.value.partner.toLowerCase() === 'ub' || 
      pendingSighting.value.partner.toLowerCase() === 'unberingt') {
    return undefined;
  }
  
  // Determine partner sex based on main sighting sex
  let partnerSex: string | undefined;
  if (pendingSighting.value.sex === 'M') {
    partnerSex = 'W';
  } else if (pendingSighting.value.sex === 'W') {
    partnerSex = 'M';
  }
  
  return {
    ...pendingSighting.value,
    ring: pendingSighting.value.partner,
    partner: pendingSighting.value.ring,
    reading: undefined,
    comment: 'Diese Sichtung wurde automatisch generiert',
    sex: partnerSex
  };
};

const getChildSightings = () => {
  return children.value
    .filter(child => child.ring)
    .map(child => ({
      ...pendingSighting.value,
      ring: child.ring,
      partner: undefined,
      reading: undefined,
      comment: 'Diese Sichtung wurde automatisch generiert',
      age: child.age ? `${child.age}` as any : undefined,
      sex: child.sex,
      status: undefined,
      breed_size: undefined,
      family_size: undefined,
      pair: pendingSighting.value?.pair === 'x' ? undefined : pendingSighting.value?.pair
    }));
};

const handleFamilyConfirm = async () => {
  if (!pendingSighting.value) return;
  
  try {
    const year = new Date(pendingSighting.value.date || new Date()).getFullYear();
    
    // Create main sighting
    const mainSighting = await createSighting(pendingSighting.value);
    
    // Create partner sighting and relationship
    const partnerSighting = getPartnerSighting();
    let createdPartnerSighting = null;
    if (partnerSighting) {
      createdPartnerSighting = await createSighting(partnerSighting);
      
      // Create breeding partner relationships
      await apiRelationships.createRelationship({
        bird1_ring: mainSighting.ring!,
        bird2_ring: createdPartnerSighting.ring!,
        relationship_type: 'breeding_partner',
        year,
        sighting1_id: mainSighting.id,
        sighting2_id: createdPartnerSighting.id
      });
      
      await apiRelationships.createRelationship({
        bird1_ring: createdPartnerSighting.ring!,
        bird2_ring: mainSighting.ring!,
        relationship_type: 'breeding_partner',
        year,
        sighting1_id: createdPartnerSighting.id,
        sighting2_id: mainSighting.id
      });
    }
    
    // Create children sightings and relationships
    const childSightings = getChildSightings();
    for (const childSighting of childSightings) {
      const createdChildSighting = await createSighting(childSighting);
      
      // Create parent-child relationships with main bird
      await apiRelationships.createRelationship({
        bird1_ring: mainSighting.ring!,
        bird2_ring: createdChildSighting.ring!,
        relationship_type: 'parent_of',
        year,
        sighting1_id: mainSighting.id,
        sighting2_id: createdChildSighting.id
      });
      
      await apiRelationships.createRelationship({
        bird1_ring: createdChildSighting.ring!,
        bird2_ring: mainSighting.ring!,
        relationship_type: 'child_of',
        year,
        sighting1_id: createdChildSighting.id,
        sighting2_id: mainSighting.id
      });

      // Create parent-child relationships with partner if exists
      if (createdPartnerSighting) {
        await apiRelationships.createRelationship({
          bird1_ring: createdPartnerSighting.ring!,
          bird2_ring: createdChildSighting.ring!,
          relationship_type: 'parent_of',
          year,
          sighting1_id: createdPartnerSighting.id,
          sighting2_id: createdChildSighting.id
        });
        
        await apiRelationships.createRelationship({
          bird1_ring: createdChildSighting.ring!,
          bird2_ring: createdPartnerSighting.ring!,
          relationship_type: 'child_of',
          year,
          sighting1_id: createdChildSighting.id,
          sighting2_id: createdPartnerSighting.id
        });
      }
    }
    
    // Create sibling relationships between children
    for (let i = 0; i < childSightings.length; i++) {
      for (let j = i + 1; j < childSightings.length; j++) {
        // Create sibling relationships
        await apiRelationships.createRelationship({
          bird1_ring: childSightings[i].ring!,
          bird2_ring: childSightings[j].ring!,
          relationship_type: 'sibling_of',
          year
        });
        
        await apiRelationships.createRelationship({
          bird1_ring: childSightings[j].ring!,
          bird2_ring: childSightings[i].ring!,
          relationship_type: 'sibling_of',
          year
        });
      }
    }
    
    showFamilyConfirmationDialog.value = false;
    
    // Reset form using the same field clearing logic as individual sightings
    if (props.clearFieldsSettings) {
      localSighting.value = createClearedSighting(pendingSighting.value, props.clearFieldsSettings);
    } else {
      // Fallback to default sighting if no clear fields settings available
      localSighting.value = createDefaultSighting();
    }
    
    children.value = [];
    pendingSighting.value = null;
    
  } catch (error) {
    console.error('Error creating family sighting:', error);
  }
};

const handleFamilyCancel = () => {
  showFamilyConfirmationDialog.value = false;
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
  get: () => localSighting.value.lat ?? undefined,
  set: (val) => {
    localSighting.value.lat = val === null ? undefined : val;
    if (val === null || val === undefined) {
      localSighting.value.is_exact_location = false;
    }
  }
});

const longitude = computed({
  get: () => localSighting.value.lon ?? undefined,
  set: (val) => {
    localSighting.value.lon = val === null ? undefined : val;
    if (val === null || val === undefined) {
      localSighting.value.is_exact_location = false;
    }
  }
});
</script>

<style scoped>
/* Enhanced submit button */
.submit-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  letter-spacing: 0.025em !important;
  background: linear-gradient(135deg, #00436C 0%, #228096 100%) !important;
  box-shadow: 0 4px 16px rgba(0, 67, 108, 0.3) !important;
  transition: all 0.3s ease !important;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 67, 108, 0.4) !important;
}

.submit-btn:active {
  transform: translateY(0);
}

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
  transition: all 0.3s ease;
}

:deep(.v-field:hover) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 67, 108, 0.1) !important;
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
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}

/* Remove default button styles */
:deep(.extra-fields-btn.v-btn--variant-text) {
  opacity: 0.7;
}

:deep(.extra-fields-btn.v-btn--variant-text:hover) {
  opacity: 1;
  background: transparent;
  transform: translateY(-1px);
}
</style>