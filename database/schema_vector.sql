-- 第二套 Neon：RAG 向量分块（document_id 逻辑关联 MD 库主键）
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS lol_knowledge_chunks (
    id SERIAL PRIMARY KEY,
    document_id INT NOT NULL,
    doc_title TEXT,
    chunk_index INT NOT NULL,
    chunk_content TEXT NOT NULL,
    chunk_embedding vector(512),
    create_time TIMESTAMP DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON lol_knowledge_chunks(document_id);
