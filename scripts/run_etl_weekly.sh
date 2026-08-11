#!/bin/bash
# Lance le pipeline ETL complet (scraping + météo) — destiné à être appelé par cron.
# Usage manuel : ./scripts/run_etl_weekly.sh
# Logs : data/external/etl_weekly.log

PROJECT_DIR="/Users/leogallus/Projets/AssuML"
LOG_FILE="$PROJECT_DIR/data/external/etl_weekly.log"

cd "$PROJECT_DIR" || exit 1

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') — Début ETL hebdomadaire ====="
  "$PROJECT_DIR/.venv/bin/python3" -m data_pipeline.extract.scraper
  "$PROJECT_DIR/.venv/bin/python3" -m data_pipeline.extract.api_extractor
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') — Fin ETL hebdomadaire ====="
} >> "$LOG_FILE" 2>&1
