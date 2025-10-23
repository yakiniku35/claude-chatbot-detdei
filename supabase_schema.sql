-- Supabase SQL Schema for Chat History
-- Run this in your Supabase SQL Editor to create the required table

CREATE TABLE IF NOT EXISTS chat_history (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster session lookups
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp);

-- Enable Row Level Security (RLS)
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

-- Create a policy that allows all operations for authenticated users
-- Adjust this based on your security requirements
CREATE POLICY "Enable all operations for authenticated users" ON chat_history
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Optional: Create a policy for anonymous users if you want to allow public access
CREATE POLICY "Enable read access for anonymous users" ON chat_history
    FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "Enable insert for anonymous users" ON chat_history
    FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "Enable delete for anonymous users" ON chat_history
    FOR DELETE
    TO anon
    USING (true);
