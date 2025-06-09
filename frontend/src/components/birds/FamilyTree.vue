<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      Familie
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-plus"
        variant="text"
        @click="showAddDialog = true"
        v-tooltip="'Familienmitglied hinzufügen'"
        size="small"
      ></v-btn>
    </v-card-title>
    <v-card-text>
      <v-progress-circular
        v-if="isLoading"
        indeterminate
        color="primary"
        class="ma-4"
      ></v-progress-circular>

      <template v-else>
        <!-- Parents Section -->
        <div v-if="familyData?.parents?.length" class="mb-4">
          <h4 class="text-subtitle-1 mb-2">Eltern</h4>
          <v-list density="compact">
            <v-list-item
              v-for="parent in familyData.parents"
              :key="parent.ring"
              :to="`/birds/${parent.ring}`"
              target="_blank"
              class="clickable-item"
            >
              <template v-slot:prepend>
                <v-icon 
                  :icon="parent.sex === 'M' ? 'mdi-gender-male' : parent.sex === 'W' ? 'mdi-gender-female' : 'mdi-help'"
                  :color="parent.sex === 'M' ? 'blue' : parent.sex === 'W' ? 'pink' : 'grey'"
                  size="small"
                ></v-icon>
              </template>
              <v-list-item-title>{{ parent.ring }}</v-list-item-title>
              <v-list-item-subtitle>
                {{ parent.sex === 'M' ? 'Vater' : parent.sex === 'W' ? 'Mutter' : 'Elternteil' }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </div>

        <!-- Partners and Children Section -->
        <div v-if="sortedRelationships.length">
          <h4 class="text-subtitle-1 mb-2">Partner & Nachkommen</h4>
          
          <!-- Show only recent years by default -->
          <div v-for="yearGroup in displayedYearGroups" :key="yearGroup.year" class="mb-3">
            <v-chip size="small" color="primary" class="mb-2">{{ yearGroup.year }}</v-chip>
            
            <v-list density="compact">
              <!-- Partners for this year -->
              <v-list-item
                v-for="partner in yearGroup.partners"
                :key="`partner-${partner.ring}-${partner.year}`"
                :to="`/birds/${partner.ring}`"
                target="_blank"
                class="clickable-item"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-heart" color="red" size="small"></v-icon>
                </template>
                <v-list-item-title>{{ partner.ring }}</v-list-item-title>
                <v-list-item-subtitle>Partner</v-list-item-subtitle>
              </v-list-item>

              <!-- Children for this year -->
              <v-list-item
                v-for="child in yearGroup.children"
                :key="`child-${child.ring}-${child.year}`"
                :to="`/birds/${child.ring}`"
                target="_blank"
                class="clickable-item"
              >
                <template v-slot:prepend>
                  <v-icon icon="mdi-baby-face" color="green" size="small"></v-icon>
                </template>
                <v-list-item-title>{{ child.ring }}</v-list-item-title>
                <v-list-item-subtitle>Nachkomme</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>

          <!-- Show more button -->
          <v-btn
            v-if="!showAllYears && sortedRelationships.length > 3"
            variant="text"
            color="primary"
            @click="showAllYears = true"
            size="small"
            class="mt-2"
          >
            Alle Jahre anzeigen ({{ sortedRelationships.length - 3 }} weitere)
          </v-btn>
        </div>

        <!-- No family data message -->
        <p v-if="!familyData?.parents?.length && !sortedRelationships.length" class="text-body-1 text-medium-emphasis">
          Keine Familieninformationen verfügbar.
        </p>
      </template>
    </v-card-text>

    <!-- Add Family Member Dialog -->
    <v-dialog v-model="showAddDialog" max-width="500">
      <v-card>
        <v-card-title>Familienmitglied hinzufügen</v-card-title>
        <v-card-text>
          <v-form ref="addForm" v-model="isFormValid">
            <v-select
              v-model="addType"
              :items="[
                { title: 'Partner', value: 'partner' },
                { title: 'Nachkomme', value: 'child' }
              ]"
              label="Typ"
              :rules="[v => !!v || 'Typ ist erforderlich']"
              class="mb-3"
            ></v-select>

            <v-text-field
              v-model="addRing"
              label="Ring"
              :rules="[v => !!v || 'Ring ist erforderlich']"
              class="mb-3"
            ></v-text-field>

            <v-text-field
              v-model="addYear"
              label="Jahr"
              type="number"
              :min="1900"
              :max="new Date().getFullYear()"
              :rules="[v => !!v || 'Jahr ist erforderlich']"
              class="mb-3"
            ></v-text-field>

            <v-select
              v-if="addType === 'child'"
              v-model="addSex"
              :items="[
                { title: 'Männlich', value: 'M' },
                { title: 'Weiblich', value: 'W' },
                { title: 'Unbekannt', value: 'U' }
              ]"
              label="Geschlecht"
              :rules="[v => !!v || 'Geschlecht ist erforderlich']"
            ></v-select>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeAddDialog">Abbrechen</v-btn>
          <v-btn 
            color="primary" 
            @click="addFamilyMember"
            :loading="isAdding"
            :disabled="!isFormValid"
          >
            Hinzufügen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
    <v-snackbar
      v-model="showSuccessSnackbar"
      color="success"
      :timeout="3000"
    >
      {{ successMessage }}
    </v-snackbar>

    <!-- Error Snackbar -->
    <v-snackbar
      v-model="showErrorSnackbar"
      color="error"
      :timeout="5000"
    >
      {{ errorMessage }}
    </v-snackbar>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import type { FamilyTreeEntry, FamilyPartner, FamilyChild } from '@/types';
