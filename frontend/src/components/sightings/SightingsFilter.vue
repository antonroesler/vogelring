<template>
  <v-card class="mb-4">
    <v-card-text>
      <v-row>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.species"
            label="Spezies"
            clearable
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.ring"
            label="Ring"
            clearable
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.place"
            label="Ort"
            clearable
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            v-model="filters.melder"
            label="Melder"
            clearable
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            type="date"
            v-model="filters.start_date"
            label="Von"
            clearable
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-text-field
            type="date"
            v-model="filters.end_date"
            label="Bis"
            clearable
            @update:model-value="emitFilters"
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="6" lg="3">
          <v-select
            v-model="filters.melded"
            label="Gemeldet"
            :items="[
              { title: 'Alle', value: undefined },
              { title: 'Ja', value: true },
              { title: 'Nein', value: false }
            ]"
            clearable
            @update:model-value="emitFilters"
          ></v-select>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Filters {
  species?: string;
  ring?: string;
  place?: string;
  melder?: string;
  start_date?: string;
  end_date?: string;
  melded?: boolean;
}

const emit = defineEmits<{
  'update:filters': [filters: Filters];
}>();

const filters = ref<Filters>({});

const emitFilters = () => {
  emit('update:filters', filters.value);
};
</script>