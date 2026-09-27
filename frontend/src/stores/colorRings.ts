import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import * as api from '@/api';
import type { ColorRing, Sighting } from '@/types';

// Registry of Farbringe, used to show a bird's color ring next to its metal ring
export const useColorRingsStore = defineStore('colorRings', () => {
  const colorRings = ref<ColorRing[]>([]);
  const loading = ref(false);
  let pending: Promise<void> | null = null;

  const byRing = computed(() => {
    const map = new Map<string, ColorRing>();
    for (const cr of colorRings.value) {
      if (cr.ring) map.set(cr.ring, cr);
    }
    return map;
  });

  const load = async (force = false) => {
    if (pending && !force) return pending;
    loading.value = true;
    pending = api.getColorRings()
      .then(result => { colorRings.value = result; })
      .catch(error => {
        console.error('Error loading color rings:', error);
        pending = null;
      })
      .finally(() => { loading.value = false; });
    return pending;
  };

  const forRing = (ring?: string | null) => (ring ? byRing.value.get(ring) : undefined);

  // What a sighting shows: the color ring read in the field, else the bird's known one
  const forSighting = (sighting: Sighting) => {
    if (sighting.color_ring_code && sighting.color_ring_color) {
      return {
        ring_color: sighting.color_ring_color,
        text_color: sighting.color_ring_text_color,
        code: sighting.color_ring_code,
      };
    }
    return forRing(sighting.ring);
  };

  // Registry entry for the color ring read in a sighting (unknown text color matches any)
  const findForSighting = (sighting: Sighting) => {
    if (!sighting.color_ring_color || !sighting.color_ring_code) return undefined;
    const candidates = colorRings.value.filter(cr =>
      cr.ring_color === sighting.color_ring_color &&
      cr.code === sighting.color_ring_code &&
      (!sighting.color_ring_text_color || !cr.text_color || cr.text_color === sighting.color_ring_text_color)
    );
    return candidates.length === 1 ? candidates[0] : undefined;
  };

  const upsert = (colorRing: ColorRing) => {
    const index = colorRings.value.findIndex(cr => cr.id === colorRing.id);
    if (index >= 0) colorRings.value.splice(index, 1, colorRing);
    else colorRings.value.push(colorRing);
  };

  const remove = (id: string) => {
    colorRings.value = colorRings.value.filter(cr => cr.id !== id);
  };

  return { colorRings, loading, load, forRing, forSighting, findForSighting, upsert, remove };
});
