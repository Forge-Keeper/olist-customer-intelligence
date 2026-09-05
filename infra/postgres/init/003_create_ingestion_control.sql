CREATE TABLE IF NOT EXISTS platform.ingestion_control (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_file TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    row_count BIGINT NOT NULL,
    status TEXT NOT NULL,
    CONSTRAINT ingestion_control_file_hash_uk UNIQUE (file_hash),
    CONSTRAINT ingestion_control_status_ck CHECK (status IN ('SUCCESS', 'FAILED'))
);
