<template>
  <AuthLayout>
    <div class="auth-header">
      <div class="auth-logo">
        <v-icon icon="mdi-account-circle" size="48" class="logo-icon"></v-icon>
      </div>
      <h1 class="auth-title">Anmelden</h1>
      <p class="auth-subtitle">Willkommen zurück</p>
    </div>
            
            <v-card-text class="auth-form">
              <v-form @submit.prevent="handleLogin" ref="form" autocomplete="on">
                <v-text-field
                  v-model="username"
                  label="Benutzername"
                  name="username"
                  prepend-inner-icon="mdi-account"
                  type="text"
                  :rules="[rules.required]"
                  required
                  variant="outlined"
                  class="auth-input"
                  autocomplete="username"
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
                  autocomplete="current-password"
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
  </AuthLayout>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import AuthLayout from "@/components/layout/AuthLayout.vue";

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
/* No additional styles needed - all handled by AuthLayout */
</style>
