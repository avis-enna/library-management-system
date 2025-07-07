-- Library Management System Database Schema
-- Author: Venna Venkata Siva Reddy
-- Date: July 2025

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS fines CASCADE;
DROP TABLE IF EXISTS reservations CASCADE;
DROP TABLE IF EXISTS borrowings CASCADE;
DROP TABLE IF EXISTS book_authors CASCADE;
DROP TABLE IF EXISTS books CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS authors CASCADE;
DROP TABLE IF EXISTS members CASCADE;

-- Authors table
CREATE TABLE authors (
    author_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    birth_date DATE,
    nationality VARCHAR(50),
    biography TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(category_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Books table
CREATE TABLE books (
    book_id SERIAL PRIMARY KEY,
    isbn VARCHAR(13) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    subtitle VARCHAR(200),
    publication_year INTEGER CHECK (publication_year > 1000 AND publication_year <= EXTRACT(YEAR FROM CURRENT_DATE)),
    publisher VARCHAR(100),
    edition VARCHAR(50),
    pages INTEGER CHECK (pages > 0),
    language VARCHAR(50) DEFAULT 'English',
    total_copies INTEGER DEFAULT 1 CHECK (total_copies >= 0),
    available_copies INTEGER DEFAULT 1 CHECK (available_copies >= 0),
    category_id INTEGER REFERENCES categories(category_id),
    location VARCHAR(100), -- Shelf location
    price DECIMAL(10,2) CHECK (price >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_available_copies CHECK (available_copies <= total_copies)
);

-- Book_Authors junction table (many-to-many)
CREATE TABLE book_authors (
    book_id INTEGER REFERENCES books(book_id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES authors(author_id) ON DELETE CASCADE,
    author_role VARCHAR(50) DEFAULT 'Author', -- Author, Co-author, Editor, etc.
    PRIMARY KEY (book_id, author_id)
);

-- Members table
CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    member_type VARCHAR(20) CHECK (member_type IN ('student', 'faculty', 'staff', 'external')),
    member_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    address TEXT,
    date_of_birth DATE,
    registration_date DATE DEFAULT CURRENT_DATE,
    membership_expiry DATE NOT NULL,
    max_books_allowed INTEGER DEFAULT 3,
    current_books_count INTEGER DEFAULT 0,
    total_fine_amount DECIMAL(10,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_membership_expiry CHECK (membership_expiry >= registration_date)
);

-- Borrowings table
CREATE TABLE borrowings (
    borrowing_id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(member_id),
    book_id INTEGER REFERENCES books(book_id),
    borrowed_date DATE DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL,
    returned_date DATE,
    renewal_count INTEGER DEFAULT 0,
    fine_amount DECIMAL(10,2) DEFAULT 0.00,
    is_returned BOOLEAN DEFAULT FALSE,
    return_condition VARCHAR(100), -- Good, Damaged, Lost, etc.
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_due_date CHECK (due_date >= borrowed_date),
    CONSTRAINT check_return_date CHECK (returned_date IS NULL OR returned_date >= borrowed_date)
);

-- Reservations table
CREATE TABLE reservations (
    reservation_id SERIAL PRIMARY KEY,
    member_id INTEGER REFERENCES members(member_id),
    book_id INTEGER REFERENCES books(book_id),
    reservation_date DATE DEFAULT CURRENT_DATE,
    expiry_date DATE NOT NULL,
    is_fulfilled BOOLEAN DEFAULT FALSE,
    fulfilled_date DATE,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_reservation_expiry CHECK (expiry_date >= reservation_date),
    CONSTRAINT unique_active_reservation UNIQUE (member_id, book_id, is_fulfilled) 
        DEFERRABLE INITIALLY DEFERRED
);

-- Fines table
CREATE TABLE fines (
    fine_id SERIAL PRIMARY KEY,
    borrowing_id INTEGER REFERENCES borrowings(borrowing_id),
    member_id INTEGER REFERENCES members(member_id),
    fine_type VARCHAR(50) NOT NULL, -- Late return, Damage, Lost book, etc.
    fine_amount DECIMAL(10,2) NOT NULL CHECK (fine_amount >= 0),
    fine_reason TEXT,
    is_paid BOOLEAN DEFAULT FALSE,
    payment_date DATE,
    payment_method VARCHAR(50), -- Cash, Card, Online, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit table for tracking changes
CREATE TABLE audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance optimization
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_category ON books(category_id);
CREATE INDEX idx_books_available ON books(available_copies) WHERE available_copies > 0;

CREATE INDEX idx_members_email ON members(email);
CREATE INDEX idx_members_code ON members(member_code);
CREATE INDEX idx_members_type ON members(member_type);
CREATE INDEX idx_members_active ON members(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_borrowings_member ON borrowings(member_id);
CREATE INDEX idx_borrowings_book ON borrowings(book_id);
CREATE INDEX idx_borrowings_due_date ON borrowings(due_date) WHERE is_returned = FALSE;
CREATE INDEX idx_borrowings_overdue ON borrowings(due_date, is_returned) WHERE is_returned = FALSE;

CREATE INDEX idx_reservations_member ON reservations(member_id);
CREATE INDEX idx_reservations_book ON reservations(book_id);
CREATE INDEX idx_reservations_active ON reservations(is_fulfilled) WHERE is_fulfilled = FALSE;

CREATE INDEX idx_fines_member ON fines(member_id);
CREATE INDEX idx_fines_unpaid ON fines(is_paid) WHERE is_paid = FALSE;

-- Full-text search indexes
CREATE INDEX idx_books_search ON books USING gin(to_tsvector('english', title || ' ' || COALESCE(subtitle, '')));
CREATE INDEX idx_authors_search ON authors USING gin(to_tsvector('english', first_name || ' ' || last_name));

-- Comments for documentation
COMMENT ON TABLE books IS 'Stores information about all books in the library';
COMMENT ON TABLE members IS 'Stores information about library members';
COMMENT ON TABLE borrowings IS 'Tracks all book borrowing transactions';
COMMENT ON TABLE reservations IS 'Manages book reservations by members';
COMMENT ON TABLE fines IS 'Tracks fines imposed on members';

COMMENT ON COLUMN books.available_copies IS 'Number of copies currently available for borrowing';
COMMENT ON COLUMN members.max_books_allowed IS 'Maximum number of books a member can borrow simultaneously';
COMMENT ON COLUMN borrowings.renewal_count IS 'Number of times the borrowing has been renewed';
COMMENT ON COLUMN reservations.priority IS 'Priority level for reservation fulfillment';

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO library_admin;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO library_staff;
-- GRANT SELECT ON books, authors, categories TO library_user;
