<template>
  <v-app>
    <v-app-bar>
      <v-app-bar-title>Vogelring</v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn to="/new-entry">Neuer Eintrag</v-btn>
      <v-btn to="/entries">Eintragliste</v-btn>
      <v-btn to="/statistics">Statistiken</v-btn>
    </v-app-bar>

    <v-main>
      <v-container>
        <router-view></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
</script>