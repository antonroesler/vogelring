import { describe, expect, it } from 'vitest'
import { categoryColumns, defaultForm, emptyBin, fromSpec, toSpec } from '@/stores/builder'

describe('bins in the builder form', () => {
  it('emits bins only for columns used as categories and not in auto mode', () => {
    const f = defaultForm()
    f.chart_kind = 'sankey'
    f.source_column = 'ringing_place'
    f.target_column = 'km_from_ringing'
    f.bins.km_from_ringing = { ...emptyBin('km_from_ringing'), mode: 'edges', edges: '1, 5, 20, 100' }
    f.bins.max_km = { ...emptyBin('max_km'), mode: 'width', width: 10 } // not used in any role → dropped
    expect(categoryColumns(f)).toEqual(['ringing_place', 'km_from_ringing'])
    expect(toSpec(f).bins).toEqual([{ column: 'km_from_ringing', edges: [1, 5, 20, 100], unit: 'km' }])
    f.bins.km_from_ringing.mode = 'auto'
    expect(toSpec(f).bins).toBeUndefined()
  })
  it('round-trips width, edges and date parts', () => {
    const spec = { kind: 'chart', chart_kind: 'bar', source: 'birds', dimension: 'sightings', color: 'first_sighting', bins: [{ column: 'sightings', width: 5 }, { column: 'first_sighting', date_part: 'season' }] }
    const f = fromSpec(spec)
    expect(f.bins.sightings).toMatchObject({ mode: 'width', width: 5 })
    expect(f.bins.first_sighting).toMatchObject({ mode: 'date', date_part: 'season' })
    expect(toSpec(f).bins).toEqual([{ column: 'sightings', width: 5 }, { column: 'first_sighting', date_part: 'season' }])
  })
  it('table group_by uses bins too and ignores invalid edges', () => {
    const f = defaultForm()
    f.kind = 'table'
    f.group_by = ['max_km']
    f.bins.max_km = { ...emptyBin('max_km'), mode: 'edges', edges: '20, 5' }
    expect(toSpec(f).bins).toBeUndefined()
    f.bins.max_km.edges = '5; 20 50'
    expect(toSpec(f).bins).toEqual([{ column: 'max_km', edges: [5, 20, 50], unit: 'km' }])
  })
})
