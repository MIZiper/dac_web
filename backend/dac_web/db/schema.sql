CREATE TABLE IF NOT EXISTS nodes (
    id UUID PRIMARY KEY DEFAULT uuidv7(), -- Require PostgreSQL 18+, for native uuid v7 support
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content JSONB DEFAULT '{}',
    creator_signature VARCHAR(20),
    valid BOOLEAN NOT NULL DEFAULT TRUE
);