<template>
    <v-container class="fill-height auth-container" fluid>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="4">
          <div class="auth-card-wrapper">
            <v-card class="auth-card">
              <div class="auth-header">
                <div class="auth-logo">
                  <v-icon icon="mdi-email-check" size="48" class="logo-icon"></v-icon>
                </div>
                <h1 class="auth-title">E-Mail bestätigen</h1>
                <p class="auth-subtitle">Geben Sie den Bestätigungscode ein</p>
              </div>
              
              <v-card-text class="auth-form">
                <v-alert type="info" class="mb-4 auth-alert" variant="tonal">
                  Bitte geben Sie den Bestätigungscode ein, den Sie per E-Mail erhalten haben.
                </v-alert>
    
                <v-form @submit.prevent="handleConfirm" ref="form">
                  <v-text-field
                    v-model="username"
                    label="Benutzername"
                    name="username"
                    prepend-inner-icon="mdi-account"
                    type="text"
                    :rules="[rules.required]"
                    required
                    :readonly="usernameFromQuery"
                    variant="outlined"
                    class="auth-input"
                  />
    
                  <v-text-field
                    v-model="confirmationCode"
                    label="Bestätigungscode"
                    name="confirmationCode"
                    prepend-inner-icon="mdi-lock"
                    type="text"
                    :rules="[rules.required, rules.codeLength]"
                    required
                    hint="6-stelliger Code aus der E-Mail"
                    persistent-hint
                    variant="outlined"
                    class="auth-input"
                  />
    
                  <v-alert
                    v-if="authStore.error"
                    type="error"
                    dismissible
                    @input="authStore.clearError"
                    class="mb-4 auth-alert"
                    variant="tonal"
                  >
                    {{ authStore.error }}
                  </v-alert>
    
                  <v-alert
                    v-if="successMessage"
                    type="success"
                    class="mb-4 auth-alert"
                    variant="tonal"
                  >
                    {{ successMessage }}
                  </v-alert>
                </v-form>
              </v-card-text>
              
              <v-card-actions class="auth-actions">
                <v-btn
                  color="primary"
                  :loading="authStore.loading"
                  @click="handleConfirm"
                  :disabled="!isFormValid"
                  size="large"
                  block
                  class="auth-submit-btn"
                  variant="elevated"
                >
                  Bestätigen
                </v-btn>
              </v-card-actions>
              
              <v-card-actions class="auth-secondary-actions">
                <v-btn
                  variant="text"
                  @click="resendCode"
                  :disabled="authStore.loading || resendDisabled"
                  :loading="resendLoading"
                  class="auth-secondary-btn"
                  block
                >
                  Code erneut senden
                  <span v-if="resendCountdown > 0"> ({{ resendCountdown }}s)</span>
                </v-btn>
              </v-card-actions>
              
              <v-divider class="auth-divider"></v-divider>
              
              <v-card-text class="auth-footer">
                <p class="text-center">
                  <router-link to="/auth/login" class="auth-link">
                    Zur Anmeldung
                  </router-link>
                </p>
              </v-card-text>
            </v-card>
          </div>
        </v-col>
      </v-row>
    </v-container>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted } from "vue";
  import { useRouter, useRoute } from "vue-router";
  import { useAuthStore } from "@/stores/auth";
  import { CognitoUser } from "amazon-cognito-identity-js";
  
  const router = useRouter();
  const route = useRoute();
  const authStore = useAuthStore();
  
  const form = ref();
  const username = ref("");
  const confirmationCode = ref("");
  const successMessage = ref("");
  const resendLoading = ref(false);
  const resendDisabled = ref(false);
  const resendCountdown = ref(0);
  const usernameFromQuery = ref(false);
  
  const rules = {
    required: (value: string) => !!value || "Dieses Feld ist erforderlich",
    codeLength: (value: string) => value.length === 6 || "Code muss 6 Zeichen lang sein",
  };
  
  const isFormValid = computed(() => {
    return username.value && confirmationCode.value && confirmationCode.value.length === 6;
  });
  
  onMounted(() => {
    // Pre-fill username if passed from registration
    if (route.query.username) {
      username.value = route.query.username as string;
      usernameFromQuery.value = true;
    }
  });
  
  const handleConfirm = async () => {
    if (!form.value.validate()) {
      return;
    }
  
    try {
      await authStore.confirmSignUp(username.value, confirmationCode.value);
      successMessage.value = "E-Mail erfolgreich bestätigt! Sie werden zur Anmeldung weitergeleitet...";
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push("/auth/login");
      }, 2000);
    } catch (error) {
      console.error("Confirmation failed:", error);
      // Error is already handled in the store and displayed in the template
    }
  };
  
  const resendCode = async () => {
    if (!username.value || resendDisabled.value) return;
  
    resendLoading.value = true;
    
    try {
      // Create a CognitoUser instance to resend the confirmation code
      const { CognitoUserPool } = await import("amazon-cognito-identity-js");
      
      const userPoolConfig = {
        UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || "eu-central-1_JIkm6sAqv",
        ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || "75k76q6tlvv01cm3glpo0crtn4",
      };
      
      const userPool = new CognitoUserPool(userPoolConfig);
      const cognitoUser = new CognitoUser({
        Username: username.value,
        Pool: userPool,
      });
  
      await new Promise<void>((resolve, reject) => {
        cognitoUser.resendConfirmationCode((err, result) => {
          if (err) {
            reject(err);
            return;
          }
          resolve();
        });
      });
  
      // Start countdown timer
      resendDisabled.value = true;
      resendCountdown.value = 60;
      
      const timer = setInterval(() => {
        resendCountdown.value--;
        if (resendCountdown.value <= 0) {
          clearInterval(timer);
          resendDisabled.value = false;
        }
      }, 1000);
  
      // Show success message
      successMessage.value = "Bestätigungscode wurde erneut gesendet!";
      setTimeout(() => {
        successMessage.value = "";
      }, 3000);
  
    } catch (error: any) {
      console.error("Resend failed:", error);
      authStore.error = error.message || "Fehler beim erneuten Senden des Codes";
    } finally {
      resendLoading.value = false;
    }
  };
  </script>
  
  <style scoped>
  .auth-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    position: relative;
  }
  
  .auth-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/><circle cx="10" cy="60" r="0.5" fill="white" opacity="0.1"/><circle cx="90" cy="40" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    pointer-events: none;
  }
  
  .auth-card-wrapper {
    position: relative;
    z-index: 1;
  }
  
  .auth-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1) !important;
    overflow: hidden;
    transition: all 0.3s ease;
  }
  
  .auth-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 24px 48px rgba(0, 0, 0, 0.15), 0 12px 24px rgba(0, 0, 0, 0.1) !important;
  }
  
  .auth-header {
    text-align: center;
    padding: 48px 32px 24px;
    background: linear-gradient(135deg, rgba(0, 67, 108, 0.05) 0%, rgba(34, 128, 150, 0.05) 100%);
  }
  
  .auth-logo {
    margin-bottom: 24px;
  }
  
  .logo-icon {
    color: #00436C;
    filter: drop-shadow(0 2px 4px rgba(0, 67, 108, 0.2));
  }
  
  .auth-title {
    font-size: 2rem;
    font-weight: 600;
    color: #00436C;
    margin-bottom: 8px;
    letter-spacing: -0.025em;
  }
  
  .auth-subtitle {
    color: #228096;
    font-size: 1rem;
    margin: 0;
    opacity: 0.8;
  }
  
  .auth-form {
    padding: 32px !important;
  }
  
  .auth-input {
    margin-bottom: 16px;
  }
  
  .auth-input :deep(.v-field) {
    border-radius: 12px;
    transition: all 0.3s ease;
  }
  
  .auth-input :deep(.v-field:hover) {
    box-shadow: 0 4px 12px rgba(0, 67, 108, 0.1);
  }
  
  .auth-input :deep(.v-field--focused) {
    box-shadow: 0 4px 16px rgba(0, 67, 108, 0.2);
  }
  
  .auth-alert {
    border-radius: 12px;
  }
  
  .auth-actions {
    padding: 0 32px 16px !important;
  }
  
  .auth-secondary-actions {
    padding: 0 32px 32px !important;
  }
  
  .auth-submit-btn {
    border-radius: 12px !important;
    height: 48px !important;
    font-weight: 600 !important;
    text-transform: none !important;
    letter-spacing: 0.025em !important;
    background: linear-gradient(135deg, #00436C 0%, #228096 100%) !important;
    box-shadow: 0 4px 16px rgba(0, 67, 108, 0.3) !important;
    transition: all 0.3s ease !important;
  }
  
  .auth-submit-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(0, 67, 108, 0.4) !important;
  }
  
  .auth-submit-btn:active {
    transform: translateY(0);
  }
  
  .auth-secondary-btn {
    border-radius: 12px !important;
    height: 40px !important;
    text-transform: none !important;
    color: #228096 !important;
    transition: all 0.3s ease !important;
  }
  
  .auth-secondary-btn:hover {
    background: rgba(34, 128, 150, 0.1) !important;
  }
  
  .auth-divider {
    margin: 0 32px;
    opacity: 0.2;
  }
  
  .auth-footer {
    padding: 24px 32px 32px !important;
    text-align: center;
  }
  
  .auth-link {
    color: #00436C;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.2s ease;
    position: relative;
  }
  
  .auth-link::after {
    content: '';
    position: absolute;
    bottom: -2px;
    left: 0;
    width: 0;
    height: 2px;
    background: linear-gradient(135deg, #00436C 0%, #228096 100%);
    transition: width 0.3s ease;
  }
  
  .auth-link:hover::after {
    width: 100%;
  }
  
  .auth-link:hover {
    color: #228096;
  }
  
  /* Responsive adjustments */
  @media (max-width: 600px) {
    .auth-header {
      padding: 32px 24px 16px;
    }
    
    .auth-form {
      padding: 24px !important;
    }
    
    .auth-actions, .auth-secondary-actions {
      padding-left: 24px !important;
      padding-right: 24px !important;
    }
    
    .auth-footer {
      padding: 16px 24px 24px !important;
    }
    
    .auth-title {
      font-size: 1.75rem;
    }
  }
  </style>

            <v-card-text>
              <v-alert type="info" class="mb-4">
                Bitte geben Sie den Bestätigungscode ein, den Sie per E-Mail erhalten haben.
              </v-alert>
  
              <v-form @submit.prevent="handleConfirm" ref="form">
                <v-text-field
                  v-model="username"
                  label="Benutzername"
                  name="username"
                  prepend-icon="mdi-account"
                  type="text"
                  :rules="[rules.required]"
                  required
                  :readonly="usernameFromQuery"
                />
  
                <v-text-field
                  v-model="confirmationCode"
                  label="Bestätigungscode"
                  name="confirmationCode"
                  prepend-icon="mdi-lock"
                  type="text"
                  :rules="[rules.required, rules.codeLength]"
                  required
                  hint="6-stelliger Code aus der E-Mail"
                  persistent-hint
                />
  
                <v-alert
                  v-if="authStore.error"
                  type="error"
                  dismissible
                  @input="authStore.clearError"
                  class="mb-4"
                >
                  {{ authStore.error }}
                </v-alert>
  
                <v-alert
                  v-if="successMessage"
                  type="success"
                  class="mb-4"
                >
                  {{ successMessage }}
                </v-alert>
              </v-form>
            </v-card-text>
            <v-card-actions>
              <v-btn
                text
                @click="resendCode"
                :disabled="authStore.loading || resendDisabled"
                :loading="resendLoading"
              >
                Code erneut senden
                <span v-if="resendCountdown > 0"> ({{ resendCountdown }}s)</span>
              </v-btn>
              <v-spacer />
              <v-btn
                color="primary"
                :loading="authStore.loading"
                @click="handleConfirm"
                :disabled="!isFormValid"
              >
                Bestätigen
              </v-btn>
            </v-card-actions>
            <v-divider />
            <v-card-text class="text-center">
              <p>
                <router-link to="/auth/login" class="text-decoration-none">
                  Zur Anmeldung
                </router-link>
              </p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted } from "vue";
  import { useRouter, useRoute } from "vue-router";
  import { useAuthStore } from "@/stores/auth";
  import { CognitoUser } from "amazon-cognito-identity-js";
  
  const router = useRouter();
  const route = useRoute();
  const authStore = useAuthStore();
  
  const form = ref();
  const username = ref("");
  const confirmationCode = ref("");
  const successMessage = ref("");
  const resendLoading = ref(false);
  const resendDisabled = ref(false);
  const resendCountdown = ref(0);
  const usernameFromQuery = ref(false);
  
  const rules = {
    required: (value: string) => !!value || "Dieses Feld ist erforderlich",
    codeLength: (value: string) => value.length === 6 || "Code muss 6 Zeichen lang sein",
  };
  
  const isFormValid = computed(() => {
    return username.value && confirmationCode.value && confirmationCode.value.length === 6;
  });
  
  onMounted(() => {
    // Pre-fill username if passed from registration
    if (route.query.username) {
      username.value = route.query.username as string;
      usernameFromQuery.value = true;
    }
  });
  
  const handleConfirm = async () => {
    if (!form.value.validate()) {
      return;
    }
  
    try {
      await authStore.confirmSignUp(username.value, confirmationCode.value);
      successMessage.value = "E-Mail erfolgreich bestätigt! Sie werden zur Anmeldung weitergeleitet...";
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push("/auth/login");
      }, 2000);
    } catch (error) {
      console.error("Confirmation failed:", error);
      // Error is already handled in the store and displayed in the template
    }
  };
  
  const resendCode = async () => {
    if (!username.value || resendDisabled.value) return;
  
    resendLoading.value = true;
    
    try {
      // Create a CognitoUser instance to resend the confirmation code
      const { CognitoUserPool } = await import("amazon-cognito-identity-js");
      
      const userPoolConfig = {
        UserPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || "eu-central-1_JIkm6sAqv",
        ClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || "75k76q6tlvv01cm3glpo0crtn4",
      };
      
      const userPool = new CognitoUserPool(userPoolConfig);
      const cognitoUser = new CognitoUser({
        Username: username.value,
        Pool: userPool,
      });
  
      await new Promise<void>((resolve, reject) => {
        cognitoUser.resendConfirmationCode((err, result) => {
          if (err) {
            reject(err);
            return;
          }
          resolve();
        });
      });
  
      // Start countdown timer
      resendDisabled.value = true;
      resendCountdown.value = 60;
      
      const timer = setInterval(() => {
        resendCountdown.value--;
        if (resendCountdown.value <= 0) {
          clearInterval(timer);
          resendDisabled.value = false;
        }
      }, 1000);
  
      // Show success message
      successMessage.value = "Bestätigungscode wurde erneut gesendet!";
      setTimeout(() => {
        successMessage.value = "";
      }, 3000);
  
    } catch (error: any) {
      console.error("Resend failed:", error);
      authStore.error = error.message || "Fehler beim erneuten Senden des Codes";
    } finally {
      resendLoading.value = false;
    }
  };
  </script>
  
  <style scoped>
  .fill-height {
    min-height: 100vh;
  }
  </style>