-- ============================================================
-- RAG Retrieval System - Database Setup
-- ============================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Staging table (CSV lands here first, emb_vector stored as TEXT)
CREATE TABLE IF NOT EXISTS document_chunks_stage (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid            TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    chunk_page_no   INTEGER,
    chunk_method    TEXT,
    chunk_size      INTEGER,
    chunk_overlap   INTEGER,
    emb_mdl_name    TEXT,
    emb_mdl_dim     INTEGER,
    emb_vector      TEXT NOT NULL,           -- raw string from CSV e.g. "[0.12,0.45,...]"
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Final table (production-ready with VECTOR column)
--    Change VECTOR(5) to VECTOR(1024) when moving to production.
CREATE TABLE IF NOT EXISTS document_chunks (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid            TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    chunk_text      TEXT NOT NULL,
    chunk_page_no   INTEGER,
    chunk_method    TEXT,
    chunk_size      INTEGER,
    chunk_overlap   INTEGER,
    emb_mdl_name    TEXT,
    emb_mdl_dim     INTEGER,
    embedding       VECTOR(1024) NOT NULL,
    ingested_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 4. IVFFlat index for cosine similarity
--    Adjust 'lists' based on row count: lists = rows / 1000 (min 10)
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 129);  -- ~129K rows / 1000
