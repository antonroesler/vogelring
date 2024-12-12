import axios from 'axios';
import type { Sighting, BirdMeta, FriendResponse, Dashboard } from '../types';

const API_BASE_URL = 'https://782syzefh4.execute-api.eu-central-1.amazonaws.com/Prod';
const API_KEY = import.meta.env.VITE_API_KEY;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'x-api-key': API_KEY
  }
});

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
  const response = await api.get<BirdMeta[]>(`/birds/suggestions/${partialReading}`);
  console.log('Received suggestions:', response.data);
  return response.data;
};

export const getBirdByRing = async (ring: string) => {
  console.log('Fetching bird with ring:', ring);
  const response = await api.get<BirdMeta>(`/birds/${ring}`);
  console.log('Received bird:', response.data);
  return response.data;
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