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
    ('Business', 'Business and management books');

    INSERT OR IGNORE INTO authors (first_name, last_name, nationality) VALUES
    ('Robert', 'Martin', 'American'),
    ('Eric', 'Evans', 'American'),
    ('Martin', 'Fowler', 'British'),
    ('Gang of Four', 'Authors', 'Various');

    INSERT OR IGNORE INTO books (isbn, title, publication_year, publisher, total_copies, available_copies, category_id) VALUES
    ('9780132350884', 'Clean Code', 2008, 'Prentice Hall', 5, 3, 1),
    ('9780321125217', 'Domain-Driven Design', 2003, 'Addison-Wesley', 3, 2, 1),
    ('9780201633610', 'Design Patterns', 1994, 'Addison-Wesley', 4, 4, 1),
    ('9780134685991', 'Effective Java', 2017, 'Addison-Wesley', 6, 5, 1);

    INSERT OR IGNORE INTO book_authors (book_id, author_id) VALUES
    (1, 1), (2, 2), (3, 4), (4, 3);

    INSERT OR IGNORE INTO members (first_name, last_name, email, phone, address) VALUES
    ('John', 'Doe', 'john.doe@email.com', '+1-555-0101', '123 Main St'),
    ('Jane', 'Smith', 'jane.smith@email.com', '+1-555-0102', '456 Oak Ave'),
    ('Mike', 'Johnson', 'mike.j@email.com', '+1-555-0103', '789 Pine Rd');

    INSERT OR IGNORE INTO borrowings (member_id, book_id, borrow_date, due_date, status) VALUES
    (1, 1, '2025-06-01', '2025-07-01', 'borrowed'),
    (2, 2, '2025-06-15', '2025-07-15', 'borrowed');
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
            <h2>📊 Database Statistics</h2>
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
                <span class="endpoint">/api/authors</span>
                <div class="description">Get all authors</div>
                <button class="try-button" onclick="tryEndpoint('/api/authors')">Try It</button>
                <div id="result-authors" class="result-box" style="display:none;"></div>
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
                <span class="endpoint">/api/stats</span>
                <div class="description">Get library statistics</div>
                <button class="try-button" onclick="tryEndpoint('/api/stats')">Try It</button>
                <div id="result-stats" class="result-box" style="display:none;"></div>
            </div>
        </div>

        <div class="demo-section">
            <h2>🔧 Technical Features Demonstrated</h2>
            <ul style="line-height: 2;">
                <li><strong>Database Design:</strong> Normalized schema with proper relationships</li>
                <li><strong>RESTful API:</strong> Clean, organized endpoints</li>
                <li><strong>Data Validation:</strong> Input validation and error handling</li>
                <li><strong>Query Optimization:</strong> Efficient database queries</li>
                <li><strong>Documentation:</strong> Self-documenting API interface</li>
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

        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
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

@app.route('/api/stats')
def get_stats():
    """Get library statistics"""
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
    
    conn.close()
    
    return jsonify({
        "success": True,
        "stats": stats,
        "generated_at": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
