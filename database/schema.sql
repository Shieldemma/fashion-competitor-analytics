-- database/schema.sql
-- PostgreSQL DDL for the v2 warehouse, generated from fashion_intel/db.py:
--   python -m fashion_intel schema > database/schema.sql
-- You do not need to run this by hand: the pipeline creates missing tables (CREATE IF NOT EXISTS
-- semantics) and never drops or alters existing ones. The legacy v1 schema is in legacy_schema_v1.sql.

CREATE TABLE competitor_brands (
	brand_handle VARCHAR(100) NOT NULL, 
	display_name VARCHAR(200), 
	platform VARCHAR(30), 
	in_registry BOOLEAN NOT NULL, 
	follower_count_reference INTEGER, 
	follower_source TEXT, 
	follower_as_of VARCHAR(10), 
	PRIMARY KEY (brand_handle)
);

CREATE TABLE pipeline_runs (
	run_id VARCHAR(40) NOT NULL, 
	started_at_utc VARCHAR(40) NOT NULL, 
	finished_at_utc VARCHAR(40), 
	status VARCHAR(20) NOT NULL, 
	input_file TEXT, 
	input_sha256 VARCHAR(64), 
	posts_loaded INTEGER, 
	comments_loaded INTEGER, 
	audit_window_start_utc VARCHAR(40), 
	audit_window_end_utc VARCHAR(40), 
	code_version VARCHAR(20), 
	PRIMARY KEY (run_id)
);

CREATE TABLE social_posts (
	post_id VARCHAR(120) NOT NULL, 
	platform VARCHAR(30) NOT NULL, 
	brand_handle VARCHAR(100) NOT NULL, 
	owner_username VARCHAR(100), 
	is_collab BOOLEAN NOT NULL, 
	is_pinned BOOLEAN NOT NULL, 
	post_url TEXT NOT NULL, 
	shortcode VARCHAR(60), 
	post_type VARCHAR(30), 
	caption TEXT, 
	published_at_utc TIMESTAMP WITH TIME ZONE, 
	published_date_wat VARCHAR(10), 
	published_hour_wat INTEGER, 
	published_weekday_wat VARCHAR(10), 
	in_audit_window BOOLEAN NOT NULL, 
	likes INTEGER, 
	likes_hidden BOOLEAN NOT NULL, 
	comments_count INTEGER, 
	interactions INTEGER, 
	video_views INTEGER, 
	video_plays INTEGER, 
	likes_per_1k_followers FLOAT, 
	caption_shows_price BOOLEAN, 
	caption_call_to_action BOOLEAN, 
	caption_launch_or_restock BOOLEAN, 
	data_source VARCHAR(60) NOT NULL, 
	source_file TEXT NOT NULL, 
	source_sha256 VARCHAR(64) NOT NULL, 
	source_row INTEGER, 
	extracted_at_utc VARCHAR(40), 
	loaded_by_run_id VARCHAR(40), 
	PRIMARY KEY (post_id), 
	FOREIGN KEY(brand_handle) REFERENCES competitor_brands (brand_handle), 
	UNIQUE (post_url)
);

CREATE INDEX ix_posts_brand_date ON social_posts (brand_handle, published_date_wat);

CREATE INDEX ix_posts_platform ON social_posts (platform);

CREATE TABLE audience_comments (
	comment_id VARCHAR(160) NOT NULL, 
	post_id VARCHAR(120) NOT NULL, 
	brand_handle VARCHAR(100) NOT NULL, 
	parent_comment_id VARCHAR(160), 
	is_reply BOOLEAN NOT NULL, 
	commenter_id VARCHAR(40), 
	is_account_reply BOOLEAN NOT NULL, 
	is_audience BOOLEAN NOT NULL, 
	text TEXT, 
	published_at_utc TIMESTAMP WITH TIME ZONE, 
	published_date_wat VARCHAR(10), 
	comment_likes INTEGER, 
	intent_label VARCHAR(20) NOT NULL, 
	intent_signals TEXT, 
	intent_signal_count INTEGER NOT NULL, 
	intent_negated BOOLEAN NOT NULL, 
	affordability_barrier BOOLEAN NOT NULL, 
	post_purchase_feedback BOOLEAN NOT NULL, 
	sentiment_polarity FLOAT, 
	sentiment_label VARCHAR(10), 
	source_sha256 VARCHAR(64) NOT NULL, 
	loaded_by_run_id VARCHAR(40), 
	PRIMARY KEY (comment_id), 
	FOREIGN KEY(post_id) REFERENCES social_posts (post_id)
);

CREATE INDEX ix_comments_brand_intent ON audience_comments (brand_handle, intent_label);

CREATE INDEX ix_comments_post ON audience_comments (post_id);

