<template>
  <v-container class="legal-page">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card class="legal-card">
          <v-card-title class="legal-title">
            <v-icon icon="mdi-information" class="me-2"></v-icon>
            Impressum
          </v-card-title>
          <v-card-text class="legal-content">
            <section class="mb-6">
              <h3>Angaben gemäß § 5 TMG</h3>
              <div class="contact-info">
                <p><strong>Anton Rösler</strong></p>
                <p>Rossäckerstr. 43</p>
                <p>74189 Weinsberg</p>
                <p>Deutschland</p>
              </div>
            </section>

            <section class="mb-6">
              <h3>Kontakt</h3>
              <div class="contact-info">
                <p><strong>E-Mail:</strong> <a href="mailto:anton@antonroesler.com">anton@antonroesler.com</a></p>
              </div>
            </section>

            <section class="mb-6">
              <h3>Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV</h3>
              <div class="contact-info">
                <p>Anton Rösler</p>
                <p>Rossäckerstr. 43</p>
                <p>74189 Weinsberg</p>
              </div>
            </section>

            <section class="mb-6">
              <h3>Haftung für Inhalte</h3>
              <p>
                Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den 
                allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht 
                unter der Verpflichtung, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach 
                Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.
              </p>
              <p>
                Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen 
                Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt 
                der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden 
                Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.
              </p>
            </section>

            <section class="mb-6">
              <h3>Haftung für Links</h3>
              <p>
                Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. 
                Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der 
                verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.
              </p>
              <p>
                Die verlinkten Seiten wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße überprüft. 
                Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar. Eine permanente inhaltliche 
                Kontrolle der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht 
                zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.
              </p>
            </section>

            <section>
              <h3>Urheberrecht</h3>
              <p>
                Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen 
                Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der 
                Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers.
              </p>
              <p>
                Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet. 
                Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte 
                Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Sollten Sie trotzdem 
                auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei 
                Bekanntwerden von Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.
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

.legal-content p {
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.87);
}

.contact-info {
  background: rgba(0, 67, 108, 0.02);
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid #228096;
}

.contact-info p {
  margin-bottom: 8px;
}

.contact-info p:last-child {
  margin-bottom: 0;
}

.contact-info a {
  color: #228096;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.contact-info a:hover {
  color: #00436C;
  text-decoration: underline;
}

section {
  margin-bottom: 32px;
}

section:last-child {
  margin-bottom: 0;
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
}
</style>