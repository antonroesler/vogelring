<template>
  <v-card class="mt-4">
    <v-card-text>
      <v-row>
        <v-col cols="12">
          <friends-map
            :bird="selectedBird"
            :friends="friendResponse?.friends || []"
            :friend-colors="friendColors"
            :seen-status="friendResponse?.seen_status ?? {}"
          />
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '@/api';
import { BirdMeta, FriendResponse, SeenStatus } from '@/types';
import FriendsMap from '@/components/map/FriendsMap.vue';

const selectedBird = ref<BirdMeta | null>(null);
const friendResponse = ref<FriendResponse | null>(null);
const friendColors = ref<Record<string, string>>({});

const selectBird = async (ring: string) => {
  try {
    friendResponse.value = await api.getBirdFriends(ring);
    selectedBird.value = friendResponse.value.bird;
    
    // Log the response to verify the seen_status
    console.log('Friend response:', friendResponse.value);
    console.log('Seen status:', friendResponse.value?.seen_status);
    
    // ... rest of the function
  } catch (error) {
    console.error('Error loading bird friends:', error);
  }
};

// ... rest of the component
</script> 