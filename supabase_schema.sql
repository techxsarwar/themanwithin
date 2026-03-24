-- Supabase PostgreSQL Schema for "The Man Within"
-- Run this in the Supabase SQL Editor to manually create tables if needed.

CREATE TABLE IF NOT EXISTS announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    content TEXT,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_announcements_title ON announcements(title);


CREATE TABLE IF NOT EXISTS seo_settings (
    id SERIAL PRIMARY KEY,
    page_name VARCHAR(255) UNIQUE,
    title VARCHAR(255),
    description TEXT
);
CREATE INDEX IF NOT EXISTS ix_seo_settings_page_name ON seo_settings(page_name);


CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    visit_count INTEGER DEFAULT 0
);


CREATE TABLE IF NOT EXISTS site_settings (
    id SERIAL PRIMARY KEY,
    youtube_url VARCHAR(255) DEFAULT '',
    instagram_url VARCHAR(255) DEFAULT '',
    github_url VARCHAR(255) DEFAULT ''
);


CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    rating INTEGER,
    text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    subject VARCHAR(255),
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
