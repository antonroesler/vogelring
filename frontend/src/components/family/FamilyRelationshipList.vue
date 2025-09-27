<template>
  <div>
    <v-list v-if="relationships.length > 0" density="compact">
      <v-list-item
        v-for="relationship in relationships"
        :key="relationship.id"
        class="relationship-item"
      >
        <template v-slot:prepend>
          <v-icon 
            :icon="getRelationshipIcon(relationship.relationship_type)"
            :color="getRelationshipColor(relationship.relationship_type)"
            size="small"
          ></v-icon>
        </template>

        <v-list-item-title>
          <v-btn
            :to="`/birds/${relationship.otherBird}`"
            target="_blank"
            variant="text"
            size="small"
            color="primary"
            class="pa-0"
          >
            {{ relationship.otherBird }}
            <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
          </v-btn>
        </v-list-item-title>

        <v-list-item-subtitle>
          {{ relationship.displayType }} ({{ relationship.year }})
          <template v-if="relationship.source && relationship.source.startsWith('sighting_')">
            • 
            <v-btn
              :to="`/entries/${relationship.source.replace('sighting_', '')}`"
              target="_blank"
              variant="text"
              size="x-small"
              color="primary"
              class="pa-0 ma-0"
              style="text-decoration: underline; min-width: auto; height: auto;"
              v-tooltip="'Zur ursprünglichen Sichtung'"
            >
              Quelle
              <v-icon size="x-small" class="ml-1">mdi-open-in-new</v-icon>
            </v-btn>
          </template>
        </v-list-item-subtitle>

        <template v-slot:append>
          <div class="d-flex">
            <v-btn
              icon="mdi-pencil"
              variant="text"
              size="x-small"
              @click="$emit('edit', relationship)"
              v-tooltip="'Bearbeiten'"
            ></v-btn>
            <v-btn
              icon="mdi-delete"
              variant="text"
              size="x-small"
              color="error"
              @click="$emit('delete', relationship)"
              v-tooltip="'Löschen'"
            ></v-btn>
          </div>
        </template>
      </v-list-item>
    </v-list>

    <v-alert v-else type="info" variant="tonal" class="text-center">
      <v-icon icon="mdi-information"></v-icon>
      Keine {{ getEmptyMessage() }} vorhanden.
    </v-alert>
  </div>
</template>

<script setup lang="ts">
interface RelationshipDisplay {
  id: string;
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: string;
  year: number;
  confidence?: string;
  source?: string;
  notes?: string;
  otherBird: string;
  displayType: string;
  created_at: string;
  updated_at: string;
}

const props = defineProps<{
  relationships: RelationshipDisplay[];
  birdRing: string;
}>();

defineEmits<{
  'edit': [relationship: RelationshipDisplay];
  'delete': [relationship: RelationshipDisplay];
}>();

const getRelationshipIcon = (type: string) => {
  switch (type) {
    case 'breeding_partner': return 'mdi-heart';
    case 'parent_of': return 'mdi-baby-face';
    case 'child_of': return 'mdi-account-supervisor';
    case 'sibling_of': return 'mdi-account-group';
    default: return 'mdi-help';
  }
};

const getRelationshipColor = (type: string) => {
  switch (type) {
    case 'breeding_partner': return 'red';
    case 'parent_of': return 'green';
    case 'child_of': return 'blue';
    case 'sibling_of': return 'orange';
    default: return 'grey';
  }
};


const getEmptyMessage = () => {
  if (props.relationships.length === 0) return 'Beziehungen';
  
  // Try to determine the type based on the first relationship
  const firstType = props.relationships[0]?.relationship_type;
  switch (firstType) {
    case 'breeding_partner': return 'Brutpartner';
    case 'parent_of': return 'Nachkommen';
    case 'child_of': return 'Eltern';
    case 'sibling_of': return 'Geschwister';
    default: return 'Beziehungen';
  }
};
</script>

<style scoped>
.relationship-item {
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all 0.2s ease;
}

.relationship-item:hover {
  background-color: rgba(0, 67, 108, 0.05);
}

:deep(.v-list-item__prepend) {
  margin-right: 12px;
}

:deep(.v-list-item__append) {
  margin-left: 8px;
}
</style>
