-- ============================================================
-- Ingest: move data from staging → final table
-- ============================================================

INSERT INTO document_chunks (
    uuid,
    file_name,
    chunk_index,
    chunk_text,
    chunk_page_no,
    chunk_method,
    chunk_size,
    chunk_overlap,
    emb_mdl_name,
    emb_mdl_dim,
    embedding
)
SELECT
    uuid,
    file_name,
    chunk_index,
    chunk_text,
    chunk_page_no,
    chunk_method,
    chunk_size,
    chunk_overlap,
    emb_mdl_name,
    emb_mdl_dim,
    emb_vector::vector(1024)
FROM document_chunks_stage;

-- Optional: clear staging after successful ingest
-- TRUNCATE TABLE document_chunks_stage;
