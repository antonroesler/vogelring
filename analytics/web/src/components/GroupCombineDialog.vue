<template>
  <v-dialog v-model="open" max-width="640" scrollable>
    <v-card class="pa-6">
      <div class="card-title">Gruppen verknüpfen</div>
      <div class="muted mb-4" style="font-size: 13px">Aus bestehenden Gruppen entsteht eine neue Gruppe. Sie verweist auf die anderen – ändert sich dort etwas, folgt sie mit.</div>

      <v-select v-model="ids" :items="props.groups" item-title="name" item-value="id" label="Gruppen (mindestens zwei)" multiple chips closable-chips hide-details class="mb-4">
        <template #chip="{ props: cp, item }"><v-chip v-bind="cp"><span class="dot" :style="{ background: item.raw.color || '#8aa' }" />{{ item.raw.name }}</v-chip></template>
        <template #item="{ props: ip, item }"><v-list-item v-bind="ip" :title="item.raw.name" :subtitle="item.raw.describe"><template #prepend><span class="dot mr-3" :style="{ background: item.raw.color || '#8aa' }" /></template></v-list-item></template>
      </v-select>

      <div class="section-label">Verknüpfung</div>
      <v-radio-group v-model="op" hide-details class="mb-2">
        <v-radio value="union"><template #label><span><strong>Vereinigung</strong> <span class="muted">– in mindestens einer der Gruppen</span></span></template></v-radio>
        <v-radio value="intersection"><template #label><span><strong>Schnittmenge</strong> <span class="muted">– in allen Gruppen zugleich</span></span></template></v-radio>
        <v-radio value="difference"><template #label><span><strong>Differenz</strong> <span class="muted">– die erste ohne die übrigen</span></span></template></v-radio>
      </v-radio-group>
      <div v-if="op === 'difference' && names.length" class="muted mb-4" style="font-size: 12.5px">Grundlage ist die zuerst gewählte Gruppe „{{ names[0] }}“; davon werden {{ names.slice(1).map((n) => `„${n}“`).join(' und ') || '…' }} abgezogen.</div>
      <div v-else class="mb-4" />

      <div class="section-label">Art der Gruppe</div>
      <v-btn-toggle v-model="scope" mandatory class="vr-toggle mb-2">
        <v-btn value="sightings" prepend-icon="mdi-binoculars">Sichtungen</v-btn>
        <v-btn value="birds" prepend-icon="mdi-bird">Vögel</v-btn>
      </v-btn-toggle>
      <div class="muted mb-4" style="font-size: 12.5px">
        <template v-if="scope === 'birds'">Alle Einträge der Vögel, die in der verknüpften Auswahl vorkommen – also auch, wo diese Vögel sonst noch gesehen wurden.</template>
        <template v-else>Nur die Einträge, die die Verknüpfung erfüllen.</template>
      </div>

      <v-text-field v-model="name" label="Name der neuen Gruppe" hide-details class="mb-3" @keyup.enter="save" />
      <v-textarea v-model="description" label="Worum geht es? (optional)" rows="2" auto-grow hide-details class="mb-4" />
      <v-alert v-if="error" type="warning" variant="tonal" class="mb-3" :text="error" />

      <div class="d-flex justify-end ga-2">
        <v-btn variant="text" @click="open = false">Abbrechen</v-btn>
        <v-btn color="primary" prepend-icon="mdi-set-center" :disabled="ids.length < 2 || !name.trim()" :loading="saving" @click="save">Gruppe anlegen</v-btn>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, type GroupScope, type GroupSummary } from '@/api/client'
import { friendlyError } from '@/lib/format'
import { useMetaStore } from '@/stores/meta'

type Op = 'union' | 'intersection' | 'difference'
const props = defineProps<{ modelValue: boolean; groups: GroupSummary[]; preselect?: string[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()
const router = useRouter()
const meta = useMetaStore()

const open = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })
const ids = ref<string[]>([])
const op = ref<Op>('union')
const scope = ref<GroupScope>('sightings')
const name = ref('')
const description = ref('')
const saving = ref(false)
const error = ref('')
let nameTouched = false

const names = computed(() => ids.value.map((id) => props.groups.find((g) => g.id === id)?.name || id))
const WORD: Record<Op, string> = { union: ' oder ', intersection: ' und ', difference: ' ohne ' }
const suggested = computed(() => (names.value.length >= 2 ? names.value.join(WORD[op.value]).slice(0, 120) : ''))

watch(open, (v) => {
  if (v) {
    ids.value = props.preselect?.length ? [...props.preselect] : []
    op.value = 'union'
    scope.value = 'sightings'
    description.value = ''
    error.value = ''
    nameTouched = false
    name.value = suggested.value
  }
})
watch(suggested, (v) => {
  if (!nameTouched) name.value = v
})
watch(name, (v) => {
  if (v !== suggested.value) nameTouched = true
})

async function save() {
  if (ids.value.length < 2 || !name.value.trim()) return
  saving.value = true
  error.value = ''
  try {
    const g = await api.combineGroups({ name: name.value.trim(), op: op.value, group_ids: ids.value, scope: scope.value, description: description.value.trim() })
    meta.notify('Gruppe angelegt.')
    open.value = false
    router.push(`/gruppen/${g.id}`)
  } catch (e) {
    error.value = friendlyError(e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; flex: none; }
</style>
