/**
 * Sighting age/sex coding — the single frontend source of truth for the RING
 * EURING integer codes used by sightings (the same scheme Ringings use).
 *
 * Age labels come from AGE_MAPPING (ageMapping.ts) so sightings and ringings
 * share one legend. Sightings render them as "<code> <label>" (e.g. "3 Diesjährig").
 */
import { SightingAgeCode, SightingSexCode } from '@/types';
import { AGE_MAPPING } from '@/utils/ageMapping';

export interface CodeOption {
  title: string;
  value: number;
}

/** Age options for a sighting dropdown, e.g. { title: '3 Diesjährig', value: 3 }. */
export function getSightingAgeOptions(): CodeOption[] {
  return Object.values(AGE_MAPPING).map((a) => ({
    title: `${a.value} ${a.label}`,
    value: a.value,
  }));
}

/** Human label for a sighting age code (blank for null/undefined). */
export function formatSightingAge(code: number | null | undefined): string {
  if (code === null || code === undefined) return '';
  const a = AGE_MAPPING[code as number];
  return a ? `${a.value} ${a.label}` : `${code}`;
}

export const SIGHTING_SEX_LABELS: Record<number, string> = {
  [SightingSexCode.Unbekannt]: 'Unbekannt',
  [SightingSexCode.Maennlich]: 'Männlich',
  [SightingSexCode.Weiblich]: 'Weiblich',
};

/** Sex options for a sighting dropdown. */
export function getSightingSexOptions(): CodeOption[] {
  return [
    { title: 'Männlich', value: SightingSexCode.Maennlich },
    { title: 'Weiblich', value: SightingSexCode.Weiblich },
    { title: 'Unbekannt', value: SightingSexCode.Unbekannt },
  ];
}

/** Human label for a sighting sex code (blank for null/undefined). */
export function formatSightingSex(code: number | null | undefined): string {
  if (code === null || code === undefined) return '';
  return SIGHTING_SEX_LABELS[code] ?? `${code}`;
}

/** Invert the sighting sex for an inferred partner (M↔W), else undefined. */
export function invertSightingSex(
  code: number | null | undefined,
): SightingSexCode | undefined {
  if (code === SightingSexCode.Maennlich) return SightingSexCode.Weiblich;
  if (code === SightingSexCode.Weiblich) return SightingSexCode.Maennlich;
  return undefined;
}
