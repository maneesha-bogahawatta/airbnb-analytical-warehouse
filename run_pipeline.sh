#!/bin/bash
# Exit immediately if any command fails
set -e

echo "🐳 Starting End-to-End Analytics Warehouse Pipeline..."
python3 src/build_db.py
python3 src/generate_charts.py
echo "🎉 Pipeline finished successfully! Figures are updated in reports/figures/."