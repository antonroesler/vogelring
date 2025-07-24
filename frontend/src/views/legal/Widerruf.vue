<template>
  <v-container class="legal-page">
    <div class="back-button-container">
      <v-btn
        variant="text"
        color="primary"
        @click="$router.back()"
        class="back-btn"
      >
        <v-icon icon="mdi-arrow-left" class="me-2"></v-icon>
        Zurück
      </v-btn>
    </div>
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card class="legal-card">
          <v-card-title class="legal-title">
            <v-icon icon="mdi-undo" class="me-2"></v-icon>
            Widerrufsrecht
          </v-card-title>
          <v-card-text class="legal-content">
            <section class="mb-6">
              <h3>Widerrufsbelehrung</h3>
              <h4>Widerrufsrecht</h4>
              <p>
                Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen.
              </p>
              <p>
                Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsschlusses.
              </p>
              <p>
                Um Ihr Widerrufsrecht auszuüben, müssen Sie uns (Anton Rösler, Musterstraße 123, 60311 Frankfurt am Main, 
                E-Mail: anton@antonroesler.com) mittels einer eindeutigen Erklärung (z.B. ein mit der Post versandter 
                Brief oder E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren.
              </p>
            </section>

            <section class="mb-6">
              <h3>Widerrufsfolgen</h3>
              <p>
                Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, 
                einschließlich der Lieferkosten (mit Ausnahme der zusätzlichen Kosten, die sich daraus ergeben, dass 
                Sie eine andere Art der Lieferung als die von uns angebotene, günstigste Standardlieferung gewählt haben), 
                unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über 
                Ihren Widerruf dieses Vertrags bei uns eingegangen ist.
              </p>
              <p>
                Für diese Rückzahlung verwenden wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion 
                eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes vereinbart; in keinem Fall 
                werden Ihnen wegen dieser Rückzahlung Entgelte berechnet.
              </p>
            </section>

            <section class="mb-6">
              <h3>Muster-Widerrufsformular</h3>
              <div class="widerruf-form">
                <p><strong>Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular aus und senden Sie es zurück:</strong></p>
                
                <div class="form-content">
                  <p>An: Anton Rösler, Rossäckerstr. 43, 74189 Weinsberg, E-Mail: anton@antonroesler.com</p>
                  
                  <p>Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über die Erbringung der folgenden Dienstleistung (*)</p>
                  
                  <p>Bestellt am (*)/erhalten am (*)</p>
                  
                  <p>Name des/der Verbraucher(s)</p>
                  
                  <p>Anschrift des/der Verbraucher(s)</p>
                  
                  <p>Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf Papier)</p>
                  
                  <p>Datum</p>
                  
                  <p class="form-note">(*) Unzutreffendes streichen.</p>
                </div>
              </div>
            </section>

            <section>
              <h3>Besondere Hinweise</h3>
              <p>
                Das Widerrufsrecht besteht nicht bei Verträgen zur Erbringung von Dienstleistungen, wenn der Unternehmer 
                die Dienstleistung vollständig erbracht hat und mit der Ausführung der Dienstleistung erst begonnen hat, 
                nachdem der Verbraucher dazu seine ausdrückliche Zustimmung gegeben hat und gleichzeitig seine Kenntnis 
                davon bestätigt hat, dass er sein Widerrufsrecht bei vollständiger Vertragserfüllung durch den Unternehmer 
                verliert.
              </p>
            </section>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// No script needed for this static page
</script>

<style scoped>
.legal-page {
  padding: 32px 16px;
  min-height: calc(100vh - 200px);
}

.legal-card {
  border-radius: 16px !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
  border: 1px solid rgba(0, 67, 108, 0.1);
}

.legal-title {
  background: linear-gradient(135deg, rgba(0, 67, 108, 0.05) 0%, rgba(34, 128, 150, 0.05) 100%);
  color: #00436C;
  font-size: 1.5rem;
  font-weight: 600;
  padding: 24px 32px;
}

.legal-content {
  padding: 32px !important;
  line-height: 1.7;
}

.legal-content h3 {
  color: #00436C;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 16px;
  border-bottom: 2px solid #DED5CA;
  padding-bottom: 8px;
}

.legal-content h4 {
  color: #228096;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 20px 0 12px 0;
}

.legal-content p {
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.87);
}

.legal-content ul {
  margin-bottom: 16px;
  padding-left: 24px;
}

.legal-content li {
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.87);
}

.widerruf-form {
  background: rgba(0, 67, 108, 0.02);
  padding: 24px;
  border-radius: 8px;
  border: 1px solid rgba(0, 67, 108, 0.1);
}

.form-content {
  background: white;
  padding: 20px;
  border-radius: 4px;
  border: 1px solid #DED5CA;
  margin-top: 16px;
  font-family: monospace;
  font-size: 0.9rem;
  line-height: 2;
}

.form-content p {
  margin-bottom: 24px;
  color: rgba(0, 0, 0, 0.87);
}

.form-note {
  font-style: italic;
  color: rgba(0, 0, 0, 0.6) !important;
  font-size: 0.8rem !important;
}

.back-button-container {
  margin-bottom: 16px;
}

.back-btn {
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}

.back-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 67, 108, 0.2);
}

/* Responsive adjustments */
@media (max-width: 600px) {
  .legal-title {
    padding: 16px 20px;
    font-size: 1.3rem;
  }
  
  .legal-content {
    padding: 20px !important;
  }
  
  .legal-content h3 {
    font-size: 1.1rem;
  }
  
  .legal-content h4 {
    font-size: 1rem;
  }
  
  .widerruf-form {
    padding: 16px;
  }
  
  .form-content {
    padding: 16px;
    font-size: 0.8rem;
  }
}
</style>