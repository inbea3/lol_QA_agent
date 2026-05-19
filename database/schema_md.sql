-- 第一套 Neon：纯 Markdown 原文
CREATE TABLE IF NOT EXISTS lol_knowledge_documents (
    id SERIAL PRIMARY KEY,
    doc_title TEXT NOT NULL,
    doc_source TEXT,
    markdown_content TEXT NOT NULL,
    is_vectorized SMALLINT NOT NULL DEFAULT 0 CHECK (is_vectorized IN (0, 1)),
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

-- 兼容旧表（无 is_vectorized 列时自动补齐）
ALTER TABLE lol_knowledge_documents
    ADD COLUMN IF NOT EXISTS is_vectorized SMALLINT NOT NULL DEFAULT 0;

ALTER TABLE lol_knowledge_documents
    DROP CONSTRAINT IF EXISTS lol_knowledge_documents_is_vectorized_check;

ALTER TABLE lol_knowledge_documents
    ADD CONSTRAINT lol_knowledge_documents_is_vectorized_check
    CHECK (is_vectorized IN (0, 1));
