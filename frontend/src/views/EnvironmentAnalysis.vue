<template>
  <div>
    <v-row>
      <v-col cols="12" md="8">
        <v-card class="mb-4">
          <v-card-title>Joined Map</v-card-title>
          <v-card-text>
            <div ref="mapContainer" style="height: 400px; width: 100%"></div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card class="mb-4">
          <v-card-title>Legend</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="friend in sortedFriends"
                :key="friend.ring"
                @click="toggleFriendVisibility(friend.ring)"
                style="cursor: pointer"
                class="legend-item"
              >
                <template v-slot:prepend>
                  <div class="legend-marker-container">
                    <span 
                      class="legend-marker" 
                      :style="{ 
                        color: friendColors[friend.ring],
                        opacity: hiddenMarkers.has(friend.ring) ? '0.4' : '1'
                      }"
                    >●</span>
                  </div>
                </template>
                <v-list-item-title>
                  {{ friend.ring }}
                  <v-icon
                    size="small"
                    :icon="hiddenMarkers.has(friend.ring) ? 'mdi-eye-off' : 'mdi-eye'"
                    class="ms-2"
                  ></v-icon>
                </v-list-item-title>
                <v-list-item-subtitle class="text-medium-emphasis">
                  {{ friend.species }} | Sichtungen: {{ friend.sharedCount }}
                </v-list-item-subtitle>
              </v-list-item>
              
              <!-- Border type legend -->
              <v-divider class="my-3"></v-divider>
              <div class="border-legend">
                <div class="border-legend-title text-subtitle-2 mb-2">Markierungen:</div>
                <div class="border-legend-item">
                  <div class="marker-example">
                    <div class="marker-circle" style="
                      background-color: #666666; 
                      width: 12px; 
                      height: 12px; 
                      border-radius: 50%; 
                      border: 1px solid white;
                      box-shadow: 0 0 3px rgba(0,0,0,0.3);
                    "></div>
                  </div>
                  <span class="text-body-2">Befreundeter Vogel</span>
                </div>
                <div class="border-legend-item">
                  <div class="marker-example">
                    <div class="marker-circle" style="
                      background-color: #999999; 
                      width: 12px; 
                      height: 12px; 
                      border-radius: 50%; 
                      border: 1px solid #666666;
                      box-shadow: 0 0 3px rgba(0,0,0,0.3);
                    "></div>
                  </div>
                  <span class="text-body-2">Anderer Vogel</span>
                </div>
              </div>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title>Date Maps</v-card-title>
          <v-card-text>
            <v-select
              v-model="selectedDate"
              :items="availableDates"
              label="Datum auswählen"
              @update:model-value="handleDateSelection"
            ></v-select>
            <div ref="dateMapContainer" style="height: 400px; width: 100%"></div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import { useRoute } from 'vue-router';
import * as api from '@/api';
import type { BirdMeta, AnalyticsBirdMeta } from '@/types';

const route = useRoute();
const mapContainer = ref<HTMLElement | null>(null);
const dateMapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const dateMap = ref<L.Map | null>(null);
const markers = ref<L.Marker[]>([]);
const dateMarkers = ref<L.Marker[]>([]);
const selectedDate = ref<string | null>(null);
const availableDates = ref<string[]>([]);
const friendColors = ref<Record<string, string>>({});
const sortedFriends = ref<AnalyticsBirdMeta[]>([]);
const hiddenMarkers = ref(new Set<string>());
const activePopup = ref<{
  marker: L.Marker;
  element: HTMLElement;
  mapType: 'joined' | 'date';
} | null>(null);
const bird = ref<BirdMeta | null>(null);
const friends = ref<AnalyticsBirdMeta[]>([]);
const originalDates = ref<Record<string, string>>({});

const createOffsetCoordinates = (sightings: Sighting[]) => {
  const offsetMap = new Map<string, number>();
  const result = new Map<string, { lat: number; lon: number }>();

  sightings.forEach(sighting => {
    if (!sighting.lat || !sighting.lon) return;
    
    const key = `${sighting.lat},${sighting.lon}`;
    const count = offsetMap.get(key) || 0;
    offsetMap.set(key, count + 1);

    if (count === 0) {
      // First sighting at this location - use original coordinates
      result.set(sighting.ring, { lat: sighting.lat, lon: sighting.lon });
    } else {
      // Create offset in a circular pattern
      const angle = (2 * Math.PI * count) / 8; // Divide circle into 8 parts
      const offsetDistance = 0.00015; // About 15 meters
      const offsetLat = sighting.lat + Math.cos(angle) * offsetDistance;
      const offsetLon = sighting.lon + Math.sin(angle) * offsetDistance;
      result.set(sighting.ring, { lat: offsetLat, lon: offsetLon });
    }
  });

  return result;
};

const loadEnvironmentData = async () => {
  const ring = route.params.ring as string;
  const friendsData = await api.getBirdFriends(ring);
  bird.value = friendsData.bird;
  friends.value = friendsData.friends;
  const birdSightings = friendsData.bird.sightings || [];

  // Assign colors to friends
  friends.value.forEach((friend, index) => {
    friendColors.value[friend.ring] = `hsl(${(index * 360) / friends.value.length}, 70%, 50%)`;
  });

  // Determine shared sightings
  friends.value.forEach(friend => {
    friend.sharedCount = 0;
    friend.sightings.forEach(sighting => {
      if (birdSightings.some(b => b.date === sighting.date && b.place === sighting.place)) {
        friend.sharedCount++;
      }
    });
  });

  sortedFriends.value = friends.value.sort((a, b) => b.sharedCount - a.sharedCount);

  // Initialize map
  if (mapContainer.value) {
    map.value = L.map(mapContainer.value, {
      zoomControl: true,
      attributionControl: true
    }).setView([50.1109, 8.6821], 13);
    
    // Add event handlers for map movements
    map.value.on('zoomstart', closeAllTooltips);
    map.value.on('movestart', closeAllTooltips);
    map.value.on('moveend', updatePopupPosition);
    map.value.on('zoomend', updatePopupPosition);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map.value);
    
    updateMarkers(birdSightings, friends.value);
  }

  // Populate available dates with formatted dates and places
  const uniqueDates = new Set<string>();
  birdSightings.forEach(s => {
    if (s.date && s.place) {
      const formattedDate = new Date(s.date).toLocaleDateString('de-DE');
      uniqueDates.add(`${formattedDate} ${s.place}`);
    }
  });
  availableDates.value = Array.from(uniqueDates).sort();
  console.log('Available dates:', availableDates.value);

  // Store original date mapping for later use
  const dateMapping = birdSightings.reduce((acc, s) => {
    if (s.date && s.place) {
      const formattedDate = new Date(s.date).toLocaleDateString('de-DE');
      const key = `${formattedDate} ${s.place}`;
      acc[key] = s.date;
      console.log('Date mapping:', { display: key, original: s.date });
    }
    return acc;
  }, {} as Record<string, string>);

  originalDates.value = dateMapping;
};

const createCustomPopup = (content: string, marker: L.Marker, targetMap: L.Map, mapType: 'joined' | 'date') => {
  // Remove existing popup if any
  if (activePopup.value) {
    activePopup.value.element.remove();
    activePopup.value = null;
  }

  // Create popup element with close button
  const popupElement = document.createElement('div');
  popupElement.className = 'custom-popup';
  popupElement.innerHTML = `
    <div class="popup-header">
      <div class="popup-close" title="Close">
        <svg viewBox="0 0 24 24" class="close-icon">
          <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
        </svg>
      </div>
    </div>
    <div class="popup-content">
      ${content}
    </div>
  `;

  // Add click handler for close button
  const closeButton = popupElement.querySelector('.popup-close');
  if (closeButton) {
    closeButton.addEventListener('click', (e) => {
      e.stopPropagation();
      if (activePopup.value) {
        activePopup.value.element.remove();
        activePopup.value = null;
      }
    });
  }
  
  // Get marker position relative to map container
  const markerPoint = targetMap.latLngToContainerPoint(marker.getLatLng());
  const mapContainer = targetMap.getContainer();
  
  // Create wrapper and position it
  const wrapper = document.createElement('div');
  wrapper.className = 'popup-wrapper';
  wrapper.style.position = 'absolute';
  wrapper.style.left = '0';
  wrapper.style.top = '0';
  wrapper.style.width = '100%';
  wrapper.style.height = '100%';
  wrapper.style.pointerEvents = 'none';
  wrapper.style.zIndex = '1000';
  
  // Position the popup
  popupElement.style.position = 'absolute';
  popupElement.style.left = `${markerPoint.x}px`;
  popupElement.style.top = `${markerPoint.y}px`;
  popupElement.style.transform = 'translate(-50%, -100%) translateY(-10px)';
  popupElement.style.zIndex = '1000';
  
  wrapper.appendChild(popupElement);
  mapContainer.appendChild(wrapper);
  
  // Store reference to current popup
  activePopup.value = { marker, element: wrapper, mapType };
};

const updateMarkers = (birdSightings: Sighting[], friends: AnalyticsBirdMeta[]) => {
  if (!map.value) return;

  // Clear existing markers and popup
  if (activePopup.value) {
    activePopup.value.element.remove();
    activePopup.value = null;
  }
  markers.value.forEach(marker => marker.remove());
  markers.value = [];

  // Collect all sightings to calculate offsets
  const allSightings = [
    ...birdSightings,
    ...friends.flatMap(f => f.sightings)
  ];
  const offsetCoords = createOffsetCoordinates(allSightings);

  // Add bird sightings (as squares)
  birdSightings.forEach(sighting => {
    if (sighting.lat && sighting.lon) {
      const coords = offsetCoords.get(sighting.ring) || { lat: sighting.lat, lon: sighting.lon };
      const marker = L.marker([coords.lat, coords.lon], {
        icon: L.divIcon({
          className: 'custom-div-icon',
          html: `<div class="marker-square" style="
            background-color: #FF0000; 
            width: 12px; 
            height: 12px; 
            border: 1px solid white; 
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
            cursor: pointer;
          "></div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        }),
        interactive: true // Make sure marker is interactive
      });

      const popupContent = `
        <a href="/birds/${sighting.ring}" target="_blank">${sighting.ring}</a>
        <div>${sighting.species}</div>
        <div>${sighting.date}</div>
      `;

      // Add click event listener
      marker.on('click', function(e) {
        console.log('Marker clicked'); // Debug log
        L.DomEvent.preventDefault(e);
        L.DomEvent.stopPropagation(e);
        
        if (activePopup.value?.marker === marker && activePopup.value.mapType === 'joined') {
          activePopup.value.element.remove();
          activePopup.value = null;
        } else {
          createCustomPopup(popupContent, marker, map.value!, 'joined');
        }
      });

      marker.addTo(map.value);
      markers.value.push(marker);
    }
  });

  // Add friend sightings
  friends.forEach(friend => {
    if (hiddenMarkers.value.has(friend.ring)) return;

    friend.sightings.forEach(sighting => {
      if (sighting.lat && sighting.lon) {
        const coords = offsetCoords.get(friend.ring) || { lat: sighting.lat, lon: sighting.lon };
        const isShared = birdSightings.some(b => b.date === sighting.date && b.place === sighting.place);
        const color = friendColors.value[friend.ring] || '#999999'; // Fallback color if not found
        const borderColor = isShared ? 'white' : '#666666';
        
        const marker = L.marker([coords.lat, coords.lon], {
          icon: L.divIcon({
            className: 'custom-div-icon',
            html: `<div class="marker-circle" style="
              background-color: ${color}; 
              width: 12px; 
              height: 12px; 
              border-radius: 50%; 
              border: 1px solid ${borderColor};
              box-shadow: 0 0 3px rgba(0,0,0,0.3);
              cursor: pointer;
            "></div>`,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
          }),
          interactive: true
        });

        const popupContent = `
          <a href="/birds/${friend.ring}" target="_blank">${friend.ring}</a>
          <div>${friend.species}</div>
          <div>${sighting.date}</div>
        `;

        // Add click event listener
        marker.on('click', function(e) {
          console.log('Friend marker clicked'); // Debug log
          L.DomEvent.preventDefault(e);
          L.DomEvent.stopPropagation(e);
          
          if (activePopup.value?.marker === marker && activePopup.value.mapType === 'joined') {
            activePopup.value.element.remove();
            activePopup.value = null;
          } else {
            createCustomPopup(popupContent, marker, map.value!, 'joined');
          }
        });

        marker.addTo(map.value);
        markers.value.push(marker);
      }
    });
  });

  // Add click handler to map to close popup when clicking elsewhere
  map.value.off('click'); // Remove any existing click handlers
  map.value.on('click', () => {
    if (activePopup.value?.mapType === 'joined') {
      activePopup.value.element.remove();
      activePopup.value = null;
    }
  });
};

const handleDateSelection = (value: string) => {
  console.log('Date selected:', value);
  if (!dateMapContainer.value) {
    console.error('Date map container not found');
    return;
  }
  
  // Initialize map if not exists
  if (!dateMap.value) {
    console.log('Initializing date map');
    dateMap.value = L.map(dateMapContainer.value).setView([50.1109, 8.6821], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(dateMap.value);
  }
  
  updateDateMap();
};

const fetchSightingsForDate = async (date: string, place: string) => {
  try {
    const response = await api.getSightings({
      start_date: date,
      end_date: date,
      place: place
    });
    return response || []; // Ensure we always return an array
  } catch (error) {
    console.error('Error fetching sightings:', error);
    return [];
  }
};

const updateDateMap = async () => {
  console.log('Updating date map');
  if (!selectedDate.value) {
    console.log('No date selected');
    return;
  }
  if (!dateMapContainer.value) {
    console.error('Date map container not found');
    return;
  }

  console.log('Selected display date:', selectedDate.value);
  const originalDate = originalDates.value[selectedDate.value];
  console.log('Original ISO date:', originalDate);
  if (!originalDate) {
    console.error('Could not find original date for:', selectedDate.value);
    return;
  }

  // Extract place from the selected date string (format: "dd.mm.yyyy Place")
  const place = selectedDate.value.split(' ').slice(1).join(' ');

  // Clear existing date markers
  console.log('Clearing existing markers');
  dateMarkers.value.forEach(marker => marker.remove());
  dateMarkers.value = [];

  try {
    // Get all sightings for this date and place
    const allSightings = await fetchSightingsForDate(originalDate, place);
    console.log('Fetched sightings:', allSightings?.length || 0);

    if (!Array.isArray(allSightings)) {
      console.error('Received invalid sightings data:', allSightings);
      return;
    }

    // Calculate offsets for all sightings
    const offsetCoords = createOffsetCoordinates(allSightings);

    // Create sets for quick lookup of friend rings and the inspected bird's ring
    const friendRings = new Set(friends.value.map(f => f.ring));
    const inspectedBirdRing = bird.value?.ring;

    // Process all sightings
    allSightings.forEach(sighting => {
      if (sighting.lat && sighting.lon) {
        let markerColor: string;
        let borderColor: string;
        let isSquare = false;

        // Determine marker appearance based on the bird
        if (sighting.ring === inspectedBirdRing) {
          // Skip if it's the inspected bird - we'll handle it separately
          return;
        } else if (friendRings.has(sighting.ring)) {
          // Skip if it's a hidden friend
          if (hiddenMarkers.value.has(sighting.ring)) return;
          // It's a friend - use friend's color
          markerColor = friendColors.value[sighting.ring] || '#999999';
          borderColor = 'white';
        } else {
          // It's another bird - use gray with different border
          markerColor = '#999999';
          borderColor = '#666666';
        }

        const coords = offsetCoords.get(sighting.ring) || { lat: sighting.lat, lon: sighting.lon };
        const marker = L.marker([coords.lat, coords.lon], {
          icon: L.divIcon({
            className: 'custom-div-icon',
            html: `<div class="${isSquare ? 'marker-square' : 'marker-circle'}" style="
              background-color: ${markerColor}; 
              width: 12px; 
              height: 12px; 
              ${!isSquare ? 'border-radius: 50%;' : ''} 
              border: 1px solid ${borderColor};
              box-shadow: 0 0 3px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
          })
        });

        const popupContent = `
          <a href="/birds/${sighting.ring}" target="_blank">${sighting.ring}</a>
          <div>${sighting.species || 'Unbekannte Art'}</div>
          <div>${new Date(sighting.date).toLocaleDateString('de-DE')}</div>
        `;

        marker.on('click', function(e) {
          L.DomEvent.preventDefault(e);
          L.DomEvent.stopPropagation(e);
          
          if (activePopup.value?.marker === marker && activePopup.value.mapType === 'date') {
            activePopup.value.element.remove();
            activePopup.value = null;
          } else {
            createCustomPopup(popupContent, marker, dateMap.value!, 'date');
          }
        });

        marker.addTo(dateMap.value!);
        dateMarkers.value.push(marker);
      }
    });

    // Add the inspected bird's sighting last
    const birdSighting = bird.value?.sightings?.find(s => s.date === originalDate);
    if (birdSighting?.lat && birdSighting?.lon) {
      const coords = offsetCoords.get(birdSighting.ring) || { lat: birdSighting.lat, lon: birdSighting.lon };
      const marker = L.marker([coords.lat, coords.lon], {
        icon: L.divIcon({
          className: 'custom-div-icon',
          html: `<div class="marker-square" style="
            background-color: #FF0000; 
            width: 12px; 
            height: 12px; 
            border: 1px solid white;
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
          "></div>`,
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        })
      });

      const popupContent = `
        <a href="/birds/${birdSighting.ring}" target="_blank">${birdSighting.ring}</a>
        <div>${birdSighting.species || 'Unbekannte Art'}</div>
        <div>${new Date(birdSighting.date).toLocaleDateString('de-DE')}</div>
      `;

      marker.on('click', function(e) {
        L.DomEvent.preventDefault(e);
        L.DomEvent.stopPropagation(e);
        
        if (activePopup.value?.marker === marker && activePopup.value.mapType === 'date') {
          activePopup.value.element.remove();
          activePopup.value = null;
        } else {
          createCustomPopup(popupContent, marker, dateMap.value!, 'date');
        }
      });

      marker.addTo(dateMap.value!);
      dateMarkers.value.push(marker);
    }

    // Fit bounds to show all markers
    if (dateMarkers.value.length > 0) {
      const group = L.featureGroup(dateMarkers.value);
      dateMap.value.fitBounds(group.getBounds().pad(0.1));
    }
  } catch (error) {
    console.error('Error updating date map:', error);
  }
};

const toggleFriendVisibility = (ring: string) => {
  if (hiddenMarkers.value.has(ring)) {
    // Show markers
    hiddenMarkers.value.delete(ring);
    // Update all markers to maintain proper layering and colors
    updateMarkers(
      bird.value?.sightings || [], 
      friends.value.filter(f => !hiddenMarkers.value.has(f.ring))
    );
  } else {
    // Hide markers
    hiddenMarkers.value.add(ring);
    // Update all markers to maintain proper layering and colors
    updateMarkers(
      bird.value?.sightings || [], 
      friends.value.filter(f => !hiddenMarkers.value.has(f.ring))
    );
  }
};

// Update the closeAllTooltips function to handle custom popups
const closeAllTooltips = () => {
  if (activePopup.value) {
    activePopup.value.element.remove();
    activePopup.value = null;
  }
};

// Add this new function to update popup position when map moves
const updatePopupPosition = () => {
  if (activePopup.value) {
    const targetMap = activePopup.value.mapType === 'joined' ? map.value : dateMap.value;
    if (targetMap) {
      const point = targetMap.latLngToContainerPoint(activePopup.value.marker.getLatLng());
      const popup = activePopup.value.element.querySelector('.custom-popup');
      if (popup) {
        (popup as HTMLElement).style.left = `${point.x}px`;
        (popup as HTMLElement).style.top = `${point.y - 45}px`;
      }
    }
  }
};

onMounted(loadEnvironmentData);
</script>

<style>
.popup-wrapper {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  pointer-events: none !important;
  z-index: 1000 !important;
}

.custom-popup {
  position: absolute !important;
  background: white !important;
  border-radius: 4px !important;
  padding: 0 !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
  pointer-events: auto !important;
  white-space: nowrap !important;
  z-index: 1000 !important;
}

.popup-content {
  padding: 8px 12px;
  min-width: 150px;
}

.popup-content a {
  color: #1976D2;
  text-decoration: none;
  font-weight: 500;
  display: block;
  margin-bottom: 4px;
}

.popup-content a:hover {
  text-decoration: underline;
}

.popup-content div {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.87);
}

.marker-square,
.marker-circle {
  cursor: pointer !important;
  transition: transform 0.2s !important;
}

.marker-square:hover,
.marker-circle:hover {
  transform: scale(1.2) !important;
}

.custom-div-icon {
  background: none !important;
  border: none !important;
}

.legend-item {
  padding: 8px 16px;
  transition: background-color 0.2s;
}

.legend-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.legend-item .v-list-item-title {
  font-size: 1rem;
  line-height: 1.2;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
}

.legend-item .v-list-item-subtitle {
  font-size: 0.875rem;
  opacity: 0.7;
}

.legend-marker-container {
  display: flex;
  align-items: center;
  margin-right: 16px; /* Increased spacing */
  width: 24px; /* Fixed width for alignment */
}

.legend-marker {
  font-size: 24px; /* Bigger marker */
  line-height: 1;
  transition: opacity 0.2s;
}

.border-legend {
  padding: 0 16px;
}

.border-legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.marker-example {
  width: 24px;
  margin-right: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.border-legend .text-body-2 {
  color: rgba(0, 0, 0, 0.87);
}

.popup-header {
  display: flex;
  justify-content: flex-end;
  padding: 4px;
}

.popup-close {
  cursor: pointer;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  padding: 2px;
  transition: background-color 0.2s;
}

.popup-close:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.close-icon {
  width: 12px;
  height: 12px;
  fill: rgba(0, 0, 0, 0.54);
  transition: fill 0.2s;
}

.popup-close:hover .close-icon {
  fill: rgba(0, 0, 0, 0.87);
}
</style> 