import { defineStore } from "pinia";
import {
  CognitoUserPool,
  CognitoUser,
  AuthenticationDetails,
  CognitoUserAttribute,
  CognitoUserSession,
} from "amazon-cognito-identity-js";

export interface AuthState {
  isAuthenticated: boolean;
  user: CognitoUser | null;
  userAttributes: Record<string, string> | null;
  loading: boolean;
  error: string | null;
}

// Configuration for Cognito User Pool (will be set via environment variables)
const userPoolConfig = {
  UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || "eu-central-1_JIkm6sAqv",
  ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || "75k76q6tlvv01cm3glpo0crtn4",
};

const userPool = new CognitoUserPool(userPoolConfig);

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    isAuthenticated: false,
    user: null,
    userAttributes: null,
    loading: false,
    error: null,
  }),

  actions: {
    async signUp(username: string, password: string, email: string) {
      this.loading = true;
      this.error = null;

      return new Promise((resolve, reject) => {
        const attributeList = [
          new CognitoUserAttribute({
            Name: "email",
            Value: email,
          }),
        ];

        userPool.signUp(username, password, attributeList, [], (err, result) => {
          this.loading = false;
          if (err) {
            this.error = err.message;
            reject(err);
            return;
          }
          resolve(result);
        });
      });
    },

    async confirmSignUp(username: string, confirmationCode: string) {
      this.loading = true;
      this.error = null;

      return new Promise((resolve, reject) => {
        const cognitoUser = new CognitoUser({
          Username: username,
          Pool: userPool,
        });

        cognitoUser.confirmRegistration(confirmationCode, true, (err, result) => {
          this.loading = false;
          if (err) {
            this.error = err.message;
            reject(err);
            return;
          }
          resolve(result);
        });
      });
    },

    async signIn(username: string, password: string) {
      this.loading = true;
      this.error = null;

      return new Promise((resolve, reject) => {
        const authenticationDetails = new AuthenticationDetails({
          Username: username,
          Password: password,
        });

        const cognitoUser = new CognitoUser({
          Username: username,
          Pool: userPool,
        });

        cognitoUser.authenticateUser(authenticationDetails, {
          onSuccess: (result: CognitoUserSession) => {
            this.user = cognitoUser;
            this.isAuthenticated = true;
            this.loading = false;
            this.loadUserAttributes();
            resolve(result);
          },
          onFailure: (err) => {
            this.loading = false;
            this.error = err.message;
            reject(err);
          },
        });
      });
    },

    async signOut() {
      return new Promise<void>((resolve) => {
        if (this.user) {
          this.user.signOut(() => {
            this.user = null;
            this.userAttributes = null;
            this.isAuthenticated = false;
            resolve();
          });
        } else {
          this.user = null;
          this.userAttributes = null;
          this.isAuthenticated = false;
          resolve();
        }
      });
    },

    async getCurrentUser(): Promise<CognitoUser | null> {
      return new Promise((resolve) => {
        const cognitoUser = userPool.getCurrentUser();
        if (cognitoUser) {
          cognitoUser.getSession((err: any, session: CognitoUserSession | null) => {
            if (err || !session || !session.isValid()) {
              this.isAuthenticated = false;
              this.user = null;
              this.userAttributes = null;
              resolve(null);
              return;
            }
            this.user = cognitoUser;
            this.isAuthenticated = true;
            this.loadUserAttributes();
            resolve(cognitoUser);
          });
        } else {
          this.isAuthenticated = false;
          this.user = null;
          this.userAttributes = null;
          resolve(null);
        }
      });
    },

    async getIdToken(): Promise<string | null> {
      return new Promise((resolve) => {
        if (!this.user) {
          resolve(null);
          return;
        }

        this.user.getSession((err: any, session: CognitoUserSession | null) => {
          if (err || !session || !session.isValid()) {
            resolve(null);
            return;
          }
          resolve(session.getIdToken().getJwtToken());
        });
      });
    },

    async refreshSession(): Promise<boolean> {
      return new Promise((resolve) => {
        if (!this.user) {
          resolve(false);
          return;
        }

        this.user.getSession((err: any, session: CognitoUserSession | null) => {
          if (err || !session) {
            resolve(false);
            return;
          }

          if (session.isValid()) {
            resolve(true);
            return;
          }

          // Try to refresh the session
          const refreshToken = session.getRefreshToken();
          this.user!.refreshSession(refreshToken, (refreshErr, newSession) => {
            if (refreshErr || !newSession) {
              this.signOut();
              resolve(false);
              return;
            }
            resolve(true);
          });
        });
      });
    },

    async loadUserAttributes() {
      if (!this.user) return;

      return new Promise<void>((resolve) => {
        this.user!.getUserAttributes((err, attributes) => {
          if (err) {
            console.error("Error loading user attributes:", err);
            resolve();
            return;
          }

          if (attributes) {
            this.userAttributes = {};
            attributes.forEach((attr) => {
              this.userAttributes![attr.getName()] = attr.getValue();
            });
          }
          resolve();
        });
      });
    },

    clearError() {
      this.error = null;
    },
  },
}); 