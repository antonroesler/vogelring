<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      Vogel Details
      <v-spacer></v-spacer>
      <v-btn
        icon
        variant="text"
        :to="`/statistics/friends?ring=${bird?.ring}`"
        v-tooltip="'Freunde analysieren'"
        class="me-2"
      >
        <v-icon>mdi-account-group</v-icon>
      </v-btn>
      <v-btn
        v-if="bird?.ring"
        icon
        variant="text"
        :to="`/birds/${bird.ring}`"
        v-tooltip="'Detailansicht öffnen'"
      >
        <v-icon>mdi-open-in-new</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-progress-circular
        v-if="!bird"
        indeterminate
        color="primary"
        class="ma-4"
      ></v-progress-circular>

      <template v-else>
        <v-list>
          <v-list-item>
            <v-list-item-title>Spezies</v-list-item-title>
            <v-list-item-subtitle>{{ bird.species || 'Unbekannt' }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Ring</v-list-item-title>
            <v-list-item-subtitle>{{ bird.ring || 'Unbekannt' }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Anzahl Sichtungen</v-list-item-title>
            <v-list-item-subtitle>{{ bird.sighting_count ?? 0 }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item v-if="bird.first_seen">
            <v-list-item-title>Erste Sichtung</v-list-item-title>
            <v-list-item-subtitle>{{ formatDate(bird.first_seen) }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item v-if="bird.last_seen">
            <v-list-item-title>Letzte Sichtung</v-list-item-title>
            <v-list-item-subtitle>{{ formatDate(bird.last_seen) }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>

        <v-divider class="my-4"></v-divider>

        <div class="d-flex align-center mb-2">
          <h3 class="text-h6">Beringungsdaten</h3>
          <v-spacer></v-spacer>
          <v-progress-circular
            v-if="isLoadingRinging"
            indeterminate
            color="primary"
            size="20"
            width="2"
            class="me-2"
          ></v-progress-circular>
          <v-btn
            v-if="ringingData && !isLoadingRinging"
            variant="text"
            color="primary"
            size="small"
            @click="showAllRingingData = !showAllRingingData"
          >
            {{ showAllRingingData ? 'Weniger Daten' : 'Mehr Daten' }}
            <v-icon :icon="showAllRingingData ? 'mdi-chevron-up' : 'mdi-chevron-down'" class="ms-1"></v-icon>
          </v-btn>
        </div>
        
        <template v-if="ringingData">
          <!-- Essential ringing data (always visible) -->
          <v-list>
            <v-list-item>
              <v-list-item-title>Beringungsdatum</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(ringingData.date) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Beringungsort</v-list-item-title>
              <v-list-item-subtitle>{{ ringingData.place }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>

          <!-- Additional ringing data (collapsible) -->
          <v-expand-transition>
            <v-list v-if="showAllRingingData">
              <v-list-item>
                <v-list-item-title>Alter bei Beringung</v-list-item-title>
                <v-list-item-subtitle>{{ formatAge(ringingData.age) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Geschlecht</v-list-item-title>
                <v-list-item-subtitle>{{ formatSex(ringingData.sex) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Status</v-list-item-title>
                <v-list-item-subtitle>
                  <v-chip
                    v-if="ringingData.status"
                    :color="getBirdStatusColor(ringingData.status)"
                    size="small"
                    variant="tonal"
                  >
                    <v-icon 
                      v-if="getBirdStatusIcon(ringingData.status)"
                      :icon="getBirdStatusIcon(ringingData.status)"
                      size="x-small"
                      class="mr-1"
                    ></v-icon>
                    {{ formatBirdStatus(ringingData.status) }}
                  </v-chip>
                  <span v-else>Unbekannt</span>
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Beringer</v-list-item-title>
                <v-list-item-subtitle>{{ ringingData.ringer }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Ring Schema</v-list-item-title>
                <v-list-item-subtitle>{{ ringingData.ring_scheme }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>Koordinaten</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatCoordinates(ringingData.lat, ringingData.lon) }}
                  <v-btn
                    icon="mdi-map-marker"
                    size="small"
                    variant="text"
                    density="compact"
                    :href="getGoogleMapsLink(ringingData.lat, ringingData.lon)"
                    target="_blank"
                    class="ms-2"
                    v-tooltip="'In Google Maps öffnen'"
                  >
                  </v-btn>
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="ringingData.comment">
                <v-list-item-title>Kommentar</v-list-item-title>
                <v-list-item-subtitle>{{ ringingData.comment }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-expand-transition>
        </template>
        <p v-else-if="!isLoadingRinging" class="text-body-1 text-medium-emphasis">
          Keine Beringungsdaten verfügbar.
        </p>

        <v-divider class="my-4"></v-divider>

        <h3 class="text-h6 mb-2">Andere Artenbestimmungen</h3>
        <v-list v-if="bird.other_species_identifications && Object.keys(bird.other_species_identifications).length > 0">
          <v-list-item v-for="(count, species) in bird.other_species_identifications" :key="species">
            <v-list-item-title>{{ species }}</v-list-item-title>
            <v-list-item-subtitle>{{ count }} mal</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <p v-else class="text-body-1">
          {{ bird.species ? `Ausschließlich als ${bird.species} identifiziert.` : 'Keine Artenbestimmungen verfügbar.' }}
        </p>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { format } from 'date-fns';
import { formatBirdStatus, getBirdStatusColor, getBirdStatusIcon } from '@/utils/statusUtils';
import type { BirdMeta, Ringing } from '@/types';
import { formatRingingAge } from '@/utils/ageMapping';

defineProps<{
  bird: BirdMeta | null;
  ringingData: Ringing | null;
}>();

const isLoadingRinging = ref(false);
const showAllRingingData = ref(false);

const formatDate = (date: string | null) => {
  if (!date) return 'Unbekannt';
  return format(new Date(date), 'dd.MM.yyyy');
};

const formatAge = (age: number) => {
  return formatRingingAge(age, true);
};

const formatSex = (sex: number) => {
  switch (sex) {
    case 1: return 'Männlich (1)';
    case 2: return 'Weiblich (2)';
    case 0: return 'Unbekannt (0)';
    default: return `Code ${sex}`;
  }
};


const formatCoordinates = (lat: number, lon: number) => {
  return `${lat.toFixed(6)}°, ${lon.toFixed(6)}°`;
};

const getGoogleMapsLink = (lat: number, lon: number) => {
  return `https://www.google.com/maps?q=${lat},${lon}`;
};
</script>

<style scoped>
.v-list-item-subtitle {
  display: flex;
  align-items: center;
}
</style>