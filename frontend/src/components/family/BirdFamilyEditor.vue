<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon icon="mdi-family-tree" class="me-2" color="primary"></v-icon>
      Familienbeziehungen
    </v-card-title>
    
    <v-card-text>
      <v-progress-circular
        v-if="loading"
        indeterminate
        color="primary"
        class="ma-4"
      ></v-progress-circular>

      <template v-else>
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="partners">
            <v-icon icon="mdi-heart" class="me-2"></v-icon>
            Partner ({{ uniquePartnerRelationships.length }})
          </v-tab>
          <v-tab value="children">
            <v-icon icon="mdi-baby-face" class="me-2"></v-icon>
            Nachkommen ({{ uniqueChildrenRelationships.length }})
          </v-tab>
          <v-tab value="parents">
            <v-icon icon="mdi-account-supervisor" class="me-2"></v-icon>
            Eltern ({{ uniqueParentRelationships.length }})
          </v-tab>
          <v-tab value="siblings">
            <v-icon icon="mdi-account-group" class="me-2"></v-icon>
            Geschwister ({{ uniqueSiblingRelationships.length }})
          </v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <!-- Partners Tab -->
          <v-tabs-window-item value="partners">
            <family-overview-list
              :relationships="uniquePartnerRelationships"
              :bird-ring="ring"
              relationship-type="Partner"
            />
          </v-tabs-window-item>

          <!-- Children Tab -->
          <v-tabs-window-item value="children">
            <family-overview-list
              :relationships="uniqueChildrenRelationships"
              :bird-ring="ring"
              relationship-type="Nachkommen"
            />
          </v-tabs-window-item>

          <!-- Parents Tab -->
          <v-tabs-window-item value="parents">
            <family-overview-list
              :relationships="uniqueParentRelationships"
              :bird-ring="ring"
              relationship-type="Eltern"
            />
          </v-tabs-window-item>

          <!-- Siblings Tab -->
          <v-tabs-window-item value="siblings">
            <family-overview-list
              :relationships="uniqueSiblingRelationships"
              :bird-ring="ring"
              relationship-type="Geschwister"
            />
          </v-tabs-window-item>
        </v-tabs-window>

        <!-- Show All Relationships Button -->
        <v-btn
          :to="`/family-relations?bird_ring=${ring}`"
          target="_blank"
          color="primary"
          variant="elevated"
          block
          size="large"
          class="mt-4 show-all-btn"
          prepend-icon="mdi-open-in-new"
        >
          Alle Beziehungen anzeigen
        </v-btn>
      </template>
    </v-card-text>

  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { getBirdRelationships } from '@/api';
import FamilyOverviewList from './FamilyOverviewList.vue';

interface Relationship {
  id: string;
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

const props = defineProps<{
  ring: string;
}>();

const relationships = ref<Relationship[]>([]);
const loading = ref(false);
const activeTab = ref('partners');

// Computed properties to filter relationships by type
const partners = computed(() => 
  relationships.value.filter(rel => rel.relationship_type === 'breeding_partner')
);

const children = computed(() => 
  relationships.value.filter(rel => 
    rel.relationship_type === 'parent_of' && rel.bird1_ring === props.ring
  )
);

const parents = computed(() => 
  relationships.value.filter(rel => 
    rel.relationship_type === 'child_of' && rel.bird1_ring === props.ring
  )
);

const siblings = computed(() => 
  relationships.value.filter(rel => rel.relationship_type === 'sibling_of')
);

// Create unique relationships (one per bird per year for each relationship type)
const uniquePartnerRelationships = computed(() => {
  const unique = new Map();
  partners.value.forEach(rel => {
    const otherBird = rel.bird1_ring === props.ring ? rel.bird2_ring : rel.bird1_ring;
    const key = `${otherBird}-${rel.year}`;
    if (!unique.has(key)) {
      unique.set(key, {
        otherBird,
        year: rel.year,
        displayType: 'Partner'
      });
    }
  });
  return Array.from(unique.values());
});

const uniqueChildrenRelationships = computed(() => {
  const unique = new Map();
  children.value.forEach(rel => {
    const otherBird = rel.bird2_ring;
    const key = `${otherBird}-${rel.year}`;
    if (!unique.has(key)) {
      unique.set(key, {
        otherBird,
        year: rel.year,
        displayType: 'Nachkomme'
      });
    }
  });
  return Array.from(unique.values());
});

const uniqueParentRelationships = computed(() => {
  const unique = new Map();
  parents.value.forEach(rel => {
    const otherBird = rel.bird2_ring;
    const key = `${otherBird}-${rel.year}`;
    if (!unique.has(key)) {
      unique.set(key, {
        otherBird,
        year: rel.year,
        displayType: 'Elternteil'
      });
    }
  });
  return Array.from(unique.values());
});

const uniqueSiblingRelationships = computed(() => {
  const unique = new Map();
  siblings.value.forEach(rel => {
    const otherBird = rel.bird1_ring === props.ring ? rel.bird2_ring : rel.bird1_ring;
    const key = `${otherBird}-${rel.year}`;
    if (!unique.has(key)) {
      unique.set(key, {
        otherBird,
        year: rel.year,
        displayType: 'Geschwister'
      });
    }
  });
  return Array.from(unique.values());
});


const loadRelationships = async () => {
  if (!props.ring) return;
  
  loading.value = true;
  try {
    relationships.value = await getBirdRelationships(props.ring);
  } catch (error) {
    console.error('Error loading relationships:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadRelationships();
});
</script>

<style scoped>
:deep(.v-tab) {
  font-size: 0.875rem;
}

:deep(.v-tabs-window-item) {
  padding: 0;
}

.show-all-btn {
  border-radius: 12px !important;
  font-weight: 600 !important;
  text-transform: none !important;
  letter-spacing: 0.025em !important;
  background: linear-gradient(135deg, #00436C 0%, #228096 100%) !important;
  box-shadow: 0 4px 16px rgba(0, 67, 108, 0.3) !important;
  transition: all 0.3s ease !important;
}

.show-all-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 67, 108, 0.4) !important;
}
</style>
