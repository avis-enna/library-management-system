-- Stored Procedures and Functions for Library Management System
-- Author: Venna Venkata Siva Reddy

-- Function to calculate fine amount based on days overdue
CREATE OR REPLACE FUNCTION calculate_overdue_fine(
    p_due_date DATE,
    p_return_date DATE DEFAULT CURRENT_DATE,
    p_daily_rate DECIMAL DEFAULT 1.00
) RETURNS DECIMAL AS $$
BEGIN
    IF p_return_date <= p_due_date THEN
        RETURN 0.00;
    ELSE
        RETURN (p_return_date - p_due_date) * p_daily_rate;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function to check if member can borrow more books
CREATE OR REPLACE FUNCTION can_member_borrow(p_member_id INTEGER) 
RETURNS BOOLEAN AS $$
DECLARE
    member_record RECORD;
    current_borrowed INTEGER;
BEGIN
    -- Get member information
    SELECT * INTO member_record 
    FROM members 
    WHERE member_id = p_member_id AND is_active = TRUE;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Check if membership is still valid
    IF member_record.membership_expiry < CURRENT_DATE THEN
        RETURN FALSE;
    END IF;
    
    -- Count current borrowed books
    SELECT COUNT(*) INTO current_borrowed
    FROM borrowings
    WHERE member_id = p_member_id AND is_returned = FALSE;
    
    -- Check if member has reached borrowing limit
    IF current_borrowed >= member_record.max_books_allowed THEN
        RETURN FALSE;
    END IF;
    
    -- Check if member has unpaid fines above threshold
    IF member_record.total_fine_amount > 50.00 THEN
        RETURN FALSE;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to issue a book to a member
CREATE OR REPLACE FUNCTION issue_book(
    p_member_id INTEGER,
    p_book_id INTEGER,
    p_loan_days INTEGER DEFAULT 14
) RETURNS BOOLEAN AS $$
DECLARE
    book_available INTEGER;
    can_borrow BOOLEAN;
BEGIN
    -- Check if book is available
    SELECT available_copies INTO book_available
    FROM books
    WHERE book_id = p_book_id AND is_active = TRUE;
    
    IF book_available IS NULL OR book_available <= 0 THEN
        RAISE EXCEPTION 'Book is not available for borrowing';
    END IF;
    
    -- Check if member can borrow
    SELECT can_member_borrow(p_member_id) INTO can_borrow;
    
    IF NOT can_borrow THEN
        RAISE EXCEPTION 'Member cannot borrow books at this time';
    END IF;
    
    -- Begin transaction
    BEGIN
        -- Insert borrowing record
        INSERT INTO borrowings (member_id, book_id, due_date)
        VALUES (p_member_id, p_book_id, CURRENT_DATE + p_loan_days);
        
        -- Update book availability
        UPDATE books
        SET available_copies = available_copies - 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE book_id = p_book_id;
        
        -- Update member's current book count
        UPDATE members
        SET current_books_count = current_books_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE member_id = p_member_id;
        
        -- Remove any reservation for this book by this member
        UPDATE reservations
        SET is_fulfilled = TRUE,
            fulfilled_date = CURRENT_DATE
        WHERE member_id = p_member_id 
        AND book_id = p_book_id 
        AND is_fulfilled = FALSE;
        
        RETURN TRUE;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE EXCEPTION 'Failed to issue book: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to return a book
