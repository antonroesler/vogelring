import { defineStore } from "pinia";
import { api } from "../api";

export interface User {
  id: string;
  email: string;
  display_name?: string;
  org_id: string;
  organization_name?: string;
  is_admin: boolean;
  is_active: boolean;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  userAttributes: Record<string, string> | null;
  loading: boolean;
  error: string | null;
}

// Auth store for multi-user support (authentication handled by Cloudflare Zero Trust in prod, dev mode in local)
export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    isAuthenticated: false,
    user: null,
    userAttributes: null,
    loading: false,
    error: null,
  }),

  getters: {
    userEmail: (state) => state.user?.email || null,
    displayName: (state) => state.user?.display_name || state.user?.email?.split('@')[0] || 'User',
    organizationName: (state) => state.user?.organization_name || 'Unknown Organization',
    isAdmin: (state) => state.user?.is_admin || false,
    isLoading: (state) => state.loading,
  },

  actions: {
    async fetchCurrentUser() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await api.get<User>('/auth/me');
        this.user = response.data;
        this.isAuthenticated = true;
      } catch (error: any) {
        console.error('Failed to fetch current user:', error);
        this.error = error.response?.data?.detail || 'Failed to authenticate';
        this.isAuthenticated = false;
        this.user = null;
      } finally {
        this.loading = false;
      }
    },

    async initialize() {
      await this.fetchCurrentUser();
    },

    clearError() {
      this.error = null;
    },

    logout() {
      this.isAuthenticated = false;
      this.user = null;
      this.userAttributes = null;
      this.error = null;
    },
  },
}); 