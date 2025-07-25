<template>
  <AuthLayout>
    <div class="auth-header">
      <div class="auth-logo">
        <v-icon icon="mdi-bird" size="48" class="logo-icon"></v-icon>
      </div>
      <h1 class="auth-title">Konto erstellen</h1>
      <p class="auth-subtitle">Registrieren Sie sich bei Vogelring</p>
    </div>
            
            <v-card-text class="auth-form">
              <v-form @submit.prevent="handleRegister" ref="form" autocomplete="on">
                <v-text-field
                  v-model="username"
                  label="Benutzername"
                  name="username"
                  prepend-inner-icon="mdi-account"
                  type="text"
                  :rules="[rules.required, rules.minLength]"
                  required
                  variant="outlined"
                  class="auth-input"
                  autocomplete="username"
                />

                <v-text-field
                  v-model="email"
                  label="E-Mail-Adresse"
                  name="email"
                  prepend-inner-icon="mdi-email"
                  type="email"
                  :rules="[rules.required, rules.email]"
                  required
                  variant="outlined"
                  class="auth-input"
                  autocomplete="email"
                />

                <v-text-field
                  v-model="password"
                  label="Passwort"
                  name="password"
                  prepend-inner-icon="mdi-lock"
                  :type="showPassword ? 'text' : 'password'"
                  :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click:append-inner="showPassword = !showPassword"
                  :rules="[rules.required, rules.passwordStrength]"
                  required
                  variant="outlined"
                  class="auth-input"
                  autocomplete="new-password"
                />

                <v-text-field
                  v-model="confirmPassword"
                  label="Passwort bestätigen"
                  name="confirmPassword"
                  prepend-inner-icon="mdi-lock-check"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  :append-inner-icon="showConfirmPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click:append-inner="showConfirmPassword = !showConfirmPassword"
                  :rules="[rules.required, rules.passwordMatch]"
                  required
                  variant="outlined"
                  class="auth-input"
                  autocomplete="new-password"
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
                @click="handleRegister"
                :disabled="!isFormValid"
                size="large"
                block
                class="auth-submit-btn"
                variant="elevated"
              >
                Registrieren
              </v-btn>
            </v-card-actions>
            
            <v-card-text class="auth-footer">
              <p class="text-center">
                Bereits ein Konto?
                <router-link to="/auth/login" class="auth-link">
                  Anmelden
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
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const successMessage = ref("");

const rules = {
  required: (value: string) => !!value || "Dieses Feld ist erforderlich",
  minLength: (value: string) =>
    value.length >= 3 || "Mindestens 3 Zeichen erforderlich",
  email: (value: string) => {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return pattern.test(value) || "Ungültige E-Mail-Adresse";
  },
  passwordStrength: (value: string) => {
    if (value.length < 8) return "Passwort muss mindestens 8 Zeichen lang sein";
    if (!/[A-Z]/.test(value))
      return "Passwort muss mindestens einen Großbuchstaben enthalten";
    if (!/[a-z]/.test(value))
      return "Passwort muss mindestens einen Kleinbuchstaben enthalten";
    if (!/[0-9]/.test(value))
      return "Passwort muss mindestens eine Zahl enthalten";
    return true;
  },
  passwordMatch: (value: string) =>
    value === password.value || "Passwörter stimmen nicht überein",
};

const isFormValid = computed(() => {
  return (
    username.value &&
    email.value &&
    password.value &&
    confirmPassword.value &&
    password.value === confirmPassword.value
  );
});

const handleRegister = async () => {
  if (!form.value.validate()) {
    return;
  }

  try {
    await authStore.signUp(username.value, password.value, email.value);
    successMessage.value =
      "Registrierung erfolgreich! Bitte überprüfen Sie Ihre E-Mails für den Bestätigungscode.";

    // Redirect to confirmation page after 2 seconds
    setTimeout(() => {
      router.push({
        path: "/auth/confirm",
        query: { username: username.value },
      });
    }, 2000);
  } catch (error) {
    console.error("Registration failed:", error);
    // Error is already handled in the store and displayed in the template
  }
};
</script>

<style scoped>
/* No additional styles needed - all handled by AuthLayout */
</style>