CREATE OR REPLACE FUNCTION return_book(
    p_borrowing_id INTEGER,
    p_return_condition VARCHAR DEFAULT 'Good',
    p_notes TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    borrowing_record RECORD;
    fine_amount DECIMAL;
BEGIN
    -- Get borrowing record
    SELECT * INTO borrowing_record
    FROM borrowings
    WHERE borrowing_id = p_borrowing_id AND is_returned = FALSE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid borrowing record or book already returned';
    END IF;
    
    -- Calculate fine if overdue
    SELECT calculate_overdue_fine(borrowing_record.due_date) INTO fine_amount;
    
    BEGIN
        -- Update borrowing record
        UPDATE borrowings
        SET is_returned = TRUE,
            returned_date = CURRENT_DATE,
            return_condition = p_return_condition,
            fine_amount = fine_amount,
            notes = p_notes,
            updated_at = CURRENT_TIMESTAMP
        WHERE borrowing_id = p_borrowing_id;
        
        -- Update book availability
        UPDATE books
        SET available_copies = available_copies + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE book_id = borrowing_record.book_id;
        
        -- Update member's current book count
        UPDATE members
        SET current_books_count = current_books_count - 1,
            total_fine_amount = total_fine_amount + fine_amount,
            updated_at = CURRENT_TIMESTAMP
        WHERE member_id = borrowing_record.member_id;
        
        -- Insert fine record if applicable
        IF fine_amount > 0 THEN
            INSERT INTO fines (borrowing_id, member_id, fine_type, fine_amount, fine_reason)
            VALUES (p_borrowing_id, borrowing_record.member_id, 'Late Return', 
                   fine_amount, 'Overdue return fine');
        END IF;
        
        RETURN TRUE;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE EXCEPTION 'Failed to return book: %', SQLERRM;
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to renew a book borrowing
CREATE OR REPLACE FUNCTION renew_book(
    p_borrowing_id INTEGER,
    p_renewal_days INTEGER DEFAULT 14
) RETURNS BOOLEAN AS $$
DECLARE
    borrowing_record RECORD;
    max_renewals INTEGER := 2;
BEGIN
    -- Get borrowing record
    SELECT * INTO borrowing_record
    FROM borrowings
    WHERE borrowing_id = p_borrowing_id AND is_returned = FALSE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid borrowing record or book already returned';
    END IF;
    
    -- Check renewal limit
    IF borrowing_record.renewal_count >= max_renewals THEN
        RAISE EXCEPTION 'Maximum renewal limit reached';
    END IF;
    
    -- Check if book is reserved by someone else
    IF EXISTS (
        SELECT 1 FROM reservations 
        WHERE book_id = borrowing_record.book_id 
        AND member_id != borrowing_record.member_id 
        AND is_fulfilled = FALSE
    ) THEN
        RAISE EXCEPTION 'Book is reserved by another member';
    END IF;
    
    -- Renew the book
    UPDATE borrowings
    SET due_date = due_date + p_renewal_days,
        renewal_count = renewal_count + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE borrowing_id = p_borrowing_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to reserve a book
CREATE OR REPLACE FUNCTION reserve_book(
    p_member_id INTEGER,
    p_book_id INTEGER,
    p_reservation_days INTEGER DEFAULT 7
) RETURNS BOOLEAN AS $$
DECLARE
    book_available INTEGER;
    existing_reservation INTEGER;
BEGIN
    -- Check if book is currently available
    SELECT available_copies INTO book_available
    FROM books WHERE book_id = p_book_id;
    
    IF book_available > 0 THEN
        RAISE EXCEPTION 'Book is currently available, no need to reserve';
    END IF;
    
    -- Check if member already has a reservation for this book
    SELECT COUNT(*) INTO existing_reservation
    FROM reservations
    WHERE member_id = p_member_id 
    AND book_id = p_book_id 
    AND is_fulfilled = FALSE;
    
    IF existing_reservation > 0 THEN
        RAISE EXCEPTION 'Member already has a reservation for this book';
    END IF;
    
    -- Create reservation
    INSERT INTO reservations (member_id, book_id, expiry_date, priority)
    VALUES (p_member_id, p_book_id, CURRENT_DATE + p_reservation_days,
           (SELECT COALESCE(MAX(priority), 0) + 1 
            FROM reservations 
            WHERE book_id = p_book_id AND is_fulfilled = FALSE));
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to get member's borrowing history
CREATE OR REPLACE FUNCTION get_member_history(
    p_member_id INTEGER,
    p_limit INTEGER DEFAULT 50
) RETURNS TABLE (
    borrowing_id INTEGER,
    book_title VARCHAR,
    author_names TEXT,
    borrowed_date DATE,
    due_date DATE,
    returned_date DATE,
    fine_amount DECIMAL,
    is_returned BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.borrowing_id,
        bk.title,
        STRING_AGG(a.first_name || ' ' || a.last_name, ', ') as author_names,
        b.borrowed_date,
        b.due_date,
        b.returned_date,
        b.fine_amount,
        b.is_returned
    FROM borrowings b
    JOIN books bk ON b.book_id = bk.book_id
    LEFT JOIN book_authors ba ON bk.book_id = ba.book_id
    LEFT JOIN authors a ON ba.author_id = a.author_id
    WHERE b.member_id = p_member_id
    GROUP BY b.borrowing_id, bk.title, b.borrowed_date, b.due_date, 
             b.returned_date, b.fine_amount, b.is_returned
    ORDER BY b.borrowed_date DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to search books with full-text search
CREATE OR REPLACE FUNCTION search_books(
    p_search_term TEXT,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
) RETURNS TABLE (
    book_id INTEGER,
    title VARCHAR,
    subtitle VARCHAR,
    author_names TEXT,
    category_name VARCHAR,
    publication_year INTEGER,
    available_copies INTEGER,
    total_copies INTEGER,
    isbn VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        b.book_id,
        b.title,
        b.subtitle,
        STRING_AGG(a.first_name || ' ' || a.last_name, ', ') as author_names,
        c.category_name,
        b.publication_year,
        b.available_copies,
        b.total_copies,
        b.isbn
    FROM books b
    LEFT JOIN book_authors ba ON b.book_id = ba.book_id
    LEFT JOIN authors a ON ba.author_id = a.author_id
    LEFT JOIN categories c ON b.category_id = c.category_id
    WHERE b.is_active = TRUE
    AND (
        to_tsvector('english', b.title || ' ' || COALESCE(b.subtitle, '')) @@ plainto_tsquery('english', p_search_term)
        OR to_tsvector('english', a.first_name || ' ' || a.last_name) @@ plainto_tsquery('english', p_search_term)
        OR b.isbn ILIKE '%' || p_search_term || '%'
    )
    GROUP BY b.book_id, b.title, b.subtitle, c.category_name, 
             b.publication_year, b.available_copies, b.total_copies, b.isbn
    ORDER BY 
        ts_rank(to_tsvector('english', b.title || ' ' || COALESCE(b.subtitle, '')), 
                plainto_tsquery('english', p_search_term)) DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;
