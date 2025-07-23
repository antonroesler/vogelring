<template>
    <v-container class="fill-height" fluid>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="4">
          <v-card class="elevation-12">
            <v-toolbar color="primary" dark flat>
              <v-toolbar-title>E-Mail Bestätigung</v-toolbar-title>
            </v-toolbar>
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