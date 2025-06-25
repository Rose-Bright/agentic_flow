-- Migration: Add checkpoint tables for LangGraph state persistence
-- Version: 002
-- Created: 2024

-- Table for storing conversation checkpoints
CREATE TABLE IF NOT EXISTS conversation_checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(255) NOT NULL UNIQUE,
    checkpoint_data TEXT NOT NULL,
    custom_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversation_checkpoints_thread_id 
ON conversation_checkpoints(thread_id);

CREATE INDEX IF NOT EXISTS idx_conversation_checkpoints_created_at 
ON conversation_checkpoints(created_at);

-- Table for storing conversation writes/operations
CREATE TABLE IF NOT EXISTS conversation_writes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255) NOT NULL,
    writes_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for conversation writes
CREATE INDEX IF NOT EXISTS idx_conversation_writes_thread_id 
ON conversation_writes(thread_id);

CREATE INDEX IF NOT EXISTS idx_conversation_writes_task_id 
ON conversation_writes(task_id);

CREATE INDEX IF NOT EXISTS idx_conversation_writes_created_at 
ON conversation_writes(created_at);

-- Table for storing conversation metrics and analytics
CREATE TABLE IF NOT EXISTS conversation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4),
    metric_data JSONB DEFAULT '{}',
    agent_type VARCHAR(100),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for conversation metrics
CREATE INDEX IF NOT EXISTS idx_conversation_metrics_conversation_id 
ON conversation_metrics(conversation_id);

CREATE INDEX IF NOT EXISTS idx_conversation_metrics_type 
ON conversation_metrics(metric_type);

CREATE INDEX IF NOT EXISTS idx_conversation_metrics_agent_type 
ON conversation_metrics(agent_type);

CREATE INDEX IF NOT EXISTS idx_conversation_metrics_recorded_at 
ON conversation_metrics(recorded_at);

-- Table for agent performance tracking
CREATE TABLE IF NOT EXISTS agent_performance_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type VARCHAR(100) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    performance_data JSONB NOT NULL,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for agent performance log
CREATE INDEX IF NOT EXISTS idx_agent_performance_log_agent_type 
ON agent_performance_log(agent_type);

CREATE INDEX IF NOT EXISTS idx_agent_performance_log_conversation_id 
ON agent_performance_log(conversation_id);

CREATE INDEX IF NOT EXISTS idx_agent_performance_log_timestamp 
ON agent_performance_log(timestamp);

CREATE INDEX IF NOT EXISTS idx_agent_performance_log_success 
ON agent_performance_log(success);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_conversation_checkpoints_updated_at 
    BEFORE UPDATE ON conversation_checkpoints 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints and defaults
ALTER TABLE conversation_checkpoints 
ADD CONSTRAINT chk_thread_id_not_empty 
CHECK (thread_id != '');

ALTER TABLE conversation_writes 
ADD CONSTRAINT chk_writes_thread_id_not_empty 
CHECK (thread_id != '');

ALTER TABLE conversation_writes 
ADD CONSTRAINT chk_writes_task_id_not_empty 
CHECK (task_id != '');

-- Add retention policy function (to be called by cron job)
CREATE OR REPLACE FUNCTION cleanup_old_conversation_data(retention_days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    cutoff_date := NOW() - INTERVAL '1 day' * retention_days;
    
    -- Delete old checkpoints
    DELETE FROM conversation_checkpoints WHERE created_at < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete old writes
    DELETE FROM conversation_writes WHERE created_at < cutoff_date;
    
    -- Delete old metrics (keep for longer period)
    DELETE FROM conversation_metrics WHERE recorded_at < (cutoff_date - INTERVAL '60 days');
    
    -- Delete old performance logs
    DELETE FROM agent_performance_log WHERE timestamp < cutoff_date;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
