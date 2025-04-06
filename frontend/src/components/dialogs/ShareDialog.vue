<template>
  <div>
    <v-dialog v-model="dialog" max-width="500px">
      <template v-slot:activator="{ props }">
        <v-btn 
          v-bind="props"
          prepend-icon="mdi-share-variant"
          color="primary"
        >
          Teilen
        </v-btn>
      </template>
      <v-card>
        <v-card-title>Teilen</v-card-title>
        <v-card-text>
          <v-select
            v-model="selectedDays"
            :items="dayOptions"
            label="Link gültig für"
          ></v-select>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="generateReport">
            Link generieren
          </v-btn>
          <v-btn color="error" @click="dialog = false">
            Abbrechen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <v-snackbar v-model="showSnackbar" color="success">
      Link wurde in die Zwischenablage kopiert
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { ShareableReport } from '@/types';

const props = defineProps<{
  generateHtml: () => string;
  getUrls: (days: number, html: string) => Promise<ShareableReport>;
}>();

const dialog = ref(false);
const showSnackbar = ref(false);
const selectedDays = ref(90);
const dayOptions = [
  { title: '30 Tage', value: 30 },
  { title: '90 Tage', value: 90 },
  { title: '180 Tage', value: 180 },
  { title: '360 Tage', value: 360 },
];

const generateReport = async () => {
  try {
    const html = props.generateHtml();
    console.log('Generated HTML length:', html.length);
    const result = await props.getUrls(selectedDays.value, html);
    await navigator.clipboard.writeText(result.view_url);
    showSnackbar.value = true;
    dialog.value = false;
  } catch (error) {
    console.error('Error generating report:', error);
  }
};
</script> 