-- Sample Data for Library Management System
-- Author: Venna Venkata Siva Reddy

-- Insert Categories
INSERT INTO categories (category_name, description) VALUES
('Computer Science', 'Books related to computer science and programming'),
('Mathematics', 'Mathematics and related topics'),
('Physics', 'Physics and applied physics'),
('Literature', 'Fiction and non-fiction literature'),
('History', 'Historical books and documents'),
('Biology', 'Biology and life sciences'),
('Engineering', 'Engineering disciplines'),
('Business', 'Business and management'),
('Psychology', 'Psychology and behavioral sciences'),
('Philosophy', 'Philosophy and ethics');

-- Insert Authors
INSERT INTO authors (first_name, last_name, birth_date, nationality, biography) VALUES
('Robert', 'Martin', '1952-12-05', 'American', 'Software engineer and author, known for Clean Code'),
('Martin', 'Fowler', '1963-12-18', 'British', 'Software engineer, author of Refactoring'),
('Eric', 'Evans', '1962-01-01', 'American', 'Software engineer, author of Domain-Driven Design'),
('Gang of Four', 'GoF', '1960-01-01', 'International', 'Authors of Design Patterns book'),
('Donald', 'Knuth', '1938-01-10', 'American', 'Computer scientist, author of The Art of Computer Programming'),
('Thomas', 'Cormen', '1956-01-01', 'American', 'Computer scientist, co-author of Introduction to Algorithms'),
('Brian', 'Kernighan', '1942-01-01', 'Canadian', 'Computer scientist, co-author of The C Programming Language'),
('Dennis', 'Ritchie', '1941-09-09', 'American', 'Creator of C programming language'),
('Bjarne', 'Stroustrup', '1950-12-30', 'Danish', 'Creator of C++ programming language'),
('James', 'Gosling', '1955-05-19', 'Canadian', 'Creator of Java programming language');

-- Insert Books
INSERT INTO books (isbn, title, subtitle, publication_year, publisher, edition, pages, category_id, total_copies, available_copies, location, price) VALUES
('9780132350884', 'Clean Code', 'A Handbook of Agile Software Craftsmanship', 2008, 'Prentice Hall', '1st', 464, 1, 5, 5, 'CS-001-A', 45.99),
('9780201485677', 'Refactoring', 'Improving the Design of Existing Code', 1999, 'Addison-Wesley', '1st', 431, 1, 3, 3, 'CS-001-B', 54.99),
('9780321125217', 'Domain-Driven Design', 'Tackling Complexity in the Heart of Software', 2003, 'Addison-Wesley', '1st', 560, 1, 2, 2, 'CS-001-C', 59.99),
('9780201633610', 'Design Patterns', 'Elements of Reusable Object-Oriented Software', 1994, 'Addison-Wesley', '1st', 395, 1, 4, 4, 'CS-002-A', 64.99),
('9780201896831', 'The Art of Computer Programming Vol 1', 'Fundamental Algorithms', 1997, 'Addison-Wesley', '3rd', 672, 1, 2, 2, 'CS-003-A', 89.99),
('9780262033848', 'Introduction to Algorithms', '', 2009, 'MIT Press', '3rd', 1312, 1, 6, 6, 'CS-004-A', 94.99),
('9780131103627', 'The C Programming Language', '', 1988, 'Prentice Hall', '2nd', 272, 1, 8, 8, 'CS-005-A', 39.99),
('9780201700732', 'The C++ Programming Language', '', 2013, 'Addison-Wesley', '4th', 1376, 1, 4, 4, 'CS-005-B', 69.99),
('9780134685991', 'Effective Java', '', 2017, 'Addison-Wesley', '3rd', 412, 1, 5, 5, 'CS-006-A', 49.99),
('9781617294945', 'Spring in Action', '', 2018, 'Manning', '5th', 520, 1, 3, 3, 'CS-007-A', 44.99);

-- Insert Book-Author relationships
INSERT INTO book_authors (book_id, author_id, author_role) VALUES
(1, 1, 'Author'),
(2, 2, 'Author'),
(3, 3, 'Author'),
(4, 4, 'Author'),
(5, 5, 'Author'),
(6, 6, 'Author'),
(7, 7, 'Co-Author'),
(7, 8, 'Co-Author'),
(8, 9, 'Author'),
(10, 10, 'Author');

