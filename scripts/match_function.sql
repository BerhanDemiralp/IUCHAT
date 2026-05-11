-- ============================================================
-- Similarity search RPC functions
-- ------------------------------------------------------------
-- 1) match_chunks          : pure vector / cosine semantic (legacy)
-- 2) match_chunks_hybrid   : hybrid (FTS + vector) with RRF
-- ============================================================

-- ------------------------------------------------------------
-- LEGACY: pure semantic similarity (kept for backwards compat)
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding VECTOR(1024),
    match_count     INT DEFAULT 5
)
RETURNS TABLE (
    file_name       TEXT,
    chunk_index     INTEGER,
    chunk_page_no   INTEGER,
    chunk_text      TEXT,
    score           REAL
)
LANGUAGE sql STABLE
AS $$
    SELECT
        dc.file_name,
        dc.chunk_index,
        dc.chunk_page_no,
        dc.chunk_text,
        1 - (dc.emb_vector <=> query_embedding) AS score
    FROM iuchat_emb dc
    ORDER BY dc.emb_vector <=> query_embedding ASC
    LIMIT match_count;
$$;


-- ============================================================
-- HYBRID SEARCH SETUP — run these once to enable FTS column
-- ============================================================

-- Generated tsvector column for Turkish full-text search.
-- The column is maintained automatically by Postgres on every insert/update.
ALTER TABLE iuchat_emb
    ADD COLUMN IF NOT EXISTS chunk_text_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('turkish', coalesce(chunk_text, ''))) STORED;

-- GIN index for fast FTS lookups
CREATE INDEX IF NOT EXISTS idx_iuchat_emb_chunk_text_tsv
    ON iuchat_emb
    USING GIN (chunk_text_tsv);


-- ------------------------------------------------------------
-- HYBRID: FTS (BM25-like) + vector similarity combined with
-- Reciprocal Rank Fusion (RRF).
--
-- Each candidate document is scored by:
--     score = 1 / (rrf_k + semantic_rank) + 1 / (rrf_k + keyword_rank)
--
-- RRF is the de-facto standard for fusing heterogeneous rankers
-- because it's robust to score-scale differences between systems.
--
-- We over-fetch `candidate_count` from each side, then merge and
-- return only the top `match_count` final results.
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION match_chunks_hybrid(
    query_text       TEXT,
    query_embedding  VECTOR(1024),
    match_count      INT DEFAULT 8,
    candidate_count  INT DEFAULT 30,
    rrf_k            INT DEFAULT 60
)
RETURNS TABLE (
    file_name       TEXT,
    chunk_index     INTEGER,
    chunk_page_no   INTEGER,
    chunk_text      TEXT,
    score           REAL
)
LANGUAGE sql STABLE
AS $$
    WITH
    -- Top-N candidates by vector similarity
    semantic AS (
        SELECT
            dc.id,
            ROW_NUMBER() OVER (
                ORDER BY dc.emb_vector <=> query_embedding ASC
            ) AS rnk
        FROM iuchat_emb dc
        ORDER BY dc.emb_vector <=> query_embedding ASC
        LIMIT candidate_count
    ),
    -- Top-N candidates by Turkish FTS. `websearch_to_tsquery` accepts a
    -- forgiving user-style syntax (quoted phrases, OR, -negation).
    keyword AS (
        SELECT
            dc.id,
            ROW_NUMBER() OVER (
                ORDER BY ts_rank_cd(dc.chunk_text_tsv,
                                    websearch_to_tsquery('turkish', query_text)) DESC
            ) AS rnk
        FROM iuchat_emb dc
        WHERE dc.chunk_text_tsv @@ websearch_to_tsquery('turkish', query_text)
          AND query_text IS NOT NULL
          AND length(trim(query_text)) > 0
        ORDER BY ts_rank_cd(dc.chunk_text_tsv,
                            websearch_to_tsquery('turkish', query_text)) DESC
        LIMIT candidate_count
    ),
    -- All unique candidate ids from either side
    all_ids AS (
        SELECT id FROM semantic
        UNION
        SELECT id FROM keyword
    ),
    -- Reciprocal Rank Fusion score
    combined AS (
        SELECT
            a.id,
            COALESCE(1.0 / (rrf_k + s.rnk), 0)
          + COALESCE(1.0 / (rrf_k + k.rnk), 0) AS rrf_score
        FROM all_ids a
        LEFT JOIN semantic s USING (id)
        LEFT JOIN keyword  k USING (id)
    )
    SELECT
        dc.file_name,
        dc.chunk_index,
        dc.chunk_page_no,
        dc.chunk_text,
        c.rrf_score::REAL AS score
    FROM combined c
    JOIN iuchat_emb dc USING (id)
    ORDER BY c.rrf_score DESC
    LIMIT match_count;
$$;
