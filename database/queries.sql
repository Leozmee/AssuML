-- ============================================================
-- AssuML — Requêtes SQL analytiques complexes
-- Compétences C4 (jointures) et C5 (agrégations, sous-requêtes)
-- Base : assuml_db | 1 338 clients, 4 régions
-- ============================================================


-- ── Requête 1 : Liste des clients avec leur nom de région ───────────────────
-- Jointure simple clients × regions — affiche les 10 premiers
-- Compétence C4 : INNER JOIN sur clé étrangère

SELECT
    c.client_id,
    c.age,
    c.sexe,
    c.imc,
    c.enfants,
    c.fumeur,
    r.nom_region
FROM clients c
INNER JOIN regions r ON c.region_id = r.region_id
WHERE c.date_suppression IS NULL
ORDER BY c.client_id
LIMIT 10;


-- ── Requête 2 : Nombre de clients actifs par région ────────────────────────
-- GROUP BY sur la clé étrangère + jointure pour afficher le nom de région
-- Compétence C5 : COUNT + GROUP BY

SELECT
    r.nom_region,
    COUNT(c.client_id) AS nb_clients
FROM regions r
LEFT JOIN clients c
    ON c.region_id = r.region_id
    AND c.date_suppression IS NULL
GROUP BY r.nom_region
ORDER BY nb_clients DESC;


-- ── Requête 3 : IMC moyen et âge moyen par région ─────────────────────────
-- Agrégations multiples par région
-- Compétence C5 : AVG + GROUP BY + ROUND

SELECT
    r.nom_region,
    ROUND(AVG(c.imc)::NUMERIC, 2)  AS imc_moyen,
    ROUND(AVG(c.age)::NUMERIC, 1)  AS age_moyen,
    MIN(c.age)                      AS age_min,
    MAX(c.age)                      AS age_max
FROM clients c
INNER JOIN regions r ON c.region_id = r.region_id
WHERE c.date_suppression IS NULL
GROUP BY r.nom_region
ORDER BY imc_moyen DESC;


-- ── Requête 4 : Régions avec plus de 100 clients fumeurs ───────────────────
-- Filtre sur un agrégat — les régions où les fumeurs sont nombreux
-- Compétence C5 : GROUP BY + HAVING

SELECT
    r.nom_region,
    COUNT(c.client_id) AS nb_fumeurs
FROM clients c
INNER JOIN regions r ON c.region_id = r.region_id
WHERE c.fumeur = TRUE
  AND c.date_suppression IS NULL
GROUP BY r.nom_region
HAVING COUNT(c.client_id) > 60
ORDER BY nb_fumeurs DESC;


-- ── Requête 5 : Coût médical prédit moyen par catégorie de risque ──────────
-- Jointure clients × predictions avec agrégation
-- Compétence C4 : INNER JOIN | Compétence C5 : AVG + GROUP BY

SELECT
    p.categorie_risque,
    COUNT(p.prediction_id)              AS nb_predictions,
    ROUND(AVG(p.cout_predit)::NUMERIC, 2) AS cout_moyen_predit,
    ROUND(AVG(p.prime)::NUMERIC, 2)      AS prime_moyenne
FROM predictions p
INNER JOIN clients c ON p.client_id = c.client_id
WHERE c.date_suppression IS NULL
GROUP BY p.categorie_risque
ORDER BY cout_moyen_predit DESC NULLS LAST;


-- ── Requête 6 : Clients sans aucune prédiction ─────────────────────────────
-- Détection des clients non encore scorés
-- Compétence C4 : LEFT JOIN avec IS NULL (anti-jointure)

SELECT
    c.client_id,
    c.age,
    c.sexe,
    r.nom_region
FROM clients c
INNER JOIN regions r ON c.region_id = r.region_id
LEFT JOIN predictions p ON p.client_id = c.client_id
WHERE p.prediction_id IS NULL
  AND c.date_suppression IS NULL
ORDER BY c.client_id
LIMIT 20;


-- ── Requête 7 : Top 5 clients par IMC avec leur région ─────────────────────
-- Sous-requête avec RANK() pour classer les clients
-- Compétence C5 : sous-requête + fonction de fenêtre RANK()

SELECT
    classement.client_id,
    classement.age,
    classement.sexe,
    classement.imc,
    classement.rang,
    r.nom_region
FROM (
    SELECT
        client_id,
        age,
        sexe,
        imc,
        region_id,
        RANK() OVER (ORDER BY imc DESC) AS rang
    FROM clients
    WHERE date_suppression IS NULL
) AS classement
INNER JOIN regions r ON classement.region_id = r.region_id
WHERE classement.rang <= 5
ORDER BY classement.rang;


-- ── Requête 8 : Répartition fumeurs / non-fumeurs par région (%) ───────────
-- Calcul de pourcentage avec GROUP BY multi-colonnes
-- Compétence C5 : GROUP BY + calcul de ratio + CASE

SELECT
    r.nom_region,
    SUM(CASE WHEN c.fumeur THEN 1 ELSE 0 END)     AS nb_fumeurs,
    SUM(CASE WHEN NOT c.fumeur THEN 1 ELSE 0 END) AS nb_non_fumeurs,
    COUNT(c.client_id)                             AS total,
    ROUND(
        100.0 * SUM(CASE WHEN c.fumeur THEN 1 ELSE 0 END)
        / NULLIF(COUNT(c.client_id), 0),
        1
    ) AS pct_fumeurs
FROM clients c
INNER JOIN regions r ON c.region_id = r.region_id
WHERE c.date_suppression IS NULL
GROUP BY r.nom_region
ORDER BY pct_fumeurs DESC;


-- ── Requête 9 : Clients avec contrats actifs — 3 tables jointes ────────────
-- Jointure clients × regions × contrats
-- Compétence C4 : jointure multi-tables (3 tables)

SELECT
    c.client_id,
    c.age,
    c.sexe,
    r.nom_region,
    co.contrat_id,
    co.type_couverture,
    co.prime_mensuelle,
    co.date_debut
FROM clients c
INNER JOIN regions r  ON c.region_id  = r.region_id
INNER JOIN contrats co ON co.client_id = c.client_id
WHERE co.statut = 'actif'
  AND c.date_suppression IS NULL
ORDER BY co.prime_mensuelle DESC
LIMIT 15;


-- ── Requête 10 : Tableau de bord par région — multi-agrégations ───────────
-- Vue synthétique complète : 2 tables, 6 métriques
-- Compétence C4 : JOIN | Compétence C5 : agrégations multiples

SELECT
    r.nom_region,
    COUNT(c.client_id)                                           AS nb_clients,
    ROUND(AVG(c.age)::NUMERIC, 1)                               AS age_moyen,
    ROUND(AVG(c.imc)::NUMERIC, 2)                               AS imc_moyen,
    ROUND(
        100.0 * SUM(CASE WHEN c.fumeur THEN 1 ELSE 0 END)
        / NULLIF(COUNT(c.client_id), 0), 1
    )                                                           AS pct_fumeurs,
    ROUND(AVG(c.enfants)::NUMERIC, 2)                           AS enfants_moyen,
    COUNT(DISTINCT p.prediction_id)                              AS nb_predictions
FROM regions r
LEFT JOIN clients c     ON c.region_id  = r.region_id AND c.date_suppression IS NULL
LEFT JOIN predictions p ON p.client_id  = c.client_id
GROUP BY r.nom_region
ORDER BY nb_clients DESC;
