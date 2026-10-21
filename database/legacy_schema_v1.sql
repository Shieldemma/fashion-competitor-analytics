-- database/schema.sql
-- How to run this:
-- 1. Open pgAdmin (installed with PostgreSQL)
-- 2. Create a new database called "fashiondb"
-- 3. Open the Query Tool (right-click fashiondb → Query Tool)
-- 4. Paste this entire file and press F5 to run

-- Brands reference table
CREATE TABLE IF NOT EXISTS brands (
    id        SERIAL PRIMARY KEY,
    handle    VARCHAR(100) UNIQUE NOT NULL,
    name      VARCHAR(100),
    platform  VARCHAR(50),
    followers INTEGER
);

-- Posts table (main data table)
CREATE TABLE IF NOT EXISTS posts (
    id               SERIAL PRIMARY KEY,
    brand_handle     VARCHAR(100) REFERENCES brands(handle),
    platform         VARCHAR(50),
    post_url         TEXT UNIQUE,
    caption          TEXT,
    likes            INTEGER DEFAULT 0,
    comments         INTEGER DEFAULT 0,
    shares           INTEGER DEFAULT 0,
    engagement_rate  DECIMAL(8,4),
    intent_tier      VARCHAR(50),
    has_intent       BOOLEAN DEFAULT FALSE,
    post_date        TIMESTAMP,
    post_hour        INTEGER,
    post_day         VARCHAR(20),
    scraped_at       TIMESTAMP DEFAULT NOW()
);

-- Seed the brands table with our 5 competitors
INSERT INTO brands (handle, name, platform, followers) VALUES
    ('veekeejames_official', 'Veekee James', 'instagram', 2000000),
    ('ashluxe',              'Ashluxe',      'instagram', 150000),
    ('wflsncrm',             'WAF Lagos',    'instagram', 25000),
    ('zivalagos',            'Ziva Lagos',   'instagram', 80000),
    ('yomicasual',           'Yomi Casual',  'instagram', 500000)
ON CONFLICT (handle) DO NOTHING;

-- Verify setup
SELECT * FROM brands;