import * as api from '@/api';

const props = defineProps<{
  ring: string;
}>();

const emit = defineEmits<{
  'family-updated': [];
}>();

const familyData = ref<FamilyTreeEntry | null>(null);
const isLoading = ref(false);
const showAllYears = ref(false);
const showAddDialog = ref(false);
const isAdding = ref(false);
const isFormValid = ref(false);
const addForm = ref();

// Add form fields
const addType = ref<'partner' | 'child'>('partner');
const addRing = ref('');
const addYear = ref(new Date().getFullYear());
const addSex = ref<'M' | 'W' | 'U'>('U');

// Snackbar state
const showSuccessSnackbar = ref(false);
const showErrorSnackbar = ref(false);
const successMessage = ref('');
const errorMessage = ref('');

// Combine partners and children with years for sorting
const sortedRelationships = computed(() => {
  if (!familyData.value) return [];
  
  const relationships: Array<{ year: number; type: 'partner' | 'child'; data: FamilyPartner | FamilyChild }> = [];
  
  // Add partners
  familyData.value.partners.forEach(partner => {
    relationships.push({
      year: partner.year,
      type: 'partner',
      data: partner
    });
  });
  
  // Add children
  familyData.value.children.forEach(child => {
    relationships.push({
      year: child.year || new Date().getFullYear(),
      type: 'child',
      data: child
    });
  });
  
  // Group by year and sort by year (newest first)
  const yearGroups = relationships.reduce((acc, rel) => {
    if (!acc[rel.year]) {
      acc[rel.year] = { year: rel.year, partners: [], children: [] };
    }
    if (rel.type === 'partner') {
      acc[rel.year].partners.push(rel.data as FamilyPartner);
    } else {
      acc[rel.year].children.push(rel.data as FamilyChild);
    }
    return acc;
  }, {} as Record<number, { year: number; partners: FamilyPartner[]; children: FamilyChild[] }>);
  
  return Object.values(yearGroups).sort((a, b) => b.year - a.year);
});

// Show only the latest 3 years by default
const displayedYearGroups = computed(() => {
  if (showAllYears.value) {
    return sortedRelationships.value;
  }
  return sortedRelationships.value.slice(0, 3);
});

const loadFamilyData = async () => {
  if (!props.ring) return;
  
  isLoading.value = true;
  try {
    familyData.value = await api.getFamilyTreeByRing(props.ring);
  } catch (error) {
    console.error('Error loading family data:', error);
    familyData.value = null;
  } finally {
    isLoading.value = false;
  }
};

const addFamilyMember = async () => {
  if (!addForm.value?.validate() || !isFormValid.value) return;
  
  isAdding.value = true;
  try {
    if (addType.value === 'partner') {
      await api.addPartnerRelationship(props.ring, addRing.value, addYear.value);
      successMessage.value = 'Partner erfolgreich hinzugefügt';
    } else {
      await api.addChildRelationship(props.ring, addRing.value, addYear.value, addSex.value);
      successMessage.value = 'Nachkomme erfolgreich hinzugefügt';
    }
    
    showSuccessSnackbar.value = true;
    closeAddDialog();
    await loadFamilyData();
    emit('family-updated');
  } catch (error) {
    console.error('Error adding family member:', error);
    errorMessage.value = 'Fehler beim Hinzufügen des Familienmitglieds';
    showErrorSnackbar.value = true;
  } finally {
    isAdding.value = false;
  }
};

const closeAddDialog = () => {
  showAddDialog.value = false;
  addType.value = 'partner';
  addRing.value = '';
  addYear.value = new Date().getFullYear();
  addSex.value = 'U';
  addForm.value?.reset();
};

// Watch for ring changes
watch(() => props.ring, loadFamilyData, { immediate: true });

onMounted(loadFamilyData);
</script>

<style scoped>
.clickable-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.v-list-item-subtitle {
  display: flex;
  align-items: center;
}
</style>