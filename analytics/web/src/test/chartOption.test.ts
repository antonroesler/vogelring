import { describe, expect, it } from 'vitest'
import { buildChartOption, type ChartModel } from '../lib/chartOption'

const base = { width: 1200, height: 700, x_axis: {}, y_axis: {} }

describe('buildChartOption', () => {
  it('builds a stacked month chart with totals and a band annotation', () => {
    const model: ChartModel = {
      ...base,
      kind: 'stacked_bar',
      categories: ['Jan', 'Feb'],
      series: [
        { name: 'Ostpark', data: [3, 4], color: '#2E8B57', stack: 'total' },
        { name: 'Rebstock', data: [2, 0], color: '#228096', stack: 'total' },
      ],
      stack: true,
      show_totals: true,
      totals: [5, 4],
      annotations: [{ kind: 'band', from: 'Jan', to: 'Feb', label: 'Mauser', color: '#228096' }],
    }
    const opt = buildChartOption(model)
    expect(opt.xAxis.type).toBe('category')
    expect(opt.series).toHaveLength(3)
    expect(opt.series[0].stack).toBe('total')
    expect(opt.series[2].name).toBe('__totals')
    expect(opt.series[0].markArea.data[0][0].name).toBe('Mauser')
    expect(opt.legend.data).toEqual(['Ostpark', 'Rebstock'])
  })

  it('builds a timeline with one scatter series per class', () => {
    const model: ChartModel = {
      ...base,
      kind: 'timeline',
      rows: ['A', 'B'],
      series: [],
      timeline: {
        points: [
          { row: 0, t: '2025-05-01', cls: 'Apr–Jun', color: '#2E8B57', tip: 'A' },
          { row: 1, t: '2025-11-02', cls: 'Nov–Jan', color: '#1E3A8A', tip: 'B' },
        ],
        classes: [
          { name: 'Apr–Jun', color: '#2E8B57' },
          { name: 'Nov–Jan', color: '#1E3A8A' },
        ],
        min: '2025-05-01',
        max: '2025-11-02',
      },
    }
    const opt = buildChartOption(model)
    expect(opt.xAxis.type).toBe('time')
    expect(opt.yAxis.data).toEqual(['A', 'B'])
    expect(opt.series.map((s: any) => s.type)).toEqual(['scatter', 'scatter'])
    expect(opt.legend.data).toEqual(['Apr–Jun', 'Nov–Jan'])
  })

  it('splits a sankey with long target labels into a wide right margin', () => {
    const model: ChartModel = {
      ...base,
      kind: 'sankey',
      series: [],
      sankey: {
        nodes: [
          { name: 'A', label: 'A', color: '#111111' },
          { name: 'Sehr langer Zielname mit vielen Zeichen', label: 'Sehr langer Zielname mit vielen Zeichen', color: '#222222' },
        ],
        links: [{ source: 'A', target: 'Sehr langer Zielname mit vielen Zeichen', value: 5 }],
      },
    }
    const opt = buildChartOption(model)
    expect(opt.series[0].type).toBe('sankey')
    expect(opt.series[0].right).toBeGreaterThan(200)
  })
})
