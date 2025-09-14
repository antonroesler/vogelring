<template>
  <v-dialog v-model="dialog" max-width="800" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-update</v-icon>
        <span>What's New in Vogelring</span>
        <v-spacer></v-spacer>
        <v-chip 
          color="primary" 
          variant="outlined" 
          size="small"
        >
          v{{ latestVersion }}
        </v-chip>
      </v-card-title>

      <v-card-text class="pa-0">
        <v-tabs v-model="selectedTab" color="primary" class="px-4">
          <v-tab 
            v-for="(release, index) in visibleReleases" 
            :key="release.version"
            :value="index"
            class="text-none"
          >
            v{{ release.version }}
            <v-chip 
              v-if="index === 0" 
              color="primary" 
              size="x-small" 
              class="ml-2"
            >
              New
            </v-chip>
          </v-tab>
        </v-tabs>

        <v-divider></v-divider>

        <v-window v-model="selectedTab" class="px-4 py-3" style="min-height: 300px; max-height: 500px; overflow-y: auto;">
          <v-window-item 
            v-for="(release, index) in visibleReleases" 
            :key="release.version"
            :value="index"
          >
            <div class="mb-3">
              <div class="text-h6 mb-1">Version {{ release.version }}</div>
              <div class="text-caption text-medium-emphasis mb-3">{{ formatDate(release.date) }}</div>
            </div>

            <div v-if="Object.keys(release.sections).length === 0" class="text-body-2 text-medium-emphasis">
              No changelog entries available for this version.
            </div>

            <div v-for="(items, sectionName) in release.sections" :key="sectionName" class="mb-4">
              <div class="text-subtitle-1 font-weight-medium mb-2 d-flex align-center">
                <v-icon :color="getSectionColor(sectionName)" size="small" class="mr-2">
                  {{ getSectionIcon(sectionName) }}
                </v-icon>
                {{ sectionName }}
              </div>
              <v-list density="compact" class="pa-0">
                <v-list-item 
                  v-for="(item, itemIndex) in items" 
                  :key="itemIndex"
                  class="px-0"
                  min-height="auto"
                >
                  <template #prepend>
                    <v-icon size="x-small" class="mr-2 mt-1">mdi-circle-small</v-icon>
                  </template>
                  <v-list-item-title class="text-body-2 text-wrap">{{ item }}</v-list-item-title>
                </v-list-item>
              </v-list>
            </div>
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="px-4 py-3">
        <v-checkbox
          v-model="dontShowAgain"
          label="Don't show this for future updates"
          density="compact"
          hide-details
        ></v-checkbox>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="dismiss">
          Later
        </v-btn>
        <v-btn color="primary" variant="elevated" @click="markAsRead">
          Got it!
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface ChangelogRelease {
  version: string
  date: string
  sections: Record<string, string[]>
}

interface Props {
  modelValue: boolean
  releases: ChangelogRelease[]
  latestVersion: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'dismiss'): void
  (e: 'markAsRead', dontShowAgain: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const selectedTab = ref(0)
const dontShowAgain = ref(false)

const dialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Show only the latest 3 releases to keep the dialog manageable
const visibleReleases = computed(() => props.releases.slice(0, 3))

const formatDate = (dateString: string) => {
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })
  } catch {
    return dateString
  }
}

const getSectionIcon = (sectionName: string) => {
  const section = sectionName.toLowerCase()
  if (section.includes('feature')) return 'mdi-star'
  if (section.includes('fix') || section.includes('bug')) return 'mdi-bug-outline'
  if (section.includes('improvement') || section.includes('perf')) return 'mdi-trending-up'
  if (section.includes('breaking')) return 'mdi-alert-circle-outline'
  if (section.includes('security')) return 'mdi-shield-outline'
  if (section.includes('deprecat')) return 'mdi-clock-outline'
  if (section.includes('doc')) return 'mdi-book-outline'
  if (section.includes('test')) return 'mdi-test-tube'
  if (section.includes('build') || section.includes('ci')) return 'mdi-cog-outline'
  return 'mdi-information-outline'
}

const getSectionColor = (sectionName: string) => {
  const section = sectionName.toLowerCase()
  if (section.includes('feature')) return 'success'
  if (section.includes('fix') || section.includes('bug')) return 'warning'
  if (section.includes('improvement') || section.includes('perf')) return 'info'
  if (section.includes('breaking')) return 'error'
  if (section.includes('security')) return 'error'
  if (section.includes('deprecat')) return 'warning'
  return 'primary'
}

const dismiss = () => {
  emit('dismiss')
}

const markAsRead = () => {
  emit('markAsRead', dontShowAgain.value)
}
</script>

<style scoped>
.v-window {
  background: transparent;
}

.v-list-item {
  padding-left: 0 !important;
  padding-right: 0 !important;
}

.v-list-item-title {
  line-height: 1.4 !important;
}
</style>
