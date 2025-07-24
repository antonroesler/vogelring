<template>
  <v-container class="legal-page">
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card class="legal-card">
          <v-card-title class="legal-title">
            <v-icon icon="mdi-file-document" class="me-2"></v-icon>
            Allgemeine Geschäftsbedingungen (AGB)
          </v-card-title>
          <v-card-text class="legal-content">
            <section class="mb-6">
              <h3>§ 1 Geltungsbereich</h3>
              <p>
                Diese Allgemeinen Geschäftsbedingungen (nachfolgend „AGB") gelten für alle Leistungen, die über die 
                Website vogelring.com (nachfolgend „Website") angeboten werden. Betreiber der Website ist Anton Rösler 
                (nachfolgend „Anbieter").
              </p>
            </section>

            <section class="mb-6">
              <h3>§ 2 Vertragsschluss</h3>
              <p>
                Die Nutzung der Website ist grundsätzlich kostenlos. Durch die Registrierung auf der Website kommt 
                ein Nutzungsvertrag zwischen dem Nutzer und dem Anbieter zustande.
              </p>
              <p>
                Der Anbieter behält sich vor, die Registrierung ohne Angabe von Gründen abzulehnen.
              </p>
            </section>

            <section class="mb-6">
              <h3>§ 3 Leistungen des Anbieters</h3>
              <p>
                Der Anbieter stellt eine Plattform zur Verfügung, die es Nutzern ermöglicht, Vogelsichtungen zu 
                dokumentieren, zu verwalten und zu analysieren. Die Verfügbarkeit der Website wird nicht garantiert.
              </p>
              <p>
                Der Anbieter behält sich vor, die angebotenen Leistungen jederzeit zu ändern, zu erweitern oder 
                einzustellen.
              </p>
            </section>

            <section class="mb-6">
              <h3>§ 4 Pflichten des Nutzers</h3>
              <p>Der Nutzer verpflichtet sich:</p>
              <ul>
                <li>Wahrheitsgemäße Angaben bei der Registrierung zu machen</li>
                <li>Seine Zugangsdaten geheim zu halten und vor Missbrauch zu schützen</li>
                <li>Keine rechtswidrigen Inhalte zu veröffentlichen</li>
                <li>Die Rechte Dritter zu respektieren</li>
                <li>Die Website nicht für kommerzielle Zwecke zu nutzen, sofern nicht ausdrücklich gestattet</li>
              </ul>
            </section>

            <section class="mb-6">
              <h3>§ 5 Haftungsausschluss</h3>
              <p>
                Der Anbieter haftet nur für Schäden, die auf einer vorsätzlichen oder grob fahrlässigen 
                Pflichtverletzung beruhen. Die Haftung für leichte Fahrlässigkeit ist ausgeschlossen, soweit nicht 
                Schäden aus der Verletzung des Lebens, des Körpers oder der Gesundheit oder aus der Verletzung einer 
                wesentlichen Vertragspflicht resultieren.
              </p>
              <p>
                Der Anbieter übernimmt keine Gewähr für die Richtigkeit, Vollständigkeit oder Aktualität der auf der 
                Website bereitgestellten Informationen.
              </p>
            </section>

            <section class="mb-6">
              <h3>§ 6 Urheberrecht</h3>
              <p>
                Die vom Nutzer eingestellten Inhalte bleiben in seinem Eigentum. Der Nutzer räumt dem Anbieter jedoch 
                das Recht ein, diese Inhalte im Rahmen der Website zu nutzen, zu speichern und zu verarbeiten.
              </p>
              <p>
                Der Nutzer versichert, dass er über alle erforderlichen Rechte an den von ihm eingestellten Inhalten 
                verfügt.
              </p>
            </section>

            <section class="mb-6">
              <h3>§ 7 Datenschutz</h3>
              <p>
                Der Schutz personenbezogener Daten ist dem Anbieter wichtig. Die Verarbeitung personenbezogener Daten 
                erfolgt entsprechend den gesetzlichen Bestimmungen. Nähere Informationen finden Sie in der 
                Datenschutzerklärung.
              </p>
            </section>

            <section class="mb-6">
              <h3>§ 8 Kündigung</h3>
              <p>
                Sowohl der Nutzer als auch der Anbieter können den Nutzungsvertrag jederzeit ohne Einhaltung einer 
                Kündigungsfrist kündigen.
              </p>
              <p>
                Der Anbieter kann den Vertrag insbesondere kündigen, wenn der Nutzer gegen diese AGB verstößt.
              </p>
            </section>

            <section class="mb-6">
              <h3>§ 9 Änderungen der AGB</h3>
              <p>
                Der Anbieter behält sich vor, diese AGB jederzeit zu ändern. Die Änderungen werden dem Nutzer per 
                E-Mail mitgeteilt. Widerspricht der Nutzer nicht innerhalb von vier Wochen nach Zugang der Mitteilung, 
                gelten die Änderungen als genehmigt.
              </p>
            </section>

            <section>
              <h3>§ 10 Schlussbestimmungen</h3>
              <p>
                Es gilt deutsches Recht unter Ausschluss des UN-Kaufrechts. Gerichtsstand ist Frankfurt am Main, 
                sofern der Nutzer Kaufmann, juristische Person des öffentlichen Rechts oder öffentlich-rechtliches 
                Sondervermögen ist.
              </p>
              <p>
                Sollten einzelne Bestimmungen dieser AGB unwirksam sein oder werden, bleibt die Wirksamkeit der 
                übrigen Bestimmungen unberührt.
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
}
</style>