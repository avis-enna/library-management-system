-- Triggers for Library Management System
-- Author: Venna Venkata Siva Reddy

-- Trigger function to update timestamp on record updates
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update timestamp triggers to relevant tables
CREATE TRIGGER trigger_books_updated_at
    BEFORE UPDATE ON books
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_members_updated_at
    BEFORE UPDATE ON members
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_borrowings_updated_at
    BEFORE UPDATE ON borrowings
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_fines_updated_at
    BEFORE UPDATE ON fines
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Trigger function for audit logging
CREATE OR REPLACE FUNCTION audit_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, record_id, new_values, changed_by)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.book_id, row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_values, new_values, changed_by)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.book_id, row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_values, changed_by)
        VALUES (TG_TABLE_NAME, TG_OP, OLD.book_id, row_to_json(OLD), current_user);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers to important tables
CREATE TRIGGER trigger_books_audit
    AFTER INSERT OR UPDATE OR DELETE ON books
    FOR EACH ROW
    EXECUTE FUNCTION audit_changes();

CREATE TRIGGER trigger_borrowings_audit
    AFTER INSERT OR UPDATE OR DELETE ON borrowings
    FOR EACH ROW
    EXECUTE FUNCTION audit_changes();

-- Trigger to automatically update book availability when borrowing changes
CREATE OR REPLACE FUNCTION update_book_availability()
RETURNS TRIGGER AS $$
BEGIN
    -- When a book is returned
    IF TG_OP = 'UPDATE' AND OLD.is_returned = FALSE AND NEW.is_returned = TRUE THEN
        -- Check if there are any pending reservations
        UPDATE reservations 
        SET is_fulfilled = TRUE, 
            fulfilled_date = CURRENT_DATE
        WHERE book_id = NEW.book_id 
        AND is_fulfilled = FALSE 
        AND reservation_id = (
            SELECT reservation_id 
            FROM reservations 
            WHERE book_id = NEW.book_id 
            AND is_fulfilled = FALSE 
            ORDER BY priority ASC, reservation_date ASC 
            LIMIT 1
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_book_availability
    AFTER UPDATE ON borrowings
    FOR EACH ROW
    EXECUTE FUNCTION update_book_availability();

-- Trigger to validate business rules
CREATE OR REPLACE FUNCTION validate_borrowing()
RETURNS TRIGGER AS $$
DECLARE
    member_can_borrow BOOLEAN;
    book_available INTEGER;
BEGIN
    -- Check on INSERT only
    IF TG_OP = 'INSERT' THEN
        -- Validate member can borrow
        SELECT can_member_borrow(NEW.member_id) INTO member_can_borrow;
        IF NOT member_can_borrow THEN
            RAISE EXCEPTION 'Member cannot borrow books at this time';
        END IF;
        
        -- Check book availability
        SELECT available_copies INTO book_available
        FROM books WHERE book_id = NEW.book_id;
        
        IF book_available <= 0 THEN
            RAISE EXCEPTION 'Book is not available for borrowing';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_borrowing
    BEFORE INSERT ON borrowings
    FOR EACH ROW
    EXECUTE FUNCTION validate_borrowing();

-- Trigger to automatically expire old reservations
CREATE OR REPLACE FUNCTION expire_reservations()
RETURNS TRIGGER AS $$
BEGIN
    -- Mark expired reservations as inactive
    UPDATE reservations
    SET is_fulfilled = TRUE
    WHERE expiry_date < CURRENT_DATE
    AND is_fulfilled = FALSE;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled trigger (would typically be run via cron job)
-- For demonstration, we'll create a function that can be called manually
CREATE OR REPLACE FUNCTION cleanup_expired_reservations()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE reservations
    SET is_fulfilled = TRUE
    WHERE expiry_date < CURRENT_DATE
    AND is_fulfilled = FALSE;
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to prevent deletion of books that are currently borrowed
CREATE OR REPLACE FUNCTION prevent_book_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM borrowings 
        WHERE book_id = OLD.book_id 
        AND is_returned = FALSE
    ) THEN
        RAISE EXCEPTION 'Cannot delete book that is currently borrowed';
    END IF;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_prevent_book_deletion
    BEFORE DELETE ON books
    FOR EACH ROW
    EXECUTE FUNCTION prevent_book_deletion();

-- Trigger to automatically calculate and update member statistics
CREATE OR REPLACE FUNCTION update_member_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update member's current borrowed book count and total fines
    UPDATE members
    SET 
        current_books_count = (
            SELECT COUNT(*) 
            FROM borrowings 
            WHERE member_id = COALESCE(NEW.member_id, OLD.member_id) 
            AND is_returned = FALSE
        ),
        total_fine_amount = (
            SELECT COALESCE(SUM(fine_amount), 0.00)
            FROM fines
            WHERE member_id = COALESCE(NEW.member_id, OLD.member_id)
            AND is_paid = FALSE
        )
    WHERE member_id = COALESCE(NEW.member_id, OLD.member_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_member_stats_borrowings
    AFTER INSERT OR UPDATE OR DELETE ON borrowings
    FOR EACH ROW
    EXECUTE FUNCTION update_member_stats();

CREATE TRIGGER trigger_update_member_stats_fines
    AFTER INSERT OR UPDATE OR DELETE ON fines
    FOR EACH ROW
    EXECUTE FUNCTION update_member_stats();
