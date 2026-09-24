<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="900">
    <v-card>
      <v-card-title class="d-flex align-center">
        Export-Verlauf
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" density="comfortable" @click="close"></v-btn>
      </v-card-title>

      <v-tabs v-model="tab" color="green-darken-2">
        <v-tab value="history">Verlauf</v-tab>
        <v-tab value="backfill">Früheren Export nachtragen</v-tab>
      </v-tabs>

      <v-card-text>
        <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = ''">
          {{ error }}
        </v-alert>

        <v-window v-model="tab">
          <!-- ---------------------------------------------------------- -->
          <v-window-item value="history">
            <p class="text-body-2 text-medium-emphasis mb-4">
              Jeder Export merkt sich, welche Einträge er enthalten hat. Sobald die
              Vogelwarte die Lieferung angenommen hat, können genau diese Einträge
              hier gesammelt als <strong>gemeldet</strong> markiert werden.
            </p>

            <div v-if="loading" class="text-center py-8">
              <v-progress-circular indeterminate color="green-darken-2"></v-progress-circular>
            </div>

            <v-alert v-else-if="runs.length === 0" type="info" variant="tonal">
              Noch keine Exporte aufgezeichnet. Exporte, die vor dieser Funktion
              erstellt wurden, lassen sich im Reiter „Früheren Export nachtragen“ erfassen.
            </v-alert>

            <v-expansion-panels v-else v-model="openPanel" variant="accordion">
              <v-expansion-panel v-for="run in runs" :key="run.id" :value="run.id">
                <v-expansion-panel-title>
                  <div class="d-flex align-center flex-wrap ga-2 w-100">
                    <span class="font-weight-medium">{{ formatDateTime(run.created_at) }}</span>
                    <v-chip size="small" variant="tonal">{{ formatRange(run) }}</v-chip>
                    <v-chip size="small" variant="tonal">{{ run.row_count }} Einträge</v-chip>
                    <v-chip v-if="run.source === 'manual'" size="small" color="grey" variant="tonal">
                      Nachtrag
                    </v-chip>
                    <v-spacer></v-spacer>
                    <v-chip
                      size="small"
                      :color="run.pending_count === 0 ? 'success' : 'warning'"
                      variant="flat"
                    >
                      {{ run.pending_count === 0 ? 'gemeldet' : `${run.pending_count} offen` }}
                    </v-chip>
                  </div>
                </v-expansion-panel-title>

                <v-expansion-panel-text>
                  <div v-if="run.note" class="text-body-2 mb-2">
                    <strong>Notiz:</strong> {{ run.note }}
                  </div>
                  <div v-if="run.marked_melded_at" class="text-body-2 text-medium-emphasis mb-3">
                    Als gemeldet markiert am {{ formatDateTime(run.marked_melded_at) }}
                    ({{ run.marked_count }} Einträge).
                  </div>

                  <div class="d-flex ga-2 mb-4 flex-wrap">
                    <v-btn
                      v-if="run.pending_count > 0"
                      color="green-darken-2"
                      variant="flat"
                      size="small"
                      prepend-icon="mdi-check-all"
                      :loading="busyId === run.id"
                      @click="confirmMark(run)"
                    >
                      {{ run.pending_count }} Einträge als gemeldet markieren
                    </v-btn>
                    <v-btn
                      v-if="run.marked_melded_at"
                      variant="tonal"
                      size="small"
                      prepend-icon="mdi-undo"
                      :loading="busyId === run.id"
                      @click="handleUnmark(run)"
                    >
                      Markierung rückgängig
                    </v-btn>
                  </div>

                  <div v-if="itemsLoading" class="text-center py-4">
                    <v-progress-circular indeterminate size="24"></v-progress-circular>
                  </div>
                  <v-table v-else-if="items.length" density="compact" class="export-items">
                    <thead>
                      <tr>
                        <th>Datum</th>
                        <th>Ring</th>
                        <th>Spezies</th>
                        <th>Ort</th>
                        <th>Gemeldet</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in items" :key="item.id">
                        <td>{{ formatDate(item.date) }}</td>
                        <td>{{ item.ring || '—' }}</td>
                        <td>{{ item.species ? resolveSpeciesName(item.species) : '—' }}</td>
                        <td>{{ item.place || '—' }}</td>
                        <td>
                          <v-icon
                            :icon="item.melded ? 'mdi-check-circle' : 'mdi-circle-outline'"
                            :color="item.melded ? 'success' : 'grey'"
                            size="small"
                          ></v-icon>
                        </td>
                      </tr>
                    </tbody>
                  </v-table>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-window-item>

          <!-- ---------------------------------------------------------- -->
          <v-window-item value="backfill">
            <p class="text-body-2 text-medium-emphasis mb-4">
              Für einen Export, der bereits an die Vogelwarte ging, bevor der Verlauf
              aufgezeichnet wurde. Es werden genau die Einträge erfasst, die der Export
              damals enthalten hätte: noch nicht gemeldet, im Zeitraum — und, falls
              gesetzt, vor dem Export-Zeitpunkt erfasst.
            </p>

            <v-row dense>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="backfillStart"
                  label="Von (Datum)"
                  type="date"
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="backfillEnd"
                  label="Bis (Datum)"
                  type="date"
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="backfillCreatedBefore"
                  label="Export-Zeitpunkt (optional)"
                  type="datetime-local"
                  variant="outlined"
                  density="comfortable"
                  hint="Schützt Einträge, die erst nach dem Export erfasst wurden — sie bleiben ungemeldet."
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="backfillNote"
                  label="Notiz (optional)"
                  variant="outlined"
                  density="comfortable"
                  placeholder="z. B. Export Ingo, 22.07.2026 — von Vogelwarte angenommen"
                ></v-text-field>
              </v-col>
            </v-row>

            <div class="d-flex ga-2 align-center mb-4 flex-wrap">
              <v-btn
                variant="tonal"
                prepend-icon="mdi-magnify"
                :loading="checking"
                :disabled="!backfillStart"
                @click="handleCheck"
              >
                Prüfen
              </v-btn>
              <span v-if="checked" class="text-body-2">
                <strong>{{ checkResult?.matched ?? 0 }}</strong> Einträge würden als
                gemeldet markiert.
              </span>
            </div>

            <v-table v-if="checkResult?.preview?.length" density="compact" class="mb-4 export-items">
              <thead>
                <tr>
                  <th>Datum</th>
                  <th>Ring</th>
                  <th>Spezies</th>
                  <th>Ort</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in checkResult.preview" :key="row.id">
                  <td>{{ formatDate(row.date) }}</td>
                  <td>{{ row.ring || '—' }}</td>
                  <td>{{ row.species ? resolveSpeciesName(row.species) : '—' }}</td>
                  <td>{{ row.place || '—' }}</td>
                </tr>
              </tbody>
            </v-table>
            <p
              v-if="checkResult && checkResult.matched > checkResult.preview.length"
              class="text-caption text-medium-emphasis mb-4"
            >
              Vorschau der ersten {{ checkResult.preview.length }} von
              {{ checkResult.matched }} Einträgen.
            </p>

            <v-alert
              v-if="checked && (checkResult?.matched ?? 0) > 0"
              type="warning"
              variant="tonal"
              class="mb-4"
            >
              Dies ändert {{ checkResult?.matched }} Einträge auf „gemeldet“. Der Vorgang
              wird im Verlauf festgehalten und kann dort rückgängig gemacht werden.
            </v-alert>

            <v-btn
              color="green-darken-2"
              variant="flat"
              prepend-icon="mdi-check-all"
              :loading="committing"
              :disabled="!checked || (checkResult?.matched ?? 0) === 0"
              @click="handleCommit"
            >
              Nachtragen & als gemeldet markieren
            </v-btn>
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="close">Schließen</v-btn>
      </v-card-actions>
    </v-card>

    <v-dialog v-model="confirmDialog" max-width="460">
      <v-card>
        <v-card-title>Als gemeldet markieren?</v-card-title>
        <v-card-text class="text-body-2">
          {{ pendingRun?.pending_count }} Einträge aus dem Export vom
          {{ formatDateTime(pendingRun?.created_at ?? null) }} werden auf „gemeldet“
          gesetzt. Das lässt sich hier wieder rückgängig machen.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="confirmDialog = false">Abbrechen</v-btn>
          <v-btn color="green-darken-2" variant="flat" @click="handleMark">Markieren</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup lang="ts">
import { resolveSpeciesName } from '@/utils/species';
import { ref, watch } from 'vue';
import {
  getSightingExports,
  getSightingExportItems,
  markSightingExportMelded,
  unmarkSightingExportMelded,
  backfillSightingExport,
  type SightingExportRun,
  type SightingExportItem,
} from '@/api';

const props = defineProps<{ modelValue: boolean }>();
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  // Sightings changed in bulk — the caller should reload its list.
  changed: [message: string];
}>();

const tab = ref('history');
const loading = ref(false);
const error = ref('');
const runs = ref<SightingExportRun[]>([]);
const openPanel = ref<string | undefined>(undefined);
const items = ref<SightingExportItem[]>([]);
const itemsLoading = ref(false);
const busyId = ref<string | null>(null);

const confirmDialog = ref(false);
const pendingRun = ref<SightingExportRun | null>(null);

const backfillStart = ref('2026-01-01');
const backfillEnd = ref('');
const backfillCreatedBefore = ref('');
const backfillNote = ref('');
const checking = ref(false);
const committing = ref(false);
const checked = ref(false);
const checkResult = ref<Awaited<ReturnType<typeof backfillSightingExport>> | null>(null);

// Backend timestamps are naive UTC — mark them as such before parsing, otherwise
// the browser reads them as local time and shifts them by the UTC offset.
const parseUtc = (value: string | null) => {
  if (!value) return null;
  const normalized = /[Zz]|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const formatDateTime = (value: string | null) => {
  const parsed = parseUtc(value);
  return parsed ? parsed.toLocaleString('de-DE', { dateStyle: 'medium', timeStyle: 'short' }) : '—';
};

const formatDate = (value: string | null) => {
  if (!value) return '—';
  const [year, month, day] = value.split('-');
  return day ? `${day}.${month}.${year}` : value;
};

const formatRange = (run: SightingExportRun) => {
  const from = formatDate(run.start_date);
  return run.end_date ? `${from} – ${formatDate(run.end_date)}` : `ab ${from}`;
};

// The user picks a local wall-clock time; created_at is stored as naive UTC.
const toNaiveUtc = (localValue: string) => {
  const parsed = new Date(localValue);
  if (Number.isNaN(parsed.getTime())) return undefined;
  return parsed.toISOString().slice(0, 19);
};

const loadRuns = async () => {
  loading.value = true;
  error.value = '';
  try {
    runs.value = await getSightingExports();
  } catch (err) {
    console.error('Error loading export history:', err);
    error.value = 'Export-Verlauf konnte nicht geladen werden.';
  } finally {
    loading.value = false;
  }
};

const loadItems = async (exportId: string) => {
  itemsLoading.value = true;
  items.value = [];
  try {
    items.value = await getSightingExportItems(exportId);
  } catch (err) {
    console.error('Error loading export items:', err);
    error.value = 'Einträge des Exports konnten nicht geladen werden.';
  } finally {
    itemsLoading.value = false;
  }
};

watch(openPanel, (exportId) => {
  if (exportId) loadItems(exportId);
  else items.value = [];
});

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      loadRuns();
      openPanel.value = undefined;
      checked.value = false;
      checkResult.value = null;
    }
  }
);

const close = () => emit('update:modelValue', false);

const confirmMark = (run: SightingExportRun) => {
  pendingRun.value = run;
  confirmDialog.value = true;
};

const handleMark = async () => {
  const run = pendingRun.value;
  confirmDialog.value = false;
  if (!run) return;

  busyId.value = run.id;
  error.value = '';
  try {
    const result = await markSightingExportMelded(run.id);
    await loadRuns();
    if (openPanel.value === run.id) await loadItems(run.id);
    emit('changed', `${result.marked} Einträge als gemeldet markiert`);
  } catch (err) {
    console.error('Error marking export as melded:', err);
    error.value = 'Markieren fehlgeschlagen. Bitte erneut versuchen.';
  } finally {
    busyId.value = null;
    pendingRun.value = null;
  }
};

const handleUnmark = async (run: SightingExportRun) => {
  busyId.value = run.id;
  error.value = '';
  try {
    const result = await unmarkSightingExportMelded(run.id);
    await loadRuns();
    if (openPanel.value === run.id) await loadItems(run.id);
    emit('changed', `${result.unmarked} Einträge wieder auf nicht gemeldet gesetzt`);
  } catch (err) {
    console.error('Error unmarking export:', err);
    error.value = 'Rückgängig machen fehlgeschlagen. Bitte erneut versuchen.';
  } finally {
    busyId.value = null;
  }
};

const backfillPayload = (dryRun: boolean) => ({
  start_date: backfillStart.value,
  end_date: backfillEnd.value || undefined,
  created_before: backfillCreatedBefore.value
    ? toNaiveUtc(backfillCreatedBefore.value)
    : undefined,
  note: backfillNote.value || undefined,
  dry_run: dryRun,
});

const handleCheck = async () => {
  checking.value = true;
  error.value = '';
  try {
    checkResult.value = await backfillSightingExport(backfillPayload(true));
    checked.value = true;
  } catch (err) {
    console.error('Error checking backfill:', err);
    error.value = 'Prüfung fehlgeschlagen. Bitte erneut versuchen.';
    checked.value = false;
  } finally {
    checking.value = false;
  }
};

const handleCommit = async () => {
  committing.value = true;
  error.value = '';
  try {
    const result = await backfillSightingExport(backfillPayload(false));
    checked.value = false;
    checkResult.value = null;
    tab.value = 'history';
    await loadRuns();
    emit('changed', `${result.marked ?? 0} Einträge nachgetragen und als gemeldet markiert`);
  } catch (err) {
    console.error('Error committing backfill:', err);
    error.value = 'Nachtragen fehlgeschlagen. Bitte erneut versuchen.';
  } finally {
    committing.value = false;
  }
};

// Any change to the date range invalidates a previous check, so the commit
// button can never act on numbers the user has not actually seen.
watch([backfillStart, backfillEnd, backfillCreatedBefore], () => {
  checked.value = false;
  checkResult.value = null;
});
</script>

<style scoped>
.export-items {
  max-height: 320px;
  overflow-y: auto;
}
</style>
