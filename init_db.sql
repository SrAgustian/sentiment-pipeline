-- ============================================================
-- init_db.sql — Inisialisasi tabel pipeline sentimen
-- Dijalankan otomatis saat container PostgreSQL pertama kali start
-- ============================================================

-- Tabel: ulasan mentah hasil scraping
CREATE TABLE IF NOT EXISTS raw_reviews (
    id          SERIAL PRIMARY KEY,
    app_name    VARCHAR(100)  NOT NULL,
    review_text TEXT          NOT NULL,
    rating      SMALLINT      CHECK (rating BETWEEN 1 AND 5),
    review_date DATE,
    scraped_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (app_name, review_text, review_date)
);

-- Tabel: ulasan setelah preprocessing
CREATE TABLE IF NOT EXISTS processed_reviews (
    id              SERIAL PRIMARY KEY,
    raw_id          INTEGER REFERENCES raw_reviews(id) ON DELETE CASCADE,
    cleaned_text    TEXT,
    tokens          TEXT,            -- disimpan sebagai JSON string
    processed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel: hasil prediksi sentimen
CREATE TABLE IF NOT EXISTS sentiment_results (
    id              SERIAL PRIMARY KEY,
    raw_id          INTEGER REFERENCES raw_reviews(id) ON DELETE CASCADE,
    app_name        VARCHAR(100),
    sentiment_label VARCHAR(20) CHECK (sentiment_label IN ('Positif','Negatif','Netral')),
    confidence      FLOAT,
    predicted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel: log monitoring pipeline Airflow
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id              SERIAL PRIMARY KEY,
    dag_id          VARCHAR(200),
    task_id         VARCHAR(200),
    run_id          VARCHAR(200),
    status          VARCHAR(20)  CHECK (status IN ('success','failed','skipped')),
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    duration_sec    FLOAT,
    rows_processed  INTEGER,
    notes           TEXT
);

-- Indeks untuk query dashboard
CREATE INDEX IF NOT EXISTS idx_sentiment_app  ON sentiment_results(app_name);
CREATE INDEX IF NOT EXISTS idx_sentiment_date ON sentiment_results(predicted_at);
CREATE INDEX IF NOT EXISTS idx_raw_app        ON raw_reviews(app_name);
