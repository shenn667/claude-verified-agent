<!-- SYNTHETIC: toutes les donnees sont fictives / all data is fictional. Banque Exemple SA / Example Bank SA. No real enterprise data. -->
# BCEAO-inspired audit logs / Journaux d'audit inspirés BCEAO

Banque Exemple SA / Example Bank SA — synthetic audit policy.
This is a synthetic policy inspired by public regulatory themes.
It is NOT actual regulatory text and carries no legal authority.
Il s'agit d'une politique synthétique inspirée de thèmes réglementaires
publics, et non d'un texte réglementaire réel.

## Rétention / Retention

- Audit logs are retained for 10 years in immutable storage.
- Les journaux d'audit sont conservés 10 ans en stockage immuable.
- Retention covers every privileged action across the estate.
- La rétention couvre chaque action privilégiée du système d'information.

## Intégrité WORM / WORM integrity

- Logs are written once and read many times (WORM), never altered.
- Les journaux sont écrits une fois, lus plusieurs fois (WORM), jamais modifiés.
- A cryptographic chain seals each batch so tampering is detectable.
- Une chaîne cryptographique scelle chaque lot pour détecter toute altération.

## Horodatage / Clock sync

- Every host synchronizes its clock over NTP to a trusted source.
- Chaque hôte synchronise son horloge via NTP sur une source de confiance.
- Consistent timestamps make cross-system traceability possible.
- Des horodatages cohérents rendent la traçabilité inter-systèmes possible.

## Traçabilité / Traceability

- Every privileged action is traced to a named, authenticated operator.
- Chaque action privilégiée est tracée vers un opérateur nommé et authentifié.
- Session start, elevation, and teardown are all recorded.
- Le début, l'élévation et la fin de session sont tous enregistrés.

## Séparation des tâches / Separation of duties

- Maker/checker: one operator proposes, a second approves.
- Maker/checker : un opérateur propose, un second approuve.
- No single person may both request and approve a privileged change.
- Nul ne peut à la fois demander et approuver un changement privilégié.

This synthetic fixture illustrates audit themes for offline demos only.
Document fictif à des fins de démonstration hors ligne uniquement.
