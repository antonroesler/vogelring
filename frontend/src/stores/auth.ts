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
    // Stub methods for backward compatibility
    async signUp(username: string, password: string, email: string) {
      console.warn('Authentication is handled by Cloudflare Zero Trust');
      return Promise.resolve();
    },

    async confirmSignUp(username: string, confirmationCode: string) {
      console.warn('Authentication is handled by Cloudflare Zero Trust');
      return Promise.resolve();
    },

    async signIn(username: string, password: string) {
      console.warn('Authentication is handled by Cloudflare Zero Trust');
      return Promise.resolve();
    },

    async signOut() {
      console.warn('Authentication is handled by Cloudflare Zero Trust');
      return Promise.resolve();
    },

    async getCurrentUser() {
      // Always return a mock user since auth is handled externally
      return Promise.resolve({ username: 'user' });
    },

    async getIdToken(): Promise<string | null> {
      // No token needed for local backend
      return Promise.resolve(null);
    },

    async refreshSession(): Promise<boolean> {
      // Always return true since auth is handled externally
      return Promise.resolve(true);
    },

    async loadUserAttributes() {
      // No user attributes needed
      return Promise.resolve();
    },

    clearError() {
      this.error = null;
    },
  },
}); 