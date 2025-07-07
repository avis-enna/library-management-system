-- Views for Library Management System
-- Author: Venna Venkata Siva Reddy

-- View for currently borrowed books
CREATE OR REPLACE VIEW current_borrowings AS
SELECT 
    b.borrowing_id,
    m.member_code,
    m.first_name || ' ' || m.last_name AS member_name,
    m.member_type,
    m.email,
    bk.title AS book_title,
    bk.isbn,
    STRING_AGG(a.first_name || ' ' || a.last_name, ', ') AS authors,
    b.borrowed_date,
    b.due_date,
    b.renewal_count,
    CASE 
        WHEN b.due_date < CURRENT_DATE THEN 'Overdue'
        WHEN b.due_date <= CURRENT_DATE + INTERVAL '3 days' THEN 'Due Soon'
        ELSE 'Active'
    END AS status,
    CASE 
        WHEN b.due_date < CURRENT_DATE THEN CURRENT_DATE - b.due_date
        ELSE 0
    END AS days_overdue
FROM borrowings b
JOIN members m ON b.member_id = m.member_id
JOIN books bk ON b.book_id = bk.book_id
LEFT JOIN book_authors ba ON bk.book_id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.author_id
WHERE b.is_returned = FALSE
GROUP BY b.borrowing_id, m.member_code, m.first_name, m.last_name, 
         m.member_type, m.email, bk.title, bk.isbn, b.borrowed_date, 
         b.due_date, b.renewal_count
ORDER BY b.due_date ASC;

-- View for overdue books
CREATE OR REPLACE VIEW overdue_books AS
SELECT 
    b.borrowing_id,
    m.member_code,
    m.first_name || ' ' || m.last_name AS member_name,
    m.email,
    m.phone,
    bk.title AS book_title,
    bk.isbn,
    b.borrowed_date,
    b.due_date,
    CURRENT_DATE - b.due_date AS days_overdue,
    (CURRENT_DATE - b.due_date) * 1.00 AS calculated_fine,
    b.renewal_count
FROM borrowings b
JOIN members m ON b.member_id = m.member_id
JOIN books bk ON b.book_id = bk.book_id
WHERE b.is_returned = FALSE 
AND b.due_date < CURRENT_DATE
ORDER BY days_overdue DESC;

-- View for book availability
CREATE OR REPLACE VIEW book_availability AS
SELECT 
    b.book_id,
    b.isbn,
    b.title,
    b.subtitle,
    STRING_AGG(a.first_name || ' ' || a.last_name, ', ') AS authors,
    c.category_name,
    b.publication_year,
    b.publisher,
    b.total_copies,
    b.available_copies,
    b.total_copies - b.available_copies AS copies_borrowed,
    CASE 
        WHEN b.available_copies > 0 THEN 'Available'
        ELSE 'Not Available'
    END AS availability_status,
    b.location,
    b.price,
    (SELECT COUNT(*) FROM reservations r WHERE r.book_id = b.book_id AND r.is_fulfilled = FALSE) AS pending_reservations
FROM books b
LEFT JOIN book_authors ba ON b.book_id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.author_id
LEFT JOIN categories c ON b.category_id = c.category_id
WHERE b.is_active = TRUE
GROUP BY b.book_id, b.isbn, b.title, b.subtitle, c.category_name, 
         b.publication_year, b.publisher, b.total_copies, b.available_copies,
         b.location, b.price
ORDER BY b.title;

-- View for member statistics
CREATE OR REPLACE VIEW member_statistics AS
SELECT 
    m.member_id,
    m.member_code,
    m.first_name || ' ' || m.last_name AS member_name,
    m.member_type,
    m.email,
    m.phone,
    m.registration_date,
    m.membership_expiry,
    m.max_books_allowed,
    m.current_books_count,
    m.total_fine_amount,
    (SELECT COUNT(*) FROM borrowings b WHERE b.member_id = m.member_id) AS total_books_borrowed,
    (SELECT COUNT(*) FROM borrowings b WHERE b.member_id = m.member_id AND b.is_returned = TRUE) AS books_returned,
    (SELECT COUNT(*) FROM borrowings b WHERE b.member_id = m.member_id AND b.is_returned = FALSE) AS books_currently_borrowed,
    (SELECT COUNT(*) FROM borrowings b WHERE b.member_id = m.member_id AND b.is_returned = FALSE AND b.due_date < CURRENT_DATE) AS overdue_books,
    (SELECT COUNT(*) FROM reservations r WHERE r.member_id = m.member_id AND r.is_fulfilled = FALSE) AS active_reservations,
    CASE 
        WHEN m.membership_expiry < CURRENT_DATE THEN 'Expired'
        WHEN m.membership_expiry <= CURRENT_DATE + INTERVAL '30 days' THEN 'Expiring Soon'
        WHEN m.is_active = FALSE THEN 'Inactive'
        ELSE 'Active'
    END AS membership_status
FROM members m
ORDER BY m.member_code;

-- View for popular books
CREATE OR REPLACE VIEW popular_books AS
SELECT 
    b.book_id,
    b.title,
    b.isbn,
    STRING_AGG(a.first_name || ' ' || a.last_name, ', ') AS authors,
    c.category_name,
    COUNT(br.borrowing_id) AS times_borrowed,
    COUNT(CASE WHEN br.borrowed_date >= CURRENT_DATE - INTERVAL '6 months' THEN 1 END) AS times_borrowed_6months,
    COUNT(CASE WHEN br.borrowed_date >= CURRENT_DATE - INTERVAL '1 month' THEN 1 END) AS times_borrowed_1month,
    b.available_copies,
    b.total_copies,
    ROUND(COUNT(br.borrowing_id)::DECIMAL / b.total_copies, 2) AS utilization_ratio
FROM books b
LEFT JOIN borrowings br ON b.book_id = br.book_id
LEFT JOIN book_authors ba ON b.book_id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.author_id
LEFT JOIN categories c ON b.category_id = c.category_id
WHERE b.is_active = TRUE
GROUP BY b.book_id, b.title, b.isbn, c.category_name, b.available_copies, b.total_copies
HAVING COUNT(br.borrowing_id) > 0
ORDER BY times_borrowed DESC, utilization_ratio DESC;

-- View for reservation queue
CREATE OR REPLACE VIEW reservation_queue AS
SELECT 
    r.reservation_id,
    b.title AS book_title,
    b.isbn,
    b.available_copies,
    m.member_code,
    m.first_name || ' ' || m.last_name AS member_name,
    m.member_type,
    m.email,
    r.reservation_date,
    r.expiry_date,
    r.priority,
    CASE 
        WHEN r.expiry_date < CURRENT_DATE THEN 'Expired'
        WHEN r.expiry_date <= CURRENT_DATE + INTERVAL '2 days' THEN 'Expiring Soon'
        ELSE 'Active'
    END AS reservation_status
FROM reservations r
JOIN books b ON r.book_id = b.book_id
JOIN members m ON r.member_id = m.member_id
WHERE r.is_fulfilled = FALSE
ORDER BY b.title, r.priority ASC, r.reservation_date ASC;

-- View for financial summary
CREATE OR REPLACE VIEW financial_summary AS
SELECT 
    DATE_TRUNC('month', f.created_at) AS month,
    COUNT(f.fine_id) AS total_fines_issued,
    SUM(f.fine_amount) AS total_fine_amount,
    COUNT(CASE WHEN f.is_paid = TRUE THEN 1 END) AS fines_paid,
    SUM(CASE WHEN f.is_paid = TRUE THEN f.fine_amount ELSE 0 END) AS amount_collected,
    COUNT(CASE WHEN f.is_paid = FALSE THEN 1 END) AS fines_outstanding,
    SUM(CASE WHEN f.is_paid = FALSE THEN f.fine_amount ELSE 0 END) AS amount_outstanding
FROM fines f
GROUP BY DATE_TRUNC('month', f.created_at)
ORDER BY month DESC;

-- View for daily library activity
CREATE OR REPLACE VIEW daily_activity AS
SELECT 
    activity_date,
    books_issued,
    books_returned,
    new_members,
    new_reservations,
    fines_collected
FROM (
    SELECT 
        CURRENT_DATE as activity_date,
        (SELECT COUNT(*) FROM borrowings WHERE borrowed_date = CURRENT_DATE) as books_issued,
        (SELECT COUNT(*) FROM borrowings WHERE returned_date = CURRENT_DATE) as books_returned,
        (SELECT COUNT(*) FROM members WHERE registration_date = CURRENT_DATE) as new_members,
        (SELECT COUNT(*) FROM reservations WHERE reservation_date = CURRENT_DATE) as new_reservations,
        (SELECT COALESCE(SUM(fine_amount), 0) FROM fines WHERE payment_date = CURRENT_DATE) as fines_collected
) daily_stats;

-- View for category-wise book distribution
CREATE OR REPLACE VIEW category_distribution AS
SELECT 
    c.category_name,
    COUNT(b.book_id) AS total_books,
    SUM(b.total_copies) AS total_copies,
    SUM(b.available_copies) AS available_copies,
    COUNT(CASE WHEN b.available_copies > 0 THEN 1 END) AS books_available,
    COUNT(CASE WHEN b.available_copies = 0 THEN 1 END) AS books_unavailable,
    ROUND(AVG(b.price), 2) AS average_price,
    COUNT(br.borrowing_id) AS total_borrowings
FROM categories c
LEFT JOIN books b ON c.category_id = b.category_id AND b.is_active = TRUE
LEFT JOIN borrowings br ON b.book_id = br.book_id
GROUP BY c.category_id, c.category_name
ORDER BY total_books DESC;
