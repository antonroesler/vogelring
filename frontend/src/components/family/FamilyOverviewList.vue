<template>
  <div>
    <v-list v-if="relationships.length > 0" density="compact">
      <v-list-item
        v-for="relationship in relationships"
        :key="`${relationship.otherBird}-${relationship.year}`"
        class="relationship-item"
        :to="`/birds/${relationship.otherBird}`"
        target="_blank"
      >
        <template v-slot:prepend>
          <v-icon 
            :icon="getRelationshipIcon(relationshipType)"
            :color="getRelationshipColor(relationshipType)"
            size="small"
          ></v-icon>
        </template>

        <v-list-item-title>
          {{ relationship.otherBird }}
          <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
        </v-list-item-title>

        <v-list-item-subtitle>
          {{ relationship.displayType }} ({{ relationship.year }})
        </v-list-item-subtitle>
      </v-list-item>
    </v-list>

    <v-alert v-else type="info" variant="tonal" class="text-center">
      <v-icon icon="mdi-information"></v-icon>
      Keine {{ getEmptyMessage() }} vorhanden.
    </v-alert>
  </div>
</template>

<script setup lang="ts">
interface RelationshipOverview {
  otherBird: string;
  year: number;
  displayType: string;
}

const props = defineProps<{
  relationships: RelationshipOverview[];
  birdRing: string;
  relationshipType: string;
}>();

const getRelationshipIcon = (type: string) => {
  switch (type) {
    case 'Partner': return 'mdi-heart';
    case 'Nachkommen': return 'mdi-baby-face';
    case 'Eltern': return 'mdi-account-supervisor';
    case 'Geschwister': return 'mdi-account-group';
    default: return 'mdi-help';
  }
};

const getRelationshipColor = (type: string) => {
  switch (type) {
    case 'Partner': return 'red';
    case 'Nachkommen': return 'green';
    case 'Eltern': return 'blue';
    case 'Geschwister': return 'orange';
    default: return 'grey';
  }
};

const getEmptyMessage = () => {
  return props.relationshipType;
};
</script>

<style scoped>
.relationship-item {
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all 0.2s ease;
  cursor: pointer;
}

.relationship-item:hover {
  background-color: rgba(0, 67, 108, 0.05);
  transform: translateX(4px);
}

:deep(.v-list-item__prepend) {
  margin-right: 12px;
}

:deep(.v-list-item-title) {
  font-weight: 500;
  color: #00436C;
}

:deep(.v-list-item-subtitle) {
  color: rgba(0, 0, 0, 0.6);
}
</style>
