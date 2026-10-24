<template>
  <div class="vr-table-wrap" :style="{ fontSize: (model.font_size || 13) + 'px' }">
    <table class="vr-table">
      <thead>
        <tr>
          <th v-if="model.row_number" class="rn">#</th>
          <th v-for="(c, i) in model.columns" :key="c.name" :class="c.align" :style="c.width ? { width: c.width + 'px' } : undefined" @click="sortBy(i)">
            {{ c.label }}<span v-if="sortCol === i">{{ sortAsc ? ' ▲' : ' ▼' }}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, r) in rows" :key="r">
          <td v-if="model.row_number" class="rn">{{ r + 1 }}</td>
          <td v-for="(cell, i) in row" :key="i" :class="[model.columns[i].align, cell.hl ? 'hl' : '']">
            <span v-if="cell.bar !== undefined" class="bar" :style="{ width: (cell.bar * 100).toFixed(1) + '%' }" />
            <a v-if="cell.href" :href="cell.href" target="_blank" rel="noopener">{{ cell.text }}</a>
            <span v-else class="t">{{ cell.text }}</span>
          </td>
        </tr>
      </tbody>
      <tfoot v-if="model.totals">
        <tr>
          <td v-if="model.row_number" class="rn" />
          <td v-for="(t, i) in model.totals" :key="i" :class="model.columns[i].align">{{ t }}</td>
        </tr>
      </tfoot>
    </table>
    <div v-if="model.total_rows > model.shown_rows" class="muted" style="padding: 8px 2px; font-size: 0.9em">{{ model.shown_rows }} von {{ model.total_rows }} Zeilen – vollständig im Excel-Export.</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Cell { text: string; value?: any; bar?: number; hl?: boolean; href?: string }
interface TableModel { columns: { name: string; label: string; align: string; numeric: boolean; width?: number }[]; rows: Cell[][]; totals?: string[] | null; total_rows: number; shown_rows: number; row_number?: boolean; font_size?: number }

const props = defineProps<{ model: TableModel }>()
const sortCol = ref<number | null>(null)
const sortAsc = ref(false)
watch(() => props.model, () => (sortCol.value = null))

function sortBy(i: number) {
  if (sortCol.value === i) sortAsc.value = !sortAsc.value
  else {
    sortCol.value = i
    sortAsc.value = false
  }
}

const rows = computed(() => {
  const r = props.model.rows.slice()
  const i = sortCol.value
  if (i === null) return r
  const numeric = props.model.columns[i].numeric
  r.sort((a, b) => {
    const va = a[i].value ?? a[i].text
    const vb = b[i].value ?? b[i].text
    let x: any = numeric ? (va === undefined || va === '' ? -Infinity : Number(va)) : String(va).toLowerCase()
    let y: any = numeric ? (vb === undefined || vb === '' ? -Infinity : Number(vb)) : String(vb).toLowerCase()
    if (x < y) return sortAsc.value ? -1 : 1
    if (x > y) return sortAsc.value ? 1 : -1
    return 0
  })
  return r
})
</script>
