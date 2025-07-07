#!/usr/bin/env python3
"""
Library Management System - Demo API
A simplified version using SQLite for easy deployment
Author: Venna Venkata Siva Reddy
"""

import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'

# Enable CORS
CORS(app)

# SQLite database setup
DB_PATH = 'library_demo.db'

def init_db():
    """Initialize SQLite database with sample data"""
    # Remove existing database to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript('''
    CREATE TABLE IF NOT EXISTS authors (
        author_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        birth_date DATE,
        nationality VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_name VARCHAR(100) UNIQUE NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn VARCHAR(13) UNIQUE NOT NULL,
        title VARCHAR(200) NOT NULL,
        publication_year INTEGER,
        publisher VARCHAR(100),
        total_copies INTEGER DEFAULT 1,
        available_copies INTEGER DEFAULT 1,
        category_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    );

    CREATE TABLE IF NOT EXISTS book_authors (
        book_id INTEGER,
        author_id INTEGER,
        PRIMARY KEY (book_id, author_id),
        FOREIGN KEY (book_id) REFERENCES books(book_id),
        FOREIGN KEY (author_id) REFERENCES authors(author_id)
    );

    CREATE TABLE IF NOT EXISTS members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        phone VARCHAR(15),
        address TEXT,
        membership_date DATE DEFAULT CURRENT_DATE,
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS borrowings (
        borrowing_id INTEGER PRIMARY KEY AUTOINCREMENT,
        member_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        borrow_date DATE DEFAULT CURRENT_DATE,
        due_date DATE,
        return_date DATE,
        status VARCHAR(20) DEFAULT 'borrowed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (member_id) REFERENCES members(member_id),
        FOREIGN KEY (book_id) REFERENCES books(book_id)
    );
    ''')
    
    # Insert sample data
    cursor.executescript('''
    INSERT OR IGNORE INTO categories (category_name, description) VALUES
    ('Technology', 'Books about technology and programming'),
    ('Science', 'Scientific and research books'),
    ('Fiction', 'Fictional literature and novels'),
    ('Business', 'Business and management books'),
    ('History', 'Historical books and biographies'),
    ('Mathematics', 'Mathematics and statistical books'),
    ('Philosophy', 'Philosophy and ethics books'),
    ('Art', 'Art, design, and creative books');

    INSERT OR IGNORE INTO authors (first_name, last_name, nationality, birth_date) VALUES
    ('Robert', 'Martin', 'American', '1952-12-05'),
    ('Eric', 'Evans', 'American', '1962-03-15'),
    ('Martin', 'Fowler', 'British', '1963-12-18'),
    ('Erich', 'Gamma', 'Swiss', '1961-03-13'),
    ('Richard', 'Helm', 'American', '1956-09-22'),
    ('Ralph', 'Johnson', 'American', '1955-10-07'),
    ('John', 'Vlissides', 'American', '1961-08-02'),
    ('Joshua', 'Bloch', 'American', '1961-08-28'),
    ('Kathy', 'Sierra', 'American', '1957-03-24'),
    ('Bert', 'Bates', 'American', '1960-06-18'),
    ('Steve', 'McConnell', 'American', '1962-06-15'),
    ('Andrew', 'Hunt', 'Canadian', '1964-04-20'),
    ('David', 'Thomas', 'British', '1956-11-30'),
    ('Frederick', 'Brooks', 'American', '1931-04-19'),
    ('Donald', 'Knuth', 'American', '1938-01-10'),
    ('Bjarne', 'Stroustrup', 'Danish', '1950-12-30'),
    ('Linus', 'Torvalds', 'Finnish', '1969-12-28'),
    ('Tim', 'Berners-Lee', 'British', '1955-06-08'),
    ('Ada', 'Lovelace', 'British', '1815-12-10'),
    ('Alan', 'Turing', 'British', '1912-06-23');

    INSERT OR IGNORE INTO books (isbn, title, publication_year, publisher, total_copies, available_copies, category_id) VALUES
    ('9780132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 2008, 'Prentice Hall', 5, 3, 1),
    ('9780321125217', 'Domain-Driven Design: Tackling Complexity in the Heart of Software', 2003, 'Addison-Wesley', 3, 2, 1),
    ('9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 1994, 'Addison-Wesley', 4, 4, 1),
    ('9780134685991', 'Effective Java', 2017, 'Addison-Wesley', 6, 5, 1),
    ('9780596007126', 'Head First Design Patterns', 2004, 'O''Reilly Media', 4, 3, 1),
    ('9780735619678', 'Code Complete: A Practical Handbook of Software Construction', 2004, 'Microsoft Press', 3, 2, 1),
    ('9780201616224', 'The Pragmatic Programmer: From Journeyman to Master', 1999, 'Addison-Wesley', 5, 4, 1),
    ('9780201835953', 'The Mythical Man-Month: Essays on Software Engineering', 1995, 'Addison-Wesley', 2, 1, 1),
    ('9780201896831', 'The Art of Computer Programming, Volume 1', 1997, 'Addison-Wesley', 2, 2, 6),
    ('9780321563842', 'The C++ Programming Language', 2013, 'Addison-Wesley', 4, 3, 1),
    ('9780596009205', 'Head First Java', 2005, 'O''Reilly Media', 6, 4, 1),
    ('9780134052786', 'Java: The Complete Reference', 2020, 'McGraw-Hill', 3, 2, 1),
    ('9780135166307', 'Refactoring: Improving the Design of Existing Code', 2018, 'Addison-Wesley', 3, 3, 1),
    ('9780134494166', 'Clean Architecture: A Craftsman''s Guide to Software Structure', 2017, 'Prentice Hall', 4, 2, 1),
    ('9780321127426', 'Patterns of Enterprise Application Architecture', 2002, 'Addison-Wesley', 2, 1, 1),
    ('9780062315007', 'The Lean Startup', 2011, 'Crown Business', 3, 2, 4),
    ('9780307887894', 'The Hard Thing About Hard Things', 2014, 'Harper Business', 2, 1, 4),
    ('9781119278962', 'Building Microservices: Designing Fine-Grained Systems', 2021, 'O''Reilly Media', 3, 2, 1),
    ('9781492032526', 'Designing Data-Intensive Applications', 2017, 'O''Reilly Media', 4, 3, 1),
    ('9780316769174', 'The Catcher in the Rye', 1951, 'Little, Brown', 5, 4, 3),
    ('9780062316097', 'Sapiens: A Brief History of Humankind', 2014, 'Harper', 4, 3, 5),
    ('9780345816023', 'The Name of the Wind', 2007, 'DAW Books', 3, 2, 3),
    ('9780553573404', 'A Brief History of Time', 1988, 'Bantam', 3, 2, 2),
    ('9780486411095', 'Flatland: A Romance of Many Dimensions', 1884, 'Dover Publications', 2, 2, 6),
    ('9780674022966', 'Justice: What''s the Right Thing to Do?', 2009, 'Harvard University Press', 2, 1, 7);

    INSERT OR IGNORE INTO book_authors (book_id, author_id) VALUES
    (1, 1), (2, 2), (3, 4), (3, 5), (3, 6), (3, 7), (4, 8), (5, 9), (5, 10),
    (6, 11), (7, 12), (7, 13), (8, 14), (9, 15), (10, 16), (11, 9), (11, 10),
    (12, 8), (13, 3), (14, 1), (15, 3), (16, 2), (17, 2), (18, 3), (19, 3);

    INSERT OR IGNORE INTO members (first_name, last_name, email, phone, address, membership_date, status) VALUES
    ('John', 'Doe', 'john.doe@email.com', '+1-555-0101', '123 Main St', '2024-01-15', 'active'),
    ('Jane', 'Smith', 'jane.smith@email.com', '+1-555-0102', '456 Oak Ave', '2024-02-20', 'active'),
    ('Mike', 'Johnson', 'mike.j@email.com', '+1-555-0103', '789 Pine Rd', '2024-03-10', 'active'),
    ('Sarah', 'Williams', 'sarah.w@email.com', '+1-555-0104', '321 Elm St', '2024-04-05', 'active'),
    ('David', 'Brown', 'david.brown@email.com', '+1-555-0105', '654 Maple Dr', '2024-05-12', 'active'),
    ('Emily', 'Davis', 'emily.davis@email.com', '+1-555-0106', '987 Cedar Ln', '2024-06-01', 'active'),
    ('Chris', 'Wilson', 'chris.wilson@email.com', '+1-555-0107', '246 Birch Rd', '2024-07-03', 'active'),
    ('Lisa', 'Garcia', 'lisa.garcia@email.com', '+1-555-0108', '135 Spruce Ave', '2023-12-20', 'active'),
    ('Mark', 'Rodriguez', 'mark.r@email.com', '+1-555-0109', '864 Willow St', '2023-11-15', 'active'),
    ('Amy', 'Martinez', 'amy.martinez@email.com', '+1-555-0110', '579 Poplar Dr', '2023-10-08', 'active'),
    ('Ryan', 'Taylor', 'ryan.taylor@email.com', '+1-555-0111', '792 Hickory Ln', '2024-01-30', 'active'),
    ('Jessica', 'Anderson', 'jessica.a@email.com', '+1-555-0112', '468 Ash Rd', '2024-02-14', 'active'),
    ('Kevin', 'Thomas', 'kevin.thomas@email.com', '+1-555-0113', '913 Walnut Ave', '2024-03-25', 'active'),
    ('Michelle', 'White', 'michelle.w@email.com', '+1-555-0114', '357 Cherry St', '2024-04-18', 'active'),
    ('Alex', 'Lee', 'alex.lee@email.com', '+1-555-0115', '682 Sycamore Dr', '2024-05-22', 'active');

    INSERT OR IGNORE INTO borrowings (member_id, book_id, borrow_date, due_date, return_date, status) VALUES
    (1, 1, '2025-06-01', '2025-07-01', NULL, 'borrowed'),
    (2, 2, '2025-06-15', '2025-07-15', NULL, 'borrowed'),
    (3, 3, '2025-06-20', '2025-07-20', NULL, 'borrowed'),
    (4, 5, '2025-06-25', '2025-07-25', NULL, 'borrowed'),
    (5, 7, '2025-07-01', '2025-08-01', NULL, 'borrowed'),
    (6, 11, '2025-07-02', '2025-08-02', NULL, 'borrowed'),
    (7, 13, '2025-07-03', '2025-08-03', NULL, 'borrowed'),
    (8, 16, '2025-07-04', '2025-08-04', NULL, 'borrowed'),
    (9, 19, '2025-07-05', '2025-08-05', NULL, 'borrowed'),
    (10, 21, '2025-07-06', '2025-08-06', NULL, 'borrowed'),
    (1, 4, '2025-05-01', '2025-06-01', '2025-05-28', 'returned'),
    (2, 6, '2025-05-10', '2025-06-10', '2025-06-08', 'returned'),
    (3, 8, '2025-05-15', '2025-06-15', '2025-06-12', 'returned'),
    (4, 10, '2025-04-20', '2025-05-20', '2025-05-18', 'returned'),
    (5, 12, '2025-04-25', '2025-05-25', '2025-05-23', 'returned'),
    (6, 14, '2025-04-30', '2025-05-30', '2025-05-27', 'returned'),
    (7, 15, '2025-03-15', '2025-04-15', '2025-04-10', 'returned'),
    (8, 17, '2025-03-20', '2025-04-20', '2025-04-15', 'returned'),
    (9, 18, '2025-03-25', '2025-04-25', '2025-04-20', 'returned'),
    (10, 20, '2025-02-10', '2025-03-10', '2025-03-05', 'returned');
    ''')
    
    conn.commit()
    conn.close()

# HTML template for the demo interface
DEMO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Library Management System - Demo</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .demo-section {
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .demo-section h2 { 
            color: #667eea; 
            margin-bottom: 20px; 
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        .api-endpoint {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin: 10px 0;
            font-family: monospace;
        }
        .method { 
            background: #28a745; 
            color: white; 
            padding: 3px 8px; 
            border-radius: 3px; 
            font-size: 0.8rem;
            margin-right: 10px;
        }
        .endpoint { color: #495057; font-weight: bold; }
        .description { margin-top: 5px; color: #6c757d; }
        .try-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        .try-button:hover { background: #5a6fd8; }
        .result-box {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            margin-top: 10px;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 0.9rem;
            max-height: 300px;
            overflow-y: auto;
        }
        .form-section {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 20px;
            margin-top: 20px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }
        .form-group {
            display: flex;
            flex-direction: column;
        }
        .form-group label {
            font-weight: bold;
            margin-bottom: 5px;
            color: #495057;
        }
        .form-group input, .form-group select {
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }
        .submit-button {
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .submit-button:hover { background: #218838; }
        .delete-button {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
        }
        .delete-button:hover { background: #c82333; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number { font-size: 2rem; font-weight: bold; }
        .stat-label { opacity: 0.9; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Library Management System</h1>
            <p>Interactive Demo - PostgreSQL Database Project</p>
            <p><strong>By Venna Venkata Siva Reddy</strong></p>
        </div>

        <div class="demo-section">
            <h2>� Interactive Database Operations (DML)</h2>
            <p style="color: #6c757d; margin-bottom: 20px;">Try creating, updating, and managing library data in real-time!</p>
            
            <!-- Add New Member -->
            <div class="form-section">
                <h3 style="color: #667eea; margin-bottom: 15px;">➕ Add New Member</h3>
                <form id="addMemberForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="firstName">First Name *</label>
                            <input type="text" id="firstName" name="first_name" required>
                        </div>
                        <div class="form-group">
                            <label for="lastName">Last Name *</label>
                            <input type="text" id="lastName" name="last_name" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="email">Email *</label>
                            <input type="email" id="email" name="email" required>
                        </div>
                        <div class="form-group">
                            <label for="phone">Phone</label>
                            <input type="text" id="phone" name="phone">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="address">Address</label>
                        <input type="text" id="address" name="address">
                    </div>
                    <button type="submit" class="submit-button">Add Member</button>
                </form>
                <div id="addMemberResult" class="result-box" style="display:none;"></div>
            </div>

            <!-- Borrow Book -->
            <div class="form-section">
                <h3 style="color: #667eea; margin-bottom: 15px;">📚 Borrow Book</h3>
                <form id="borrowBookForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="borrowMemberId">Member ID *</label>
                            <input type="number" id="borrowMemberId" name="member_id" required min="1">
                        </div>
                        <div class="form-group">
                            <label for="borrowBookId">Book ID *</label>
                            <input type="number" id="borrowBookId" name="book_id" required min="1">
                        </div>
                    </div>
                    <button type="submit" class="submit-button">Borrow Book</button>
                </form>
                <div id="borrowBookResult" class="result-box" style="display:none;"></div>
            </div>

            <!-- Return Book -->
            <div class="form-section">
                <h3 style="color: #667eea; margin-bottom: 15px;">🔄 Return Book</h3>
                <form id="returnBookForm">
                    <div class="form-group">
                        <label for="borrowingId">Borrowing ID *</label>
                        <input type="number" id="borrowingId" name="borrowing_id" required min="1">
                        <small style="color: #6c757d;">Check the borrowings list above to find the borrowing ID</small>
                    </div>
                    <button type="submit" class="submit-button">Return Book</button>
                </form>
                <div id="returnBookResult" class="result-box" style="display:none;"></div>
            </div>

            <!-- Add New Book -->
            <div class="form-section">
                <h3 style="color: #667eea; margin-bottom: 15px;">📖 Add New Book</h3>
                <form id="addBookForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="bookIsbn">ISBN *</label>
                            <input type="text" id="bookIsbn" name="isbn" required>
                        </div>
                        <div class="form-group">
                            <label for="bookTitle">Title *</label>
                            <input type="text" id="bookTitle" name="title" required>
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="bookYear">Publication Year *</label>
                            <input type="number" id="bookYear" name="publication_year" required min="1000" max="2025">
                        </div>
                        <div class="form-group">
                            <label for="bookPublisher">Publisher</label>
                            <input type="text" id="bookPublisher" name="publisher">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="bookCopies">Total Copies</label>
                            <input type="number" id="bookCopies" name="total_copies" min="1" value="1">
                        </div>
                        <div class="form-group">
                            <label for="bookCategory">Category</label>
                            <select id="bookCategory" name="category_id">
                                <option value="1">Technology</option>
                                <option value="2">Science</option>
                                <option value="3">Fiction</option>
                                <option value="4">Business</option>
                                <option value="5">History</option>
                                <option value="6">Mathematics</option>
                                <option value="7">Philosophy</option>
                                <option value="8">Art</option>
                            </select>
                        </div>
                    </div>
                    <button type="submit" class="submit-button">Add Book</button>
                </form>
                <div id="addBookResult" class="result-box" style="display:none;"></div>
            </div>
        </div>

        <div class="demo-section">
            <h2>�📊 Database Statistics</h2>
            <div class="stats-grid" id="stats-grid">
                <!-- Stats will be loaded here -->
            </div>
        </div>

        <div class="demo-section">
            <h2>📚 Available API Endpoints</h2>
            
            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/books</span>
                <div class="description">Get all books in the library</div>
                <button class="try-button" onclick="tryEndpoint('/api/books')">Try It</button>
                <div id="result-books" class="result-box" style="display:none;"></div>
            </div>

            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/books/available</span>
                <div class="description">Get only available books</div>
                <button class="try-button" onclick="tryEndpoint('/api/books/available')">Try It</button>
                <div id="result-available" class="result-box" style="display:none;"></div>
            </div>

            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/authors</span>
                <div class="description">Get all authors</div>
                <button class="try-button" onclick="tryEndpoint('/api/authors')">Try It</button>
                <div id="result-authors" class="result-box" style="display:none;"></div>
            </div>

            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/categories</span>
                <div class="description">Get all book categories</div>
                <button class="try-button" onclick="tryEndpoint('/api/categories')">Try It</button>
                <div id="result-categories" class="result-box" style="display:none;"></div>
            </div>

            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/members</span>
                <div class="description">Get all library members</div>
                <button class="try-button" onclick="tryEndpoint('/api/members')">Try It</button>
                <div id="result-members" class="result-box" style="display:none;"></div>
            </div>

            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/borrowings</span>
                <div class="description">Get all current borrowings</div>
                <button class="try-button" onclick="tryEndpoint('/api/borrowings')">Try It</button>
                <div id="result-borrowings" class="result-box" style="display:none;"></div>
            </div>

            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/borrowings/overdue</span>
                <div class="description">Get overdue borrowings</div>
                <button class="try-button" onclick="tryEndpoint('/api/borrowings/overdue')">Try It</button>
                <div id="result-overdue" class="result-box" style="display:none;"></div>
            </div>

            <div class="api-endpoint">
                <span class="method">GET</span>
                <span class="endpoint">/api/stats</span>
                <div class="description">Get library statistics</div>
                <button class="try-button" onclick="tryEndpoint('/api/stats')">Try It</button>
                <div id="result-stats" class="result-box" style="display:none;"></div>
            </div>
        </div>

        <div class="demo-section">
            <h2>🔧 Technical Features Demonstrated</h2>
            <ul style="line-height: 2;">
                <li><strong>Database Design:</strong> Normalized schema with proper relationships and foreign keys</li>
                <li><strong>Complex Queries:</strong> JOINs, GROUP BY, aggregations, and date calculations</li>
                <li><strong>Full CRUD Operations:</strong> Create, Read, Update, Delete with real-time interaction</li>
                <li><strong>Data Validation:</strong> Input validation, constraint checking, and error handling</li>
                <li><strong>Transaction Management:</strong> Atomic operations for borrowing/returning books</li>
                <li><strong>Business Logic:</strong> Overdue tracking, availability management, member status</li>
                <li><strong>RESTful API Design:</strong> Proper HTTP methods (GET, POST, PUT, DELETE)</li>
                <li><strong>Real-time Updates:</strong> Live statistics refresh after DML operations</li>
                <li><strong>Interactive Demo:</strong> Visitors can add members, borrow/return books, add books</li>
                <li><strong>Comprehensive Dataset:</strong> 25+ books, 20+ authors, 15+ members, 20+ transactions</li>
                <li><strong>Production-Ready Code:</strong> Error handling, status codes, JSON responses</li>
            </ul>
        </div>
    </div>

    <script>
        async function tryEndpoint(endpoint) {
            const resultId = 'result-' + endpoint.split('/').pop();
            const resultBox = document.getElementById(resultId);
            
            resultBox.style.display = 'block';
            resultBox.textContent = 'Loading...';
            
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                resultBox.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultBox.textContent = 'Error: ' + error.message;
            }
        }

        // Form submission handlers
        document.getElementById('addMemberForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            const resultBox = document.getElementById('addMemberResult');
            resultBox.style.display = 'block';
            resultBox.textContent = 'Adding member...';
            
            try {
                const response = await fetch('/api/members', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                resultBox.textContent = JSON.stringify(result, null, 2);
                
                if (result.success) {
                    e.target.reset();
                    loadStats(); // Refresh stats
                }
            } catch (error) {
                resultBox.textContent = 'Error: ' + error.message;
            }
        });

        document.getElementById('borrowBookForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            data.member_id = parseInt(data.member_id);
            data.book_id = parseInt(data.book_id);
            
            const resultBox = document.getElementById('borrowBookResult');
            resultBox.style.display = 'block';
            resultBox.textContent = 'Processing borrowing...';
            
            try {
                const response = await fetch('/api/borrowings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                resultBox.textContent = JSON.stringify(result, null, 2);
                
                if (result.success) {
                    e.target.reset();
                    loadStats(); // Refresh stats
                }
            } catch (error) {
                resultBox.textContent = 'Error: ' + error.message;
            }
        });

        document.getElementById('returnBookForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const borrowingId = formData.get('borrowing_id');
            
            const resultBox = document.getElementById('returnBookResult');
            resultBox.style.display = 'block';
            resultBox.textContent = 'Processing return...';
            
            try {
                const response = await fetch(`/api/borrowings/${borrowingId}/return`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' }
                });
                const result = await response.json();
                resultBox.textContent = JSON.stringify(result, null, 2);
                
                if (result.success) {
                    e.target.reset();
                    loadStats(); // Refresh stats
                }
            } catch (error) {
                resultBox.textContent = 'Error: ' + error.message;
            }
        });

        document.getElementById('addBookForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            data.publication_year = parseInt(data.publication_year);
            data.total_copies = parseInt(data.total_copies || 1);
            data.category_id = parseInt(data.category_id);
            
            const resultBox = document.getElementById('addBookResult');
            resultBox.style.display = 'block';
            resultBox.textContent = 'Adding book...';
            
            try {
                const response = await fetch('/api/books', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                const result = await response.json();
                resultBox.textContent = JSON.stringify(result, null, 2);
                
                if (result.success) {
                    e.target.reset();
                    loadStats(); // Refresh stats
                }
            } catch (error) {
                resultBox.textContent = 'Error: ' + error.message;
            }
        });

        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                const stats = data.stats;
                
                const statsGrid = document.getElementById('stats-grid');
                statsGrid.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_books || 0}</div>
                        <div class="stat-label">Total Books</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_authors || 0}</div>
                        <div class="stat-label">Authors</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_members || 0}</div>
                        <div class="stat-label">Members</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.active_borrowings || 0}</div>
                        <div class="stat-label">Active Loans</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_categories || 0}</div>
                        <div class="stat-label">Categories</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_copies || 0}</div>
                        <div class="stat-label">Total Copies</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.available_copies || 0}</div>
                        <div class="stat-label">Available</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.overdue_borrowings || 0}</div>
                        <div class="stat-label">Overdue</div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading stats:', error);
            }
        }

        // Load stats on page load
        loadStats();
    </script>
</body>
</html>
'''

@app.route('/')
def demo_home():
    """Demo homepage with interactive interface"""
    return render_template_string(DEMO_TEMPLATE)

@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/books')
def get_books():
    """Get all books with author information"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.*, c.category_name,
               GROUP_CONCAT(a.first_name || ' ' || a.last_name) as authors
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        GROUP BY b.book_id
        ORDER BY b.title
    ''')
    
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(books),
        "books": books
    })

@app.route('/api/books/available')
def get_available_books():
    """Get only available books"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT b.*, c.category_name,
               GROUP_CONCAT(a.first_name || ' ' || a.last_name) as authors
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        WHERE b.available_copies > 0
        GROUP BY b.book_id
        ORDER BY b.title
    ''')
    
    books = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(books),
        "books": books
    })

@app.route('/api/authors')
def get_authors():
    """Get all authors with book count"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.*, COUNT(ba.book_id) as book_count
        FROM authors a
        LEFT JOIN book_authors ba ON a.author_id = ba.author_id
        GROUP BY a.author_id
        ORDER BY a.last_name, a.first_name
    ''')
    
    authors = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(authors),
        "authors": authors
    })

@app.route('/api/categories')
def get_categories():
    """Get all categories with book counts"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT c.*, COUNT(b.book_id) as book_count
        FROM categories c
        LEFT JOIN books b ON c.category_id = b.category_id
        GROUP BY c.category_id
        ORDER BY c.category_name
    ''')
    
    categories = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(categories),
        "categories": categories
    })

@app.route('/api/members')
def get_members():
    """Get all library members"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, COUNT(br.borrowing_id) as total_borrowings
        FROM members m
        LEFT JOIN borrowings br ON m.member_id = br.member_id
        GROUP BY m.member_id
        ORDER BY m.last_name, m.first_name
    ''')
    
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(members),
        "members": members
    })

@app.route('/api/borrowings')
def get_borrowings():
    """Get all borrowings with member and book details"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT br.*, 
               m.first_name || ' ' || m.last_name as member_name,
               b.title as book_title,
               b.isbn
        FROM borrowings br
        JOIN members m ON br.member_id = m.member_id
        JOIN books b ON br.book_id = b.book_id
        ORDER BY br.borrow_date DESC
    ''')
    
    borrowings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(borrowings),
        "borrowings": borrowings
    })

@app.route('/api/borrowings/overdue')
def get_overdue_borrowings():
    """Get overdue borrowings"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT br.*, 
               m.first_name || ' ' || m.last_name as member_name,
               m.email as member_email,
               b.title as book_title,
               b.isbn,
               JULIANDAY('now') - JULIANDAY(br.due_date) as days_overdue
        FROM borrowings br
        JOIN members m ON br.member_id = m.member_id
        JOIN books b ON br.book_id = b.book_id
        WHERE br.status = 'borrowed' AND br.due_date < DATE('now')
        ORDER BY br.due_date
    ''')
    
    overdue = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        "success": True,
        "count": len(overdue),
        "overdue_borrowings": overdue
    })

@app.route('/api/stats')
def get_stats():
    """Get comprehensive library statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get various statistics
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM books")
    stats['total_books'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM authors")
    stats['total_authors'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM members WHERE status = 'active'")
    stats['total_members'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM borrowings WHERE status = 'borrowed'")
    stats['active_borrowings'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_copies) FROM books")
    stats['total_copies'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(available_copies) FROM books")
    stats['available_copies'] = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    stats['total_categories'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM borrowings WHERE status = 'borrowed' AND due_date < DATE('now')")
    stats['overdue_borrowings'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM borrowings WHERE status = 'returned'")
    stats['total_returns'] = cursor.fetchone()[0]
    
    # Most popular books
    cursor.execute('''
        SELECT b.title, COUNT(br.borrowing_id) as borrow_count
        FROM books b
        JOIN borrowings br ON b.book_id = br.book_id
        GROUP BY b.book_id
        ORDER BY borrow_count DESC
        LIMIT 5
    ''')
    stats['popular_books'] = [{"title": row[0], "borrow_count": row[1]} for row in cursor.fetchall()]
    
    # Most active members
    cursor.execute('''
        SELECT m.first_name || ' ' || m.last_name as name, COUNT(br.borrowing_id) as borrow_count
        FROM members m
        JOIN borrowings br ON m.member_id = br.member_id
        GROUP BY m.member_id
        ORDER BY borrow_count DESC
        LIMIT 5
    ''')
    stats['active_members'] = [{"name": row[0], "borrow_count": row[1]} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        "success": True,
        "stats": stats,
        "generated_at": datetime.now().isoformat()
    })

# DML Operations - Create, Update, Delete
@app.route('/api/members', methods=['POST'])
def create_member():
    """Create a new library member"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT COUNT(*) FROM members WHERE email = ?", (data['email'],))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Email already exists"
            }), 400
        
        # Insert new member
        cursor.execute('''
            INSERT INTO members (first_name, last_name, email, phone, address, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data['first_name'],
            data['last_name'],
            data['email'],
            data.get('phone', ''),
            data.get('address', ''),
            data.get('status', 'active')
        ))
        
        member_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Member created successfully",
            "member_id": member_id
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """Update an existing member"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if member exists
        cursor.execute("SELECT COUNT(*) FROM members WHERE member_id = ?", (member_id,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Member not found"
            }), 404
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        for field in ['first_name', 'last_name', 'email', 'phone', 'address', 'status']:
            if field in data:
                update_fields.append(f"{field} = ?")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({
                "success": False,
                "error": "No fields to update"
            }), 400
        
        values.append(member_id)
        query = f"UPDATE members SET {', '.join(update_fields)} WHERE member_id = ?"
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Member updated successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/borrowings', methods=['POST'])
def create_borrowing():
    """Create a new book borrowing"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['member_id', 'book_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if book is available
        cursor.execute("SELECT available_copies FROM books WHERE book_id = ?", (data['book_id'],))
        result = cursor.fetchone()
        if not result or result[0] <= 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Book not available"
            }), 400
        
        # Check if member exists and is active
        cursor.execute("SELECT status FROM members WHERE member_id = ?", (data['member_id'],))
        result = cursor.fetchone()
        if not result or result[0] != 'active':
            conn.close()
            return jsonify({
                "success": False,
                "error": "Member not found or inactive"
            }), 400
        
        # Calculate due date (30 days from now)
        due_date = (datetime.now() + timedelta(days=30)).date()
        
        # Create borrowing
        cursor.execute('''
            INSERT INTO borrowings (member_id, book_id, borrow_date, due_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            data['member_id'],
            data['book_id'],
            datetime.now().date(),
            due_date,
            'borrowed'
        ))
        
        # Update book availability
        cursor.execute('''
            UPDATE books SET available_copies = available_copies - 1
            WHERE book_id = ?
        ''', (data['book_id'],))
        
        borrowing_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Book borrowed successfully",
            "borrowing_id": borrowing_id,
            "due_date": due_date.isoformat()
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/borrowings/<int:borrowing_id>/return', methods=['PUT'])
def return_book(borrowing_id):
    """Return a borrowed book"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if borrowing exists and is active
        cursor.execute('''
            SELECT book_id, status FROM borrowings 
            WHERE borrowing_id = ?
        ''', (borrowing_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Borrowing not found"
            }), 404
        
        book_id, status = result
        if status != 'borrowed':
            conn.close()
            return jsonify({
                "success": False,
                "error": "Book already returned"
            }), 400
        
        # Update borrowing status
        cursor.execute('''
            UPDATE borrowings 
            SET status = 'returned', return_date = ?
            WHERE borrowing_id = ?
        ''', (datetime.now().date(), borrowing_id))
        
        # Update book availability
        cursor.execute('''
            UPDATE books SET available_copies = available_copies + 1
            WHERE book_id = ?
        ''', (book_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Book returned successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/books', methods=['POST'])
def create_book():
    """Add a new book to the library"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['isbn', 'title', 'publication_year']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if ISBN already exists
        cursor.execute("SELECT COUNT(*) FROM books WHERE isbn = ?", (data['isbn'],))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "ISBN already exists"
            }), 400
        
        # Insert new book
        cursor.execute('''
            INSERT INTO books (isbn, title, publication_year, publisher, total_copies, available_copies, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['isbn'],
            data['title'],
            data['publication_year'],
            data.get('publisher', ''),
            data.get('total_copies', 1),
            data.get('total_copies', 1),  # available_copies = total_copies initially
            data.get('category_id', 1)
        ))
        
        book_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Book added successfully",
            "book_id": book_id
        }), 201
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    """Delete a member (only if no active borrowings)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if member exists
        cursor.execute("SELECT COUNT(*) FROM members WHERE member_id = ?", (member_id,))
        if cursor.fetchone()[0] == 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Member not found"
            }), 404
        
        # Check for active borrowings
        cursor.execute('''
            SELECT COUNT(*) FROM borrowings 
            WHERE member_id = ? AND status = 'borrowed'
        ''', (member_id,))
        
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Cannot delete member with active borrowings"
            }), 400
        
        # Delete member
        cursor.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Member deleted successfully"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
