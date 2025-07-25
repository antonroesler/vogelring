<template>
  <AuthLayout>
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
    
                <v-form @submit.prevent="handleConfirm" ref="form" autocomplete="on">
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
                    autocomplete="username"
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
                    autocomplete="one-time-code"
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
  </AuthLayout>
</template>
  
  <script setup lang="ts">
  import { ref, computed, onMounted } from "vue";
  import { useRouter, useRoute } from "vue-router";
  import { useAuthStore } from "@/stores/auth";
  import { CognitoUser } from "amazon-cognito-identity-js";
  import AuthLayout from "@/components/layout/AuthLayout.vue";
  
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
/* Specific styles for confirm signup page */
.auth-secondary-actions {
  padding: 0 32px 32px !important;
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

/* Responsive adjustments */
@media (max-width: 600px) {
  .auth-secondary-actions {
    padding-left: 24px !important;
    padding-right: 24px !important;
  }
}
</style>