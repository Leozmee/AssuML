# Accessibilité — AssuML / Actuavie

Ce document couvre la démarche d'accessibilité de l'application Django (`django_app/`), réalisée dans le cadre de la feature `015-accessibilite-wcag-rgaa` (compétences C14 et C17 du référentiel Simplon).

## Standard suivi

- **WCAG 2.1** niveau **AA**.
- Transposition nationale : **RGAA 4.1** (Référentiel Général d'Amélioration de l'Accessibilité).

## Mesures implémentées

1. Structure sémantique HTML5 (`header`, `nav`, `main`, `footer`) sur toutes les pages.
2. Lien d'évitement ("Aller au contenu principal") en tout début de page, visible au focus clavier uniquement.
3. Labels explicites associés à tous les champs de formulaire (`label` + `for`/`id`).
4. `aria-required` et légende visuelle ("* champ obligatoire") sur les champs obligatoires.
5. Messages d'erreur de validation liés au champ concerné (`aria-describedby` + `role="alert"`).
6. `aria-label` sur tous les boutons représentés par une icône seule (liste des clients, fiche client).
6bis. Icônes emoji strictement décoratives ou redondantes avec un texte adjacent masquées aux technologies d'assistance (`<span aria-hidden="true">`) — badges de décision, statuts de monitoring, libellés de carte.
7. `aria-live="polite"` sur les zones à mise à jour dynamique (IMC calculé, indicateurs de monitoring).
8. Contraste texte/fond ≥ 4.5:1 (niveau AA) sur les combinaisons vérifiées.
9. Navigation complète au clavier (Tab, Maj+Tab, Entrée), focus toujours visible.
10. Tableaux de données structurés (`caption`, `th scope="col"`).
11. Aucune information transmise uniquement par la couleur (badges toujours accompagnés d'un texte).
12. Attribut `lang="fr"` sur la page.

## Tests effectués

| Test | Méthode | Résultat |
|---|---|---|
| Structure sémantique (lang, landmarks, lien d'évitement) | Test automatisé (`tests/test_accessibility.py`, classe `TestStructureSemantique`) | ✅ Passé |
| Absence de règle `outline: none`/`outline: 0` globale | Test automatisé (`tests/test_accessibility.py`, classe `TestFocusOutline`) | ✅ Passé |
| Labels de formulaire (`label[for]`/`id`) | Test automatisé (`tests/test_accessibility.py`, classe `TestFormulaires`) | ✅ Passé |
| `aria-label` sur boutons icône (liste clients) | Test automatisé (`tests/test_accessibility.py`, classe `TestBoutonsIcones`) | ✅ Passé |
| Tableaux (`caption`, `th scope="col"`) | Test automatisé (`tests/test_accessibility.py`, classe `TestTableaux`) | ✅ Passé |
| `aria-live` monitoring et calculateur IMC | Test automatisé (`tests/test_accessibility.py`, classe `TestZonesDynamiques`) | ✅ Passé |
| Contraste texte/fond (`--muted`, `--primary`, badges risque/statut, `.btn-success`) | Calcul programmatique du ratio de contraste WCAG (luminance relative, script Python dédié) sur chaque paire couleur/fond réellement utilisée dans `assuml.css` | ✅ Toutes les paires vérifiées ≥ 4.5:1 (texte normal) ou ≥ 3:1 (texte large ≥ 18.66px gras) après correction de `--muted`, `--primary`, `--success`/`--warning`/`--danger`/`--orange` |
| Navigation clavier de bout en bout (connexion → scoring → soumission) | Test manuel (Tab/Maj+Tab/Entrée, sans souris) | ⏳ À réaliser — nécessite un navigateur réel, non disponible dans l'environnement d'exécution de cette implémentation |
| Contraste des couleurs avec un outil en ligne dédié (ex. WebAIM Contrast Checker) | Test manuel dans un navigateur | ⏳ À réaliser — substitué par la vérification programmatique ci-dessus (même formule de contraste WCAG que ces outils), à confirmer visuellement |
| Lecteur d'écran (VoiceOver, macOS) | Test manuel | ⏳ À réaliser — nécessite une session macOS avec VoiceOver actif, non disponible dans l'environnement d'exécution de cette implémentation |

42 tests automatisés passent dans `django_app/tests/` (dont 9 dédiés à l'accessibilité), sans régression sur les tests existants des features 013/014.

**Dernière vérification** (2026-08-16) : relecture indépendante de l'ensemble des 8 user stories sur le code réel de
`django_app/` (landmarks de `base.html`, liaison erreur/champ via `AccessibleFormMixin`, `aria-live` du monitoring,
absence d'`outline: none` dans `assuml.css`, structure des tableaux, `fieldset`/`legend`) — `manage.py check` clean,
`pytest tests/` 42/42, `flake8` clean. Deux corrections supplémentaires apportées à cette occasion : masquage
`aria-hidden` d'emoji décoratifs jusque-là non masqués (mesure 6bis ci-dessus), et mise à jour des couleurs de repli
obsolètes dans `static/js/charts.js`. Détail dans `specs/015-accessibilite-wcag-rgaa/tasks.md` (T024a, T031a).

## Limites connues

- Les graphiques Plotly.js (module Analytics) ne sont pas entièrement accessibles aux lecteurs d'écran (les éléments SVG générés dynamiquement ne portent pas d'alternative sémantique native). Une alternative textuelle (tableau de données `<table>` avec `caption`/`th scope="col"`, repliable via `<details>`, reprenant les mêmes valeurs que le graphique) est fournie sous chaque graphique du module Analytics.
- Chaque graphique Analytics utilise une seule série de couleur unie (pas d'encodage de plusieurs catégories par teinte au sein d'un même graphique) : le risque de confusion daltonienne entre catégories ne s'applique donc pas à ces graphiques.
- Les vérifications manuelles (navigation clavier réelle, lecteur d'écran, outil de contraste en ligne) n'ont pas pu être réalisées dans cet environnement d'implémentation (pas de navigateur ni de lecteur d'écran disponibles) ; elles restent à effectuer par un humain avant la certification finale, comme documenté ci-dessus.
