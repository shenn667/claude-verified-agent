<!-- SYNTHETIC: toutes les donnees sont fictives / all data is fictional. Banque Exemple SA / Example Bank SA. No real enterprise data. -->
# SecOps incident playbook / Playbook d'incident SecOps

Banque Exemple SA / Example Bank SA — synthetic ransomware playbook.
Fictional fixture for offline demos; not a real incident procedure.
Document fictif illustrant des thèmes de réponse à incident.

## Confinement ransomware / Ransomware containment

- Isolate the affected VLAN immediately to stop lateral spread.
- Isoler immédiatement le VLAN touché pour stopper la propagation latérale.
- Block east-west traffic between segments at the firewall.
- Bloquer le trafic est-ouest entre segments au niveau du pare-feu.
- Keep north-south egress closed until the scope is understood.
- Garder la sortie nord-sud fermée tant que le périmètre n'est pas connu.

## Préservation forensic / Forensic preservation

- Preserve a forensic image of every affected host before any rebuild.
- Préserver une image forensic de chaque hôte touché avant toute reconstruction.
- Capture memory and disk artifacts before powering systems down.
- Capturer les artefacts mémoire et disque avant l'extinction des systèmes.
- Chain of custody is documented for each preserved image.
- La chaîne de custody est documentée pour chaque image préservée.

## Escalade / Escalation

- Escalate to the RSSI / CISO within 1 hour of confirmed impact.
- Escalader au RSSI / CISO dans l'heure suivant l'impact confirmé.
- Notify the regulator within 72 hours (synthetic deadline).
- Notifier le régulateur sous 72 heures (échéance synthétique).
- The notification clock starts at first confirmed compromise.
- Le délai de notification court dès la première compromission confirmée.

## Rançon / Ransom

- Never pay a ransom from compromised systems or accounts.
- Ne jamais payer de rançon depuis des systèmes ou comptes compromis.
- Payment decisions are out of scope for this synthetic playbook.
- Les décisions de paiement sortent du périmètre de ce playbook synthétique.

## Reprise / Recovery

- Rebuild only from known-good images after forensic preservation.
- Reconstruire uniquement depuis des images saines après préservation forensic.
- Validate integrity before returning any segment to production.
- Valider l'intégrité avant de remettre un segment en production.

This synthetic playbook illustrates SecOps themes for offline demos only.
Playbook fictif à des fins de démonstration hors ligne uniquement.
