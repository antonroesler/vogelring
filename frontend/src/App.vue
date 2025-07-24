<template>
  <v-app>
    <v-app-bar flat class="app-header">
      <!-- Left section -->
      <v-app-bar-title class="app-title">
        <div class="d-flex align-center" style="cursor: pointer" @click="navigateToHome">
          <v-icon icon="mdi-bird" size="32" class="logo-icon me-3"></v-icon>
          <div>
            <span class="title-text">Vogelring</span>
            <span class="version-text" v-if="version">v{{ version }}</span>
          </div>
        </div>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- Center section with search -->
      <div class="search-container" v-if="authStore.isAuthenticated">
        <v-autocomplete
          v-model="selectedBird"
          v-model:search="searchQuery"
          :items="sortedSuggestions"
          :loading="isLoading"
          color="primary"
          hide-details
          :append-inner-icon="null"
          :no-data-append-icon="null"
          placeholder="Ring suchen..."
          item-title="ring"
          item-value="ring"
          return-object
          class="bird-search"
          density="compact"
          variant="solo"
          @update:search="debouncedSearch"
          @update:model-value="onBirdSelected"
          :filter="() => true"
          :custom-filter="() => true"
        >
          <template v-slot:item="{ item }">
            <div class="d-flex align-center py-1 px-2 suggestion-item" @click="navigateToBird(item.raw)">
              <v-icon icon="mdi-bird" color="primary" size="small" class="mr-2"></v-icon>
              <div class="flex-grow-1">
                <div><strong>{{ item.raw.ring }}</strong> - {{ item.raw.species }}</div>
                <div class="text-caption">
                  {{ item.raw.sighting_count }} 
                  Sichtung{{ item.raw.sighting_count !== 1 ? 'en' : '' }} | 
                  Letzte Sichtung: {{ formatDate(item.raw.last_seen) }}
                </div>
              </div>
              <v-btn
                icon
                size="small"
                variant="text"
                color="primary"
                @click.stop="navigateToBird(item.raw)"
                class="ml-2"
              >
                <v-icon>mdi-eye</v-icon>
                <v-tooltip activator="parent" location="bottom">
                  Details anzeigen
                </v-tooltip>
              </v-btn>
            </div>
          </template>

          <!-- Custom no-data slot to differentiate between loading and no results -->
          <template v-slot:no-data>
            <div class="pa-2">
              <div v-if="isLoading" class="d-flex align-center">
                <v-progress-circular
                  indeterminate
                  size="20"
                  width="2"
                  color="primary"
                  class="mr-2"
                ></v-progress-circular>
                <span>Suche läuft...</span>
              </div>
              <div v-else-if="noResults && searchQuery.length >= 2" class="text-center">
                <v-icon icon="mdi-alert-circle-outline" color="warning" class="mr-1"></v-icon>
                Keine Ergebnisse gefunden
              </div>
              <div v-else-if="searchQuery.length < 2" class="text-center text-medium-emphasis">
                Bitte mindestens 2 Zeichen eingeben
              </div>
            </div>
          </template>

          <!-- Add message for additional results -->
          <template v-slot:append-item v-if="totalResults > 50">
            <div class="pa-2 text-caption text-center text-medium-emphasis">
              {{ totalResults - 50 }} weitere Ergebnisse verfügbar
            </div>
          </template>
        </v-autocomplete>
      </div>

      <v-spacer></v-spacer>

      <!-- Right section -->
      <div class="navigation-buttons pe-4">
        <template v-if="authStore.isAuthenticated">
          <v-btn 
            to="/new-entry" 
            variant="text"
            class="nav-btn"
          >
            <v-icon icon="mdi-plus" class="me-1"></v-icon>
            Neuer Eintrag
          </v-btn>
          <v-btn 
            to="/entries" 
            variant="text"
            class="nav-btn"
          >
            <v-icon icon="mdi-format-list-bulleted" class="me-1"></v-icon>
            Eintragliste
          </v-btn>
          <v-btn 
            to="/ringing" 
            variant="text"
            class="nav-btn"
          >
            <v-icon icon="mdi-ring" class="me-1"></v-icon>
            Beringungen
          </v-btn>
          <v-btn 
            to="/statistics" 
            variant="text"
            class="nav-btn"
          >
            <v-icon icon="mdi-chart-line" class="me-1"></v-icon>
            Statistiken
          </v-btn>
          
          <!-- User menu -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                variant="text"
                icon
                class="user-menu-btn"
              >
                <v-icon size="28">mdi-account-circle</v-icon>
              </v-btn>
            </template>
            <v-list class="user-menu">
              <v-list-item v-if="authStore.userAttributes?.email">
                <v-list-item-title>{{ authStore.userAttributes.email }}</v-list-item-title>
                <v-list-item-subtitle>Angemeldet</v-list-item-subtitle>
              </v-list-item>
              <v-divider />
              <v-list-item @click="handleLogout">
                <v-list-item-prepend>
                  <v-icon>mdi-logout</v-icon>
                </v-list-item-prepend>
                <v-list-item-title>Abmelden</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </template>
        <template v-else>
          <v-btn 
            to="/auth/login" 
            variant="outlined"
            class="auth-nav-btn login-btn"
          >
            Anmelden
          </v-btn>
          <v-btn 
            to="/auth/register" 
            variant="elevated"
            class="auth-nav-btn register-btn"
          >
            Registrieren
          </v-btn>
        </template>
      </div>
    </v-app-bar>

    <v-main>
      <v-container class="px-6">
        <router-view :key="$route.fullPath"></router-view>
      </v-container>
    </v-main>

    <Footer />
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import Footer from './components/layout/Footer.vue';
import { api } from './api';
import { useRouter } from 'vue-router';
import debounce from 'lodash/debounce';
import { SuggestionBird } from './types';
import { useAuthStore } from './stores/auth';

interface Sighting {
  id: string;
  excel_id: number;
  species: string;
  ring: string;
  reading: string;
  date: string;
  place: string;
  group_size: number | null;
  comment: string | null;
  melder: string;
  melded: boolean;
  lat: number;
  lon: number;
  habitat: string;
}

// Use the SuggestionBird type directly instead of redefining it
type BirdSuggestion = SuggestionBird;

const router = useRouter();
const authStore = useAuthStore();
const version = ref<string>();
const searchQuery = ref('');
const suggestions = ref<BirdSuggestion[]>([]);
const isLoading = ref(false);
const selectedBird = ref<BirdSuggestion | null>(null);
const totalResults = ref(0);
const noResults = ref(false);
const latestRequestId = ref(0); // To track the latest request

// Updated computed property - no sorting needed, API provides sorted results
const sortedSuggestions = computed(() => {
  // Store total count
  totalResults.value = suggestions.value.length;
  
  // Return only first 50 results
  return suggestions.value.slice(0, 50);
});

// Format date helper function
const formatDate = (date: string | null) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('de-DE');
};

// Format the autocomplete item text for display
const formatBirdInfo = (item: SuggestionBird) => {
  return {
    title: `${item.ring} - ${item.species}`,
    subtitle: `${item.sighting_count} Sichtung${item.sighting_count !== 1 ? 'en' : ''} | Letzte Sichtung: ${formatDate(item.last_seen)}`
  };
};

// Debounced search function
const debouncedSearch = debounce(async (query: string) => {
  if (!query || query.length < 2) {
    suggestions.value = [];
    noResults.value = false;
    return;
  }

  isLoading.value = true;
  noResults.value = false;
  
  // Generate a unique request ID
  const currentRequestId = ++latestRequestId.value;
  
  try {
    console.log(`Sending request for query "${query}" (request ID: ${currentRequestId})`);
    const response = await api.get<BirdSuggestion[]>(`/birds/suggestions/${query}`);
    
    // Only update if this is still the latest request
    if (currentRequestId === latestRequestId.value) {
      console.log(`Received ${response.data.length} suggestions for query "${query}"`);
      suggestions.value = response.data;
      noResults.value = response.data.length === 0;
      
      // Debugging log to see the structure of the response data
      if (response.data.length > 0) {
        console.log('First suggestion:', JSON.stringify(response.data[0]));
      }
    } else {
      console.log(`Discarding stale response for query "${query}" (request ID: ${currentRequestId})`);
    }
  } catch (error) {
    // Only update if this is still the latest request
    if (currentRequestId === latestRequestId.value) {
      console.error('Failed to fetch suggestions:', error);
      suggestions.value = [];
      noResults.value = true;
    }
  } finally {
    // Only update if this is still the latest request
    if (currentRequestId === latestRequestId.value) {
      isLoading.value = false;
    }
  }
}, 900);

// Handle bird selection
const onBirdSelected = (bird: BirdSuggestion | null) => {
  if (bird) {
    router.push(`/birds/${bird.ring}`);
    selectedBird.value = null;
    searchQuery.value = '';
  }
};

// Navigate to bird details page
const navigateToBird = (bird: BirdSuggestion) => {
  router.push(`/birds/${bird.ring}`);
  selectedBird.value = null;
  searchQuery.value = '';
};

// Navigate to home
const navigateToHome = () => {
  if (authStore.isAuthenticated) {
    router.push('/');
  } else {
    router.push('/auth/login');
  }
};

// Handle user logout
const handleLogout = async () => {
  try {
    await authStore.signOut();
    router.push('/auth/login');
  } catch (error) {
    console.error('Logout failed:', error);
  }
};

onMounted(async () => {
  try {
    const response = await api.get('/health');
    version.value = response.data.version;
  } catch (error) {
    console.error('Failed to fetch version:', error);
  }
});
</script>

<style>
/* App Header Styling */
.app-header {
  background: linear-gradient(135deg, #00436C 0%, #228096 100%) !important;
  box-shadow: 0 4px 20px rgba(0, 67, 108, 0.3) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.app-title {
  color: white !important;
  flex-shrink: 0 !important;
  min-width: fit-content !important;
}

.logo-icon {
  color: white;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.title-text {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.025em;
}

.version-text {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-left: 8px;
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Navigation Buttons */
.nav-btn {
  color: white !important;
  text-transform: none !important;
  font-weight: 500 !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
  margin: 0 4px !important;
  backdrop-filter: blur(10px);
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.15) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.nav-btn:active {
  transform: translateY(0);
}

.nav-btn .v-icon {
  opacity: 0.9;
}

.nav-btn:hover .v-icon {
  opacity: 1;
}

/* Auth Navigation Buttons */
.auth-nav-btn {
  text-transform: none !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
  margin: 0 4px !important;
}

.login-btn {
  color: white !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
}

.login-btn:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  transform: translateY(-1px);
}

.register-btn {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #00436C !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) !important;
}

.register-btn:hover {
  background: white !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

/* User Menu */
.user-menu-btn {
  color: white !important;
  transition: all 0.3s ease !important;
}

.user-menu-btn:hover {
  background: rgba(255, 255, 255, 0.15) !important;
  transform: scale(1.05);
}

.user-menu {
  border-radius: 12px !important;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15) !important;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

/* Search Container */
.search-container {
  width: 100%;
  max-width: 400px;
  margin: 0 24px;
}

.bird-search {
  width: 100%;
}

.bird-search .v-field {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 12px !important;
  min-height: 40px !important;
  height: 40px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.bird-search .v-field:hover {
  background: white !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.bird-search .v-field--focused {
  background: white !important;
  box-shadow: 0 4px 20px rgba(0, 67, 108, 0.2);
  border-color: rgba(255, 255, 255, 0.4) !important;
}

.bird-search .v-field input {
  color: #00436C !important;
  font-weight: 500;
}

.bird-search .v-field input::placeholder {
  color: rgba(0, 67, 108, 0.6) !important;
}

/* Suggestion Items */
.suggestion-item {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 8px;
  margin: 2px 4px;
}

.suggestion-item:hover {
  background: linear-gradient(135deg, rgba(0, 67, 108, 0.05) 0%, rgba(34, 128, 150, 0.05) 100%);
  transform: translateX(4px);
}

.v-btn {
  margin-left: 8px;
  text-transform: none;
  font-weight: 400;
  box-shadow: none !important;
}

/* Style for disabled buttons */
.v-btn.v-btn--disabled {
  background-color: #E0E0E0 !important;
  color: #FFFFFF !important;
  opacity: 1 !important;
}

.v-card {
  border: 1px solid #DED5CA !important;
  background-color: #FFFFFF !important;
  box-shadow: none !important;
  transition: all 0.3s ease;
}

.v-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
}

.v-text-field .v-field {
  box-shadow: none !important;
  border: 1px solid #DED5CA !important;
  border-radius: 8px !important;
  transition: all 0.3s ease;
}

.v-text-field .v-field:hover {
  border-color: #228096 !important;
  box-shadow: 0 2px 8px rgba(34, 128, 150, 0.1) !important;
}

.v-text-field .v-field--focused {
  border-color: #00436C !important;
  box-shadow: 0 2px 12px rgba(0, 67, 108, 0.2) !important;
}

/* Remove underline from input fields */
.v-field__outline {
  --v-field-border-width: 0 !important;
}

/* Remove underline from select fields as well */
.v-select .v-field__outline {
  --v-field-border-width: 0 !important;
}

/* Optional: Style the dropdown menu */
.bird-search .v-list {
  background-color: #FFFFFF;
  border: 1px solid #DED5CA;
  color: rgba(0, 0, 0, 0.87);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.bird-search .v-list-item:hover {
  background: linear-gradient(135deg, rgba(0, 67, 108, 0.05) 0%, rgba(34, 128, 150, 0.05) 100%);
}

/* Navigation buttons container */
.navigation-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.bird-search .v-list-item__title strong {
  color: #00436C;
}

.bird-search .v-list-item__subtitle {
  color: #228096;
}

/* Add styles for the "more results" message */
.bird-search .v-autocomplete__append-item {
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  background-color: #f5f5f5;
}

/* Force hide the dropdown icon */
.bird-search .v-field__append-inner {
  display: none !important;
}

/* Adjust the field input wrapper height */
.bird-search .v-field__input {
  min-height: 40px !important;
  padding: 0 12px !important;
}

/* Styles for loading and no-results states */
.bird-search .v-autocomplete__no-data {
  padding: 8px;
  min-height: 48px;
}

.bird-search .v-autocomplete__no-data .v-progress-circular {
  margin-right: 8px;
}

.bird-search .v-autocomplete__no-data .text-center {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
}

.suggestion-item .v-btn {
  opacity: 0.7;
  transition: all 0.2s ease;
}

.suggestion-item:hover .v-btn {
  opacity: 1;
  transform: scale(1.05);
}

/* Enhanced button styling */
.v-btn {
  transition: all 0.3s ease !important;
}

.v-btn:hover {
  transform: translateY(-1px);
}

.v-btn:active {
  transform: translateY(0);
}

/* Force white background for login page */
.v-application.v-theme--light {
  background-color: #ffffff !important;
}

.v-main {
  background-color: #ffffff !important;
}

/* Responsive adjustments */
@media (max-width: 960px) {
  .search-container {
    display: none;
  }
  
  .navigation-buttons {
    gap: 4px;
  }
  
  .nav-btn .v-icon {
    display: none;
  }
}

@media (max-width: 600px) {
  .navigation-buttons {
    flex-direction: column;
    gap: 2px;
  }
  
  .nav-btn, .auth-nav-btn {
    font-size: 0.875rem !important;
    padding: 0 12px !important;
  }
}
</style>