<template>
  <div>
    <h1 class="text-h4 mb-4">Statistiken</h1>

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