import { defineStore } from "pinia";

export interface AuthState {
  isAuthenticated: boolean;
  user: null;
  userAttributes: Record<string, string> | null;
  loading: boolean;
  error: string | null;
}

// Simplified auth store for local deployment (authentication handled by Cloudflare Zero Trust)
export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    isAuthenticated: true, // Always authenticated since Cloudflare handles auth
    user: null,
    userAttributes: null,
    loading: false,
    error: null,
  }),

  actions: {
    // Minimal actions for private server deployment
    clearError() {
      this.error = null;
    },
  },
}); 