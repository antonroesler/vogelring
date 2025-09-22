<template>
  <div>
    <v-card-subtitle class="px-0 mt-4">Nachkommen</v-card-subtitle>
    <div v-for="(child, index) in children" :key="index" class="mb-3">
      <v-row>
        <v-col cols="6">
          <v-text-field
            v-model="child.ring"
            :label="`Kind ${index + 1} Ring`"
            density="comfortable"
          ></v-text-field>
        </v-col>
        <v-col cols="2">
          <v-select
            v-model="child.age"
            :items="ageOptions"
            label="Alter"
            item-title="text"
            item-value="value"
            density="comfortable"
          ></v-select>
        </v-col>
        <v-col cols="3">
          <v-select
            v-model="child.sex"
            :items="sexOptions"
            label="Geschlecht"
            density="comfortable"
          ></v-select>
        </v-col>
        <v-col cols="1">
          <v-btn
            icon="mdi-delete"
            variant="text"
            color="error"
            size="small"
            @click="removeChild(index)"
          ></v-btn>
        </v-col>
      </v-row>
    </div>
    
    <v-btn
      variant="outlined"
      prepend-icon="mdi-plus"
      @click="addChild"
      size="small"
    >
      Kind hinzufügen
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { getRingingAgeOptions } from '@/utils/ageMapping';

const emit = defineEmits<{
  'update:children': [children: Array<{ ring: string; age?: number; sex?: string }>];
}>();

const children = ref<Array<{ ring: string; age?: number; sex?: string }>>([]);
const ageOptions = getRingingAgeOptions(true);
const sexOptions = [
  { title: 'Männlich', value: 'M' },
  { title: 'Weiblich', value: 'W' }
];

const addChild = () => {
  children.value.push({ ring: '', age: undefined, sex: undefined });
  emit('update:children', children.value);
};

const removeChild = (index: number) => {
  children.value.splice(index, 1);
  emit('update:children', children.value);
};

watch(children, () => {
  emit('update:children', children.value);
}, { deep: true });
</script>
