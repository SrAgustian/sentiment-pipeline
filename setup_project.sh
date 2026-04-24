#!/bin/bash
# ============================================================
# setup_project.sh — Buat struktur folder proyek & init Git
# Jalankan sekali dari WSL2:  bash setup_project.sh
# ============================================================

PROJECT_NAME="sentiment-pipeline"

echo "📁  Membuat struktur folder proyek: $PROJECT_NAME/"
mkdir -p $PROJECT_NAME/{dags,scripts,data/{raw,processed},models,notebooks}

# Salin file konfigurasi yang sudah ada
cp docker-compose.yaml   $PROJECT_NAME/
cp .env.example          $PROJECT_NAME/
cp requirements.txt      $PROJECT_NAME/
cp scripts/init_db.sql   $PROJECT_NAME/scripts/
cp scripts/test_db_connection.py $PROJECT_NAME/scripts/

# Placeholder files agar folder tidak kosong di Git
touch $PROJECT_NAME/dags/.gitkeep
touch $PROJECT_NAME/data/raw/.gitkeep
touch $PROJECT_NAME/data/processed/.gitkeep
touch $PROJECT_NAME/models/.gitkeep
touch $PROJECT_NAME/notebooks/.gitkeep

# ── .gitignore ──────────────────────────────────────────────
cat > $PROJECT_NAME/.gitignore << 'EOF'
# Kredensial — JANGAN PERNAH di-commit!
.env

# Data & model (besar, simpan di cloud storage)
data/raw/*.csv
data/processed/*.csv
models/*.pkl

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.env/

# Jupyter
.ipynb_checkpoints/

# Docker volumes
logs/

# OS
.DS_Store
Thumbs.db
EOF

echo "✅  .gitignore dibuat"

# ── README.md ───────────────────────────────────────────────
cat > $PROJECT_NAME/README.md << 'EOF'
# Sentiment Pipeline — Analisis Sentimen Google Play Store

Pipeline otomatis berbasis Apache Airflow untuk scraping, preprocessing,
dan klasifikasi sentimen ulasan aplikasi e-commerce di Google Play Store.

## Struktur Proyek
```
sentiment-pipeline/
├── dags/           # DAG Airflow
├── scripts/        # Skrip Python & SQL
├── data/
│   ├── raw/        # Data mentah hasil scraping (.csv)
│   └── processed/  # Data setelah preprocessing
├── models/         # Model ML (.pkl) & vectorizer
├── notebooks/      # Eksplorasi & analisis
├── docker-compose.yaml
├── requirements.txt
└── .env.example
```

## Cara Mulai
1. Copy `.env.example` → `.env` dan isi semua nilai
2. `docker compose up -d`
3. Buka Airflow UI: http://localhost:8080
EOF

echo "✅  README.md dibuat"

# ── Init Git ────────────────────────────────────────────────
cd $PROJECT_NAME
git init
git add .
git commit -m "chore: initial project structure — Fase 1"

echo ""
echo "✅  Struktur proyek selesai!"
echo ""
echo "📂  Isi folder:"
find . -not -path './.git/*' | sort | head -40
echo ""
echo "👉  Langkah selanjutnya:"
echo "    1. cp .env.example .env"
echo "    2. Edit .env — isi semua nilai kredensial"
echo "    3. docker compose up airflow-init"
echo "    4. docker compose up -d"
