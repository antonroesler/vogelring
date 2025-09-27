import axios from 'axios';
import type { Sighting, BirdMeta, FriendResponse, Dashboard, Ringing, ShareableReport, SuggestionBird, FamilyTreeEntry } from '../types';

// API configuration for local FastAPI backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  },
  timeout: 20000,
  withCredentials: false
});

export { api };

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('Making request:', config.method?.toUpperCase(), config.url, config.params || config.data);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    console.log('Response received:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('Response error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const getSightings = async (params?: {
  page?: number;
  per_page?: number;
  start_date?: string;
  end_date?: string;
  species?: string;
  place?: string;
}) => {
  console.log('Fetching sightings with params:', params);
  try {
    const response = await api.get<Sighting[]>('/sightings', { params });
    console.log('Received sightings:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in getSightings:', error);
    if (axios.isAxiosError(error)) {
      console.error('Axios error details:', {
        response: error.response,
        request: error.request,
        message: error.message
      });
    }
    throw error;
  }
};

export const getSightingById = async (id: string) => {
  console.log('Fetching sighting with id:', id);
  const response = await api.get<Sighting>(`/sightings/${id}`);
  console.log('Received sighting:', response.data);
  return response.data;
};

export const createSighting = async (sighting: Partial<Sighting>) => {
  console.log('Creating sighting:', sighting);
  const response = await api.post('/sightings', sighting);
  console.log('Created sighting:', response.data);
  return response.data;
};

export const updateSighting = async (sighting: Partial<Sighting>) => {
  console.log('Updating sighting:', sighting);
  const response = await api.put('/sightings', sighting);
  console.log('Updated sighting:', response.data);
  return response.data;
};

export const deleteSighting = async (id: string) => {
  console.log('Deleting sighting with id:', id);
  const response = await api.delete(`/sightings/${id}`);
  console.log('Delete response:', response.data);
  return response.data;
};

export const getBirdSuggestions = async (partialReading: string) => {
  console.log('Fetching bird suggestions for:', partialReading);
  const response = await api.get<SuggestionBird[]>(`/birds/suggestions/${partialReading}`);
  console.log('Received suggestions:', response.data);
  return response.data;
};

export const getBirdByRing = async (ring: string): Promise<BirdMeta | null> => {
  try {
    const response = await api.get<BirdMeta>(`/birds/${ring}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null;
    }
    throw error;
  }
};

export const getBirdFriends = async (ring: string) => {
  console.log('Fetching bird friends for ring:', ring);
  const response = await api.get<FriendResponse>(`/analytics/groups/${ring}`);
  console.log('Received friends:', response.data);
  return response.data;
};

export const getSightingsInRadius = async (lat: number, lon: number, radius: number) => {
  console.log('Fetching sightings within radius:', { lat, lon, radius });
  const response = await api.get<Sighting[]>('/sightings/radius', {
    params: {
      lat,
      lon,
      radius_m: Math.round(radius)
    }
  });
  console.log('Received sightings in radius:', response.data);
  return response.data;
};

export async function getDashboard(): Promise<Dashboard> {
  const response = await api.get<Dashboard>('/dashboard');
  return response.data;
}

export const getShareableReportUrls = async (days: number, htmlContent?: string): Promise<ShareableReport> => {
  try {
    const response = await api.post<ShareableReport>('/report/shareable', {
      days,
      html: htmlContent
    });
    
    console.log('Received shareable URL:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error getting shareable report URL:', error);
    throw new Error('Failed to generate shareable report');
  }
};

export const getRingingByRing = async (ring: string) => {
  console.log('Fetching ringing data for ring:', ring);
  const encodedRing = encodeURIComponent(ring);
  try {
    const response = await api.get<Ringing>(`/ringing/${encodedRing}`);
    console.log('Received ringing data:', response.data);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error('Axios error details:', {
        status: error.response?.status,
        data: error.response?.data,
        headers: error.response?.headers
      });
      // Return null for 404 and handle CORS errors
      if (error.response?.status === 404 || error.code === 'ERR_NETWORK') {
        return null;
      }
    }
    throw error;
  }
};

export const createRinging = async (ringing: Partial<Ringing>) => {
  console.log('Creating ringing:', ringing);
  const response = await api.post<Ringing>('/ringing', ringing);
  console.log('Created ringing:', response.data);
  return response.data;
};

export const deleteRinging = async (ring: string) => {
  console.log('Deleting ringing:', ring);
  await api.delete(`/ringing/${ring}`);
  console.log('Ringing deleted');
};

export const updateRinging = async (ringing: Partial<Ringing>) => {
  console.log('Updating ringing:', ringing);
  const response = await api.put<Ringing>('/ringing', ringing);
  console.log('Updated ringing:', response.data);
  return response.data;
};

export const getSeasonalAnalysis = async () => {
  console.log('Fetching seasonal analysis');
  const response = await api.get('/seasonal-analysis');
  console.log('Received seasonal analysis:', response.data);
  return response.data;
};

// Family Relationship API functions
export const getBirdRelationships = async (ring: string) => {
  console.log('Fetching relationships for ring:', ring);
  const response = await api.get(`/family/relationships/${ring}`);
  console.log('Received relationships:', response.data);
  return response.data;
};

export const getPartners = async (ring: string, year?: number) => {
  console.log('Fetching partners for ring:', ring);
  const params = year ? { year } : {};
  const response = await api.get(`/family/partners/${ring}`, { params });
  console.log('Received partners:', response.data);
  return response.data;
};

export const getChildren = async (ring: string, year?: number) => {
  console.log('Fetching children for ring:', ring);
  const params = year ? { year } : {};
  const response = await api.get(`/family/children/${ring}`, { params });
  console.log('Received children:', response.data);
  return response.data;
};

export const getParents = async (ring: string, year?: number) => {
  console.log('Fetching parents for ring:', ring);
  const params = year ? { year } : {};
  const response = await api.get(`/family/parents/${ring}`, { params });
  console.log('Received parents:', response.data);
  return response.data;
};

export const getSiblings = async (ring: string, year?: number) => {
  console.log('Fetching siblings for ring:', ring);
  const params = year ? { year } : {};
  const response = await api.get(`/family/siblings/${ring}`, { params });
  console.log('Received siblings:', response.data);
  return response.data;
};

export const createRelationship = async (relationship: {
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: 'breeding_partner' | 'parent_of' | 'child_of' | 'sibling_of';
  year: number;
  source?: string;
  notes?: string;
  sighting1_id?: string;
  sighting2_id?: string;
  ringing1_id?: string;
  ringing2_id?: string;
}) => {
  console.log('Creating relationship:', relationship);
  const response = await api.post('/family/relationships', relationship);
  console.log('Created relationship:', response.data);
  return response.data;
};

export const createSymmetricRelationship = async (relationship: {
  bird1_ring: string;
  bird2_ring: string;
  relationship_type: 'breeding_partner' | 'sibling_of';
  year: number;
}) => {
  console.log('Creating symmetric relationship:', relationship);
  const response = await api.post('/family/relationships/symmetric', relationship);
  console.log('Created symmetric relationship:', response.data);
  return response.data;
};

export const getAllRelationships = async (params?: {
  relationship_type?: 'breeding_partner' | 'parent_of' | 'child_of' | 'sibling_of';
  year?: number;
  bird_ring?: string;
  limit?: number;
  offset?: number;
}) => {
  console.log('Fetching all relationships with params:', params);
  const response = await api.get('/family/relationships', { params });
  console.log('Received all relationships:', response.data);
  return response.data;
};

export const updateRelationship = async (id: string, updates: {
  relationship_type?: 'breeding_partner' | 'parent_of' | 'child_of' | 'sibling_of';
  year?: number;
  source?: string;
  notes?: string;
}, updateSymmetric: boolean = false) => {
  console.log('Updating relationship:', id, updates, 'symmetric:', updateSymmetric);
  const params = updateSymmetric ? { update_symmetric: true } : {};
  const response = await api.put(`/family/relationships/${id}`, updates, { params });
  console.log('Updated relationship:', response.data);
  return response.data;
};

export const deleteRelationship = async (id: string, deleteSymmetric: boolean = false) => {
  console.log('Deleting relationship:', id, 'symmetric:', deleteSymmetric);
  const params = deleteSymmetric ? { delete_symmetric: true } : {};
  const response = await api.delete(`/family/relationships/${id}`, { params });
  console.log('Deleted relationship:', response.data);
  return response.data;
};

export const getRingingEntryList = async (params?: {
  page?: number;
  per_page?: number;
  start_date?: string;
  end_date?: string;
  species?: string;
  place?: string;
  ring?: string;
  ringer?: string;
}) => {
  console.log('Fetching ringing entry list with params:', params);
  try {
    const response = await api.get<Ringing[]>('/ringings/entry-list', { params });
    console.log('Received ringing entry list:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error in getRingingEntryList:', error);
    if (axios.isAxiosError(error)) {
      console.error('Axios error details:', {
        response: error.response,
        request: error.request,
        message: error.message
      });
    }
    throw error;
  }
};