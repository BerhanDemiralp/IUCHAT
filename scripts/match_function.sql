-- ============================================================
-- Similarity search RPC function
-- ============================================================

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
        1 - (dc.embedding <=> query_embedding) AS score   -- cosine similarity
    FROM document_chunks dc
    ORDER BY dc.embedding <=> query_embedding ASC         -- closest first
    LIMIT match_count;
$$;
