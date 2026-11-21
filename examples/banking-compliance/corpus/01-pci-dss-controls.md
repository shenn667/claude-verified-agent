<!-- SYNTHETIC: toutes les donnees sont fictives / all data is fictional. Banque Exemple SA / Example Bank SA. No real enterprise data. -->
# PCI DSS controls / Contrôles PCI DSS

Banque Exemple SA / Example Bank SA — synthetic control catalogue.
This document is a fictional training fixture, not a real policy.

## Chiffrement / Encryption

Selon la politique PCI DSS, la fréquence de rotation des clés de
chiffrement est strictement encadrée pour tout titulaire de compte.
Les clés de chiffrement doivent faire l'objet d'une rotation tous les 90 jours.
Encryption keys must be rotated every 90 days.
The PCI DSS rotation policy applies to every data-encryption key.

- AES-256 encryption at rest for all stored cardholder data.
- Chiffrement AES-256 au repos pour toutes les données stockées.
- TLS 1.2 or higher in transit; TLS 1.2 ou supérieur en transit.
- No protocol older than TLS 1.2 is permitted on any channel.

## Masquage du PAN / PAN masking

The full PAN is never rendered, never logged, never exported.
Le PAN complet n'est jamais affiché, journalisé ni exporté.
- Only the first six and last four digits of a PAN may be displayed.
- Seuls les six premiers et quatre derniers chiffres du PAN sont affichés.
- The CVV code is never stored after authorization, in any form.
- Le code CVV n'est jamais conservé après autorisation.

## Gestion des clés / Key management

- Keys live in a hardware security module (HSM), never on disk in clear.
- Les clés résident dans un module matériel de sécurité (HSM).
- Key rotation is automated and audited; the rotation rule is mandatory.
- La rotation des clés est automatisée et auditée tous les 90 jours.
- Split knowledge and dual control govern every key ceremony.

## Journalisation / Logging

- Every key-management action is logged with a tamper-evident trail.
- Chaque action de gestion des clés est journalisée de façon infalsifiable.
- Access to cardholder data is restricted to authorized roles only.
- L'accès aux données de titulaires de carte est limité aux rôles autorisés.

This synthetic catalogue illustrates PCI DSS themes for offline demos.
Il ne s'agit pas d'un texte réglementaire réel / not actual regulatory text.
