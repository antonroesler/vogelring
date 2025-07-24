<template>
  <v-container class="fill-height auth-container" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <div class="auth-card-wrapper">
          <v-card class="auth-card">
            <div class="auth-header">
              <div class="auth-logo">
                <v-icon icon="mdi-account-circle" size="48" class="logo-icon"></v-icon>
              </div>
              <h1 class="auth-title">Anmelden</h1>
              <p class="auth-subtitle">Willkommen zurück</p>
            </div>
            
            <v-card-text class="auth-form">
              <v-form @submit.prevent="handleLogin" ref="form">
                <v-text-field
                  v-model="username"
                  label="Benutzername oder E-Mail"
                  name="username"
                  prepend-inner-icon="mdi-account"
                  type="text"
                  :rules="[rules.required]"
                  required
                  variant="outlined"
                  class="auth-input"
                />

                <v-text-field
                  v-model="password"
                  :label="passwordLabel"
                  name="password"
                  prepend-inner-icon="mdi-lock"
                  :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  :type="showPassword ? 'text' : 'password'"
                  :rules="[rules.required]"
                  required
                  @click:append-inner="showPassword = !showPassword"
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
              </v-form>
            </v-card-text>
            
            <v-card-actions class="auth-actions">
              <v-btn
                color="primary"
                :loading="authStore.loading"
                @click="handleLogin"
                :disabled="!isFormValid"
                size="large"
                block
                class="auth-submit-btn"
                variant="elevated"
              >
                Anmelden
              </v-btn>
            </v-card-actions>
            
            <v-divider class="auth-divider"></v-divider>
            
            <v-card-text class="auth-footer">
              <p class="text-center">
                Noch kein Konto? 
                <router-link to="/auth/register" class="auth-link">
                  Registrieren
                </router-link>
              </p>
              <p class="text-center mt-2">
                <router-link to="/auth/forgot-password" class="auth-link">
                  Passwort vergessen?
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
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const form = ref();
const username = ref("");
const password = ref("");
const showPassword = ref(false);

const rules = {
  required: (value: string) => !!value || "Dieses Feld ist erforderlich",
};

const passwordLabel = computed(() => {
  return showPassword.value ? "Passwort" : "Passwort";
});

const isFormValid = computed(() => {
  return username.value && password.value;
});

const handleLogin = async () => {
  if (!form.value.validate()) {
    return;
  }

  try {
    await authStore.signIn(username.value, password.value);
    router.push("/");
  } catch (error) {
    console.error("Login failed:", error);
    // Error is already handled in the store and displayed in the template
  }
};
</script>

<style scoped>
.auth-container {
  min-height: 100vh;
  background: #ffffff;
  position: relative;
  overflow: hidden;
}

.auth-container::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 95%;
  height: 95%;
  background: url('/blackheadedgull.png') no-repeat center center;
  background-size: contain;
  opacity: 0.4;
  z-index: 0;
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
  
  .auth-actions {
    padding: 0 24px 24px !important;
  }
  
  .auth-footer {
    padding: 16px 24px 24px !important;
  }
  
  .auth-title {
    font-size: 1.75rem;
  }
}
</style>