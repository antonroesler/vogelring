/**
 * Centralized status utilities for consistent formatting and styling across the application
 */

import { BirdStatus } from '@/types';

export interface StatusInfo {
  label: string;
  color: string;
  icon?: string;
}

export const STATUS_CONFIG: Record<string, StatusInfo> = {
  'BV': {
    label: 'Brutvogel',
    color: 'success',
    icon: 'mdi-heart'
  },
  'MG': {
    label: 'Mausergast',
    color: 'info',
    icon: 'mdi-feather'
  },
  'NB': {
    label: 'Nichtbrüter',
    color: 'warning',
    icon: 'mdi-bird'
  },
  'RV': {
    label: 'Reviervogel',
    color: 'primary',
    icon: 'mdi-home-variant'
  },
  'TF': {
    label: 'Totfund',
    color: 'error',
    icon: 'mdi-close-circle'
  }
};

/**
 * Format bird status for display
 */
export const formatBirdStatus = (status?: string | null): string => {
  if (!status) return '-';
  return STATUS_CONFIG[status]?.label || status;
};

/**
 * Get color for bird status
 */
export const getBirdStatusColor = (status?: string | null): string => {
  if (!status) return 'grey';
  return STATUS_CONFIG[status]?.color || 'grey';
};

/**
 * Get icon for bird status
 */
export const getBirdStatusIcon = (status?: string | null): string | undefined => {
  if (!status) return undefined;
  return STATUS_CONFIG[status]?.icon;
};

/**
 * Get complete status info
 */
export const getBirdStatusInfo = (status?: string | null): StatusInfo => {
  if (!status) {
    return {
      label: '-',
      color: 'grey'
    };
  }
  return STATUS_CONFIG[status] || {
    label: status,
    color: 'grey'
  };
};

/**
 * Check if a bird is dead based on its sightings
 */
export const isBirdDead = (sightings?: Array<{ status?: string | null }>): boolean => {
  if (!sightings) return false;
  return sightings.some(sighting => sighting.status === BirdStatus.TOTFUND);
};

/**
 * All available bird statuses
 */
export const ALL_BIRD_STATUSES = Object.keys(STATUS_CONFIG);