-- Insert Members
INSERT INTO members (member_type, member_code, first_name, last_name, email, phone, address, registration_date, membership_expiry, max_books_allowed) VALUES
('student', 'STU001', 'John', 'Doe', 'john.doe@university.edu', '555-0101', '123 Campus Drive, University City', '2024-01-15', '2025-01-15', 5),
('student', 'STU002', 'Jane', 'Smith', 'jane.smith@university.edu', '555-0102', '456 Student Lane, University City', '2024-02-01', '2025-02-01', 5),
('faculty', 'FAC001', 'Dr. Michael', 'Johnson', 'mjohnson@university.edu', '555-0201', '789 Faculty Row, University City', '2024-01-01', '2025-12-31', 10),
('faculty', 'FAC002', 'Prof. Sarah', 'Williams', 'swilliams@university.edu', '555-0202', '321 Professor Ave, University City', '2024-01-01', '2025-12-31', 10),
('staff', 'STA001', 'Robert', 'Brown', 'rbrown@university.edu', '555-0301', '654 Staff Street, University City', '2024-01-01', '2025-12-31', 7),
('student', 'STU003', 'Emily', 'Davis', 'emily.davis@university.edu', '555-0103', '987 Dorm Hall, University City', '2024-03-01', '2025-03-01', 5),
('student', 'STU004', 'David', 'Wilson', 'david.wilson@university.edu', '555-0104', '147 Apartment Complex, University City', '2024-03-15', '2025-03-15', 5),
('external', 'EXT001', 'Lisa', 'Garcia', 'lisa.garcia@email.com', '555-0401', '258 Public Street, City', '2024-04-01', '2024-10-01', 3),
('student', 'STU005', 'Kevin', 'Martinez', 'kevin.martinez@university.edu', '555-0105', '369 Student Housing, University City', '2024-05-01', '2025-05-01', 5),
('faculty', 'FAC003', 'Dr. Amanda', 'Taylor', 'ataylor@university.edu', '555-0203', '741 Research Building, University City', '2024-01-01', '2025-12-31', 10);

-- Insert some sample borrowings
INSERT INTO borrowings (member_id, book_id, borrowed_date, due_date, is_returned) VALUES
(1, 1, '2024-06-01', '2024-06-15', FALSE),
(1, 6, '2024-06-05', '2024-06-19', FALSE),
(2, 2, '2024-06-10', '2024-06-24', FALSE),
(3, 3, '2024-05-20', '2024-06-03', TRUE),
(4, 4, '2024-06-01', '2024-06-15', FALSE),
(5, 7, '2024-05-25', '2024-06-08', TRUE),
(6, 8, '2024-06-12', '2024-06-26', FALSE),
(7, 9, '2024-06-08', '2024-06-22', FALSE),
(8, 10, '2024-06-15', '2024-06-29', FALSE);

-- Update returned borrowings with return dates
UPDATE borrowings 
SET returned_date = '2024-06-02', 
    return_condition = 'Good'
WHERE borrowing_id = 4;

UPDATE borrowings 
SET returned_date = '2024-06-10', 
    return_condition = 'Good'
WHERE borrowing_id = 6;

-- Insert some reservations
INSERT INTO reservations (member_id, book_id, reservation_date, expiry_date) VALUES
(9, 1, '2024-06-16', '2024-06-23'),
(10, 2, '2024-06-17', '2024-06-24'),
(2, 3, '2024-06-18', '2024-06-25');

-- Insert some fines (for demonstration)
INSERT INTO fines (borrowing_id, member_id, fine_type, fine_amount, fine_reason) VALUES
(4, 3, 'Late Return', 0.00, 'Returned on time'),
(6, 5, 'Late Return', 2.00, 'Returned 2 days late');

-- Update book availability based on borrowings
UPDATE books SET available_copies = total_copies - (
    SELECT COUNT(*) 
    FROM borrowings 
    WHERE borrowings.book_id = books.book_id 
    AND is_returned = FALSE
);

-- Update member statistics
UPDATE members SET 
    current_books_count = (
        SELECT COUNT(*) 
        FROM borrowings 
        WHERE borrowings.member_id = members.member_id 
        AND is_returned = FALSE
    ),
    total_fine_amount = (
        SELECT COALESCE(SUM(fine_amount), 0.00)
        FROM fines
        WHERE fines.member_id = members.member_id
        AND is_paid = FALSE
    );
