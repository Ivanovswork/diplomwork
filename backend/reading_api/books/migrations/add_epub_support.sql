-- SQL Migration for EPUB support
-- Run this if Django migration cannot be applied automatically

-- Add format column with default 'pdf'
ALTER TABLE books_book ADD COLUMN format VARCHAR(10) DEFAULT 'pdf';

-- Add extracted_text column (nullable)
ALTER TABLE books_book ADD COLUMN extracted_text TEXT;

-- Update existing books to have format='pdf'
UPDATE books_book SET format = 'pdf' WHERE format IS NULL;
