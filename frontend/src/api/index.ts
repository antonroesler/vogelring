import axios from 'axios';
import type { Sighting, BirdMeta, FriendResponse, Dashboard, Ringing, ShareableReport, SuggestionBird } from '../types';

const API_BASE_URL = 'https://782syzefh4.execute-api.eu-central-1.amazonaws.com/Prod';
const API_KEY = import.meta.env.VITE_API_KEY;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'x-api-key': API_KEY,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  },
  timeout: 10000,
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

// Add response interceptor for logging
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