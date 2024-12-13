<template>
  <v-dialog v-model="dialog" max-width="500">
    <template v-slot:activator="{ props }">
      <v-btn
        color="primary"
        prepend-icon="mdi-share-variant"
        v-bind="props"
        :loading="loading"
      >
        Teilen
      </v-btn>
    </template>

    <v-card>
      <v-card-title>Bericht teilen</v-card-title>
      <v-card-text>
        <v-form @submit.prevent="generateAndShare">
          <v-text-field
            v-model="days"
            label="Gültigkeitstage"
            type="number"
            min="1"
            max="365"
            :rules="[v => !!v || 'Erforderlich', v => (v >= 1 && v <= 365) || 'Zwischen 1 und 365 Tagen']"
          ></v-text-field>

          <div v-if="shareableUrl" class="mt-4">
            <v-text-field
              v-model="shareableUrl"
              label="Teilbare URL"
              readonly
              append-inner-icon="mdi-content-copy"
              @click:append-inner="copyToClipboard"
            ></v-text-field>
            <v-alert
              v-if="showCopiedAlert"
              type="success"
              variant="tonal"
              class="mt-2"
            >
              URL in die Zwischenablage kopiert
            </v-alert>
          </div>
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          color="grey-darken-1"
          variant="text"
          @click="dialog = false"
        >
          Schließen
        </v-btn>
        <v-btn
          color="primary"
          :loading="loading"
          :disabled="!isValid"
          @click="generateAndShare"
        >
          Bericht generieren
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import * as api from '@/api';

const props = defineProps<{
  generateHtml: () => string;
}>();

const dialog = ref(false);
const days = ref(30);
const loading = ref(false);
const shareableUrl = ref('');
const showCopiedAlert = ref(false);

const isValid = computed(() => {
  return days.value >= 1 && days.value <= 365;
});

const generateAndShare = async () => {
  if (!isValid.value) return;
  
  loading.value = true;
  try {
    // Get pre-signed URLs
    const { pre_signed_s3_upload_url, pre_signed_cloudfront_share_url } = 
      await api.getShareableReportUrls(days.value);

    // Generate HTML content
    const htmlContent = props.generateHtml();

    // Upload to S3 using pre-signed URL
    await fetch(pre_signed_s3_upload_url, {
      method: 'PUT',
      body: htmlContent,
      headers: {
        'Content-Type': 'text/html'
      }
    });

    // Set the shareable URL
    shareableUrl.value = pre_signed_cloudfront_share_url;
  } catch (error) {
    console.error('Error generating shareable report:', error);
  } finally {
    loading.value = false;
  }
};

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(shareableUrl.value);
    showCopiedAlert.value = true;
    setTimeout(() => {
      showCopiedAlert.value = false;
    }, 3000);
  } catch (error) {
    console.error('Error copying to clipboard:', error);
  }
};
</script> 