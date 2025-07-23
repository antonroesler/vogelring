<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Vogelring Registrierung</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleRegister" ref="form">
              <v-text-field
                v-model="username"
                label="Benutzername"
                name="username"
                prepend-icon="mdi-account"
                type="text"
                :rules="[rules.required, rules.minLength]"
                required
              />

              <v-text-field
                v-model="email"
                label="E-Mail-Adresse"
                name="email"
                prepend-icon="mdi-email"
                type="email"
                :rules="[rules.required, rules.email]"
                required
              />

              <v-text-field
                v-model="password"
                label="Passwort"
                name="password"
                prepend-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append="showPassword = !showPassword"
                :rules="[rules.required, rules.passwordStrength]"
                required
              />

              <v-text-field
                v-model="confirmPassword"
                label="Passwort bestätigen"
                name="confirmPassword"
                prepend-icon="mdi-lock-check"
                :type="showConfirmPassword ? 'text' : 'password'"
                :append-icon="showConfirmPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append="showConfirmPassword = !showConfirmPassword"
                :rules="[rules.required, rules.passwordMatch]"
                required
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

              <v-alert v-if="successMessage" type="success" class="mb-4">
                {{ successMessage }}
              </v-alert>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              :loading="authStore.loading"
              @click="handleRegister"
              :disabled="!isFormValid"
            >
              Registrieren
            </v-btn>
          </v-card-actions>
          <v-divider />
          <v-card-text class="text-center">
            <p>
              Bereits ein Konto?
              <router-link to="/auth/login" class="text-decoration-none">
                Anmelden
              </router-link>
            </p>
          </v-card-text>
        </v-card>
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
.fill-height {
  min-height: 100vh;
}
</style>
