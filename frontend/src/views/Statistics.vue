<template>
  <div>
    <h1 class="text-h4 mb-4">Statistiken</h1>

    <!-- Analytics Platform Banner -->
    <v-alert
      type="info"
      variant="tonal"
      class="mb-4 analytics-banner"
    >
      <template v-slot:prepend>
        <v-icon icon="mdi-chart-line"></v-icon>
      </template>
      <v-alert-title class="text-h6 mb-2">
        🚀 Neue Analytics-Plattform verfügbar!
      </v-alert-title>
      <div class="mb-3">
        Entdecke erweiterte Analysen und interaktive Dashboards auf unserer neuen Analytics-Plattform.
      </div>
      <v-btn
        :href="'https://analytics.vogelring.com'"
        target="_blank"
        color="primary"
        variant="flat"
        prepend-icon="mdi-open-in-new"
        class="analytics-btn"
      >
        Analytics-Plattform öffnen
      </v-btn>
    </v-alert>

    <v-card>
      <v-card-text>
        <v-btn-group>
          <v-btn
            :to="{ name: 'statistics-dashboard' }"
            :color="isActive('statistics-dashboard') ? 'primary' : undefined"
          >
            Dashboard
          </v-btn>
          <v-btn
            :to="{ name: 'statistics-friends' }"
            :color="isActive('statistics-friends') ? 'primary' : undefined"
          >
            Freunde
          </v-btn>
          <v-btn
            :to="{ name: 'statistics-radius' }"
            :color="isActive('statistics-radius') ? 'primary' : undefined"
          >
            Umkreis
          </v-btn>
          <v-btn
            :to="{ name: 'statistics-seasonal' }"
            :color="isActive('statistics-seasonal') ? 'primary' : undefined"
          >
            Saisonale Analyse
          </v-btn>
          <v-btn
            :to="{ name: 'statistics-data-quality' }"
            :color="isActive('statistics-data-quality') ? 'primary' : undefined"
          >
            Datenqualität
          </v-btn>
        </v-btn-group>
      </v-card-text>
    </v-card>

    <router-view></router-view>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();

const isActive = (name: string) => route.name === name;
</script>

<style scoped>
.analytics-btn {
  text-transform: none !important;
}
</style>