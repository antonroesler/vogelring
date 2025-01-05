<template>
  <v-dialog v-model="dialog" max-width="500">
    <template v-slot:activator="{ props }">
      <v-btn
        v-bind="props"
        variant="text"
        color="secondary"
        density="comfortable"
        class="settings-btn"
        prepend-icon="mdi-cog"
      >
        Einstellungen
      </v-btn>
    </template>

    <v-card>
      <v-card-title>Einstellungen: Felder zurücksetzen</v-card-title>
      <v-card-text>
        <p class="text-body-2 mb-4">
          Felder zum Zurücksetzen auswählen:
        </p>
        <div class="scrollable-content">
          <v-row dense>
            <v-col cols="12" sm="6" v-for="field in fields" :key="field.key">
              <v-checkbox
                v-model="localSettings[field.key]"
                :label="field.label"
                density="comfortable"
                hide-details
                class="mb-2"
              ></v-checkbox>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          variant="elevated"
          size="large"
          @click="saveSettings"
          class="px-8"
        >
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const dialog = ref(false);

const fields = [
  { key: 'date', label: 'Datum' },
  { key: 'place', label: 'Ort' },
  { key: 'habitat', label: 'Habitat' },
  { key: 'area', label: 'Kleinfläche' },
  { key: 'field_fruit', label: 'Feldfrucht' },
  { key: 'reading', label: 'Ablesung' },
  { key: 'ring', label: 'Ring' },
  { key: 'species', label: 'Spezies' },
  { key: 'partner', label: 'Partner' },
  { key: 'small_group_size', label: 'Kleingruppe' },
  { key: 'large_group_size', label: 'Großgruppe' },
  { key: 'breed_size', label: 'Nicht flügge Junge' },
  { key: 'family_size', label: 'Flügge Junge' },
  { key: 'pair', label: 'Paarung' },
  { key: 'status', label: 'Status' },
  { key: 'age', label: 'Alter' },
  { key: 'melder', label: 'Melder' },
  { key: 'melded', label: 'Gemeldet' },
  { key: 'comment', label: 'Kommentar' },
  { key: 'coordinates', label: 'Koordinaten' },
];

const defaultSettings = Object.fromEntries(
  fields.map(field => [field.key, field.key === 'date' || field.key === 'place' ? false : true])
);

const localSettings = ref({ ...defaultSettings });

const emit = defineEmits<{
  'update:settings': [settings: Record<string, boolean>]
}>();

onMounted(() => {
  // Load settings from localStorage
  const savedSettings = localStorage.getItem('clearFieldsSettings');
  if (savedSettings) {
    localSettings.value = JSON.parse(savedSettings);
  }
  emit('update:settings', localSettings.value);
});

const saveSettings = () => {
  localStorage.setItem('clearFieldsSettings', JSON.stringify(localSettings.value));
  emit('update:settings', localSettings.value);
  dialog.value = false;
};
</script>

<style scoped>
.settings-btn {
  font-size: 0.875rem;
  text-transform: none;
  letter-spacing: normal;
}

.scrollable-content {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 8px;
}

/* Custom scrollbar styles */
.scrollable-content::-webkit-scrollbar {
  width: 8px;
}

.scrollable-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.scrollable-content::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.scrollable-content::-webkit-scrollbar-thumb:hover {
  background: #666;
}
</style> 