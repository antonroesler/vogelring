<template>
  <v-toolbar 
    flat 
    class="secondary-nav" 
    height="56"
    color="surface"
    border="b"
    elevation="0"
  >
    <v-container class="d-flex align-center px-3 px-sm-4 px-md-6">
      <div class="nav-items">
        <v-btn 
          :to="{ path: '/new-entry' }"
          variant="text"
          class="secondary-nav-btn"
          :class="{ 'active': isActive('/new-entry') }"
        >
          <v-icon icon="mdi-plus" class="me-2"></v-icon>
          Neuer Eintrag
        </v-btn>
        
        <v-btn 
          :to="{ path: '/entries' }"
          variant="text"
          class="secondary-nav-btn"
          :class="{ 'active': isActive('/entries') }"
        >
          <v-icon icon="mdi-format-list-bulleted" class="me-2"></v-icon>
          Eintragliste
        </v-btn>
        
        <v-btn 
          :to="{ path: '/ringing' }"
          variant="text"
          class="secondary-nav-btn"
          :class="{ 'active': isActive('/ringing') }"
        >
          <v-icon icon="mdi-ring" class="me-2"></v-icon>
          Beringungen
        </v-btn>
        
        <v-btn 
          :to="{ path: '/family-relations' }"
          variant="text"
          class="secondary-nav-btn"
          :class="{ 'active': isActive('/family-relations') }"
        >
          <v-icon icon="mdi-family-tree" class="me-2"></v-icon>
          Familienbeziehungen
        </v-btn>
        
        <v-btn 
          :to="{ path: '/statistics' }"
          variant="text"
          class="secondary-nav-btn"
          :class="{ 'active': isActive('/statistics') }"
        >
          <v-icon icon="mdi-chart-line" class="me-2"></v-icon>
          Statistiken
        </v-btn>
      </div>
    </v-container>
  </v-toolbar>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const isActive = (path: string) => {
  return route.path.startsWith(path);
};
</script>

<style scoped>
.secondary-nav {
  background: rgba(255, 255, 255, 0.98) !important;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 67, 108, 0.1) !important;
  box-shadow: none !important;
  position: sticky !important;
  top: 0 !important;
  z-index: 1000 !important;
  margin: 0 !important;
}

.nav-items {
  display: flex;
  gap: 8px;
  align-items: center;
  width: 100%;
}

.secondary-nav-btn {
  color: rgba(0, 67, 108, 0.7) !important;
  text-transform: none !important;
  font-weight: 500 !important;
  border-radius: 8px !important;
  transition: background-color 0.3s ease, color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease !important;
  padding: 0 16px !important;
  height: 40px !important;
  min-width: auto !important;
}

.secondary-nav-btn:hover {
  background: rgba(0, 67, 108, 0.08) !important;
  color: rgba(0, 67, 108, 0.9) !important;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 67, 108, 0.15);
}

.secondary-nav-btn.active {
  background: rgba(0, 67, 108, 0.12) !important;
  color: #00436C !important;
  font-weight: 500 !important;
}

.secondary-nav-btn.active .v-icon {
  color: #00436C !important;
}

.secondary-nav-btn .v-icon {
  opacity: 0.8;
  transition: all 0.3s ease;
}

.secondary-nav-btn:hover .v-icon,
.secondary-nav-btn.active .v-icon {
  opacity: 1;
}

/* Responsive adjustments */
@media (max-width: 960px) {
  .nav-items {
    gap: 4px;
  }
  
  .secondary-nav-btn {
    padding: 0 12px !important;
    font-size: 0.875rem !important;
  }
  
  .secondary-nav-btn .v-icon {
    font-size: 18px !important;
  }
}

@media (max-width: 600px) {
  .nav-items {
    gap: 4px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    padding-bottom: 4px;
  }

  .nav-items::-webkit-scrollbar {
    display: none;
  }

  .secondary-nav-btn {
    padding: 0 10px !important;
    font-size: 0.8rem !important;
    height: 36px !important;
    flex-shrink: 0;
  }

  .secondary-nav-btn .v-icon {
    font-size: 16px !important;
    margin-right: 4px !important;
  }
}
</style>
