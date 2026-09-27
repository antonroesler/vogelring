<template>
  <span
    v-if="colorRing?.code"
    class="color-ring"
    :class="`color-ring--${size}`"
    role="img"
    :aria-label="ariaLabel"
    :title="ariaLabel"
  >
    <span class="color-ring__band" :style="bandStyle">{{ colorRing.code }}</span>
    <span v-if="showLabel" class="color-ring__label">{{ colors }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import {
  getColor,
  contrastHex,
  describeColors,
  describeColorRing,
  type ColorRingLike,
} from '@/utils/colorRings';

const props = withDefaults(defineProps<{
  colorRing?: ColorRingLike | null;
  size?: 'small' | 'default' | 'large';
  // Spelled-out colors next to the ring (detail views); lists rely on the tooltip
  showLabel?: boolean;
}>(), {
  colorRing: null,
  size: 'default',
  showLabel: true,
});

const ringHex = computed(() => getColor(props.colorRing?.ring_color)?.hex ?? '#9e9e9e');
const textHex = computed(
  () => getColor(props.colorRing?.text_color)?.hex ?? contrastHex(ringHex.value)
);

const bandStyle = computed(() => ({
  backgroundColor: ringHex.value,
  color: textHex.value,
}));

const colors = computed(() => {
  const text = props.colorRing ? describeColors(props.colorRing) : '';
  return text.charAt(0).toUpperCase() + text.slice(1);
});

const ariaLabel = computed(() =>
  props.colorRing ? `Farbring ${describeColorRing(props.colorRing)}` : ''
);
</script>

<style scoped>
.color-ring {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  vertical-align: middle;
  white-space: nowrap;
}

.color-ring__band {
  display: inline-block;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-weight: 600;
  letter-spacing: 0.06em;
  border-radius: 6px;
  /* Keeps white and yellow rings visible on white backgrounds */
  border: 1px solid rgba(0, 0, 0, 0.18);
}

.color-ring__label {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
}

.color-ring--small .color-ring__band {
  padding: 0 6px;
  font-size: 0.75rem;
  line-height: 1.25rem;
}

.color-ring--default .color-ring__band {
  padding: 0 8px;
  font-size: 0.875rem;
  line-height: 1.5rem;
}

.color-ring--large .color-ring__band {
  padding: 2px 12px;
  font-size: 1.125rem;
  line-height: 1.75rem;
}
</style>
