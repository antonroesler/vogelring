<template>
  <v-dialog v-model="dialog" max-width="500">
    <template v-slot:activator="{ props }">
      <v-btn
        v-bind="props"
        variant="text"
        color="secondary"
        density="comfortable"
        class="settings-btn enhanced-btn"
        prepend-icon="mdi-cog"
      >
        Einstellungen
      </v-btn>
    </template>

    <v-card class="settings-dialog">
      <v-card-title>Einstellungen: Felder zurücksetzen</v-card-title>
      <v-card-text>
        <div class="legend mb-4">
          <div class="d-flex align-center mb-2">
            <v-icon icon="mdi-refresh" color="error" class="mr-2"></v-icon>
            <span>Feld wird zurückgesetzt</span>
          </div>
          <div class="d-flex align-center">
            <v-icon icon="mdi-content-save" color="success" class="mr-2"></v-icon>
            <span>Feld wird beibehalten</span>
          </div>
        </div>
        <v-divider class="mb-4"></v-divider>
        <div class="scrollable-content">
          <v-row dense>
            <v-col 
              cols="12" 
              v-for="field in fields.filter(f => !f.hidden)" 
              :key="field.key"
              class="field-col"
            >
              <div class="d-flex align-center justify-space-between field-row">
                <span>{{ field.label }}</span>
                <v-btn
                  icon
                  size="small"
                  :color="localSettings[field.key] ? 'error' : 'success'"
                  variant="text"
                  @click="toggleField(field.key)"
                  density="comfortable"
                  class="field-btn enhanced-field-btn"
                >
                  <v-icon :icon="localSettings[field.key] ? 'mdi-refresh' : 'mdi-content-save'"></v-icon>
                  <v-tooltip activator="parent" location="left">
                    {{ localSettings[field.key] ? 'Feld wird zurückgesetzt' : 'Feld wird beibehalten' }}
                  </v-tooltip>
                </v-btn>
              </div>
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
          class="px-8 save-settings-btn"
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
  { key: 'species', label: 'Spezies' },
  { key: 'partner', label: 'Partner' },
  { key: 'small_group_size', label: 'Kleingruppe' },
  { key: 'large_group_size', label: 'Großgruppe' },
  { key: 'breed_size', label: 'Nicht flügge Junge' },
  { key: 'family_size', label: 'Flügge Junge' },
  { key: 'pair', label: 'Paarung' },
  { key: 'status', label: 'Status' },
  { key: 'age', label: 'Alter' },
  { key: 'sex', label: 'Geschlecht' },
  { key: 'melder', label: 'Melder' },
  { key: 'melded', label: 'Gemeldet' },
  { key: 'comment', label: 'Kommentar' },
  { key: 'lat', label: 'Koordinaten' },
  { key: 'lon', label: 'Koordinaten (hidden)', hidden: true },
];

const defaultSettings = Object.fromEntries(
  fields.map(field => [field.key, field.key === 'date' || field.key === 'place' ? false : true])
);

const localSettings = ref({ ...defaultSettings });

const emit = defineEmits<{
  'update:settings': [settings: Record<string, boolean>]
}>();

const toggleField = (key: string) => {
  localSettings.value[key] = !localSettings.value[key];
};

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
.settings-dialog {
  border-radius: 16px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important;
}

.enhanced-btn {
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}

.enhanced-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(34, 128, 150, 0.2);
}

.enhanced-field-btn {
  transition: all 0.3s ease !important;
}

.enhanced-field-btn:hover {
  transform: scale(1.1);
}

.save-settings-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  letter-spacing: 0.025em !important;
  background: linear-gradient(135deg, #00436C 0%, #228096 100%) !important;
  box-shadow: 0 4px 16px rgba(0, 67, 108, 0.3) !important;
  transition: all 0.3s ease !important;
}

.save-settings-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 67, 108, 0.4) !important;
}

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

.field-col {
  padding-top: 0;
  padding-bottom: 0;
}

.field-row {
  padding: 2px 0;
  min-height: 32px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.field-btn {
  margin: 0;
  height: 28px;
  width: 28px;
}

.field-row:hover {
  background: linear-gradient(135deg, rgba(0, 67, 108, 0.05) 0%, rgba(34, 128, 150, 0.05) 100%);
  transform: translateX(4px);
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
  background: linear-gradient(135deg, #00436C 0%, #228096 100%);
  border-radius: 4px;
}

.scrollable-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #228096 0%, #00436C 100%);
}

.legend {
  color: rgba(0, 0, 0, 0.6);
  font-size: 0.875rem;
}
</style> 