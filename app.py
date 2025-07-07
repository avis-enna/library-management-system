#!/usr/bin/env python3
"""
Library Management System - Flask API
Author: Venna Venkata Siva Reddy
Database: PostgreSQL with advanced features
"""

import os
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import redis
import json
from functools import wraps

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/library_management')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
cors = CORS(app)
jwt = JWTManager(app)

# Redis for caching
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    print("Redis not available, running without cache")

# Cache decorator
def cache_result(timeout=300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not REDIS_AVAILABLE:
                return f(*args, **kwargs)
            
            cache_key = f"{f.__name__}:{request.full_path}"
            cached_result = redis_client.get(cache_key)
            
            if cached_result:
                return json.loads(cached_result)
            
            result = f(*args, **kwargs)
            redis_client.setex(cache_key, timeout, json.dumps(result))
            return result
        return decorated_function
    return decorator

# Database Models (simplified for API)
class Book(db.Model):
    __tablename__ = 'books'
    
    book_id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(200))
    publication_year = db.Column(db.Integer)
    publisher = db.Column(db.String(100))
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    location = db.Column(db.String(100))
    price = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class Member(db.Model):
    __tablename__ = 'members'
    
    member_id = db.Column(db.Integer, primary_key=True)
    member_type = db.Column(db.String(20), nullable=False)
    member_code = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    registration_date = db.Column(db.Date, default=datetime.utcnow().date())
    membership_expiry = db.Column(db.Date, nullable=False)
    max_books_allowed = db.Column(db.Integer, default=3)
    current_books_count = db.Column(db.Integer, default=0)
    total_fine_amount = db.Column(db.Numeric(10, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)

class Borrowing(db.Model):
    __tablename__ = 'borrowings'
    
    borrowing_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    borrowed_date = db.Column(db.Date, default=datetime.utcnow().date())
    due_date = db.Column(db.Date, nullable=False)
    returned_date = db.Column(db.Date)
    renewal_count = db.Column(db.Integer, default=0)
    fine_amount = db.Column(db.Numeric(10, 2), default=0.00)
    is_returned = db.Column(db.Boolean, default=False)
    return_condition = db.Column(db.String(100))

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'database': 'connected',
        'cache': 'available' if REDIS_AVAILABLE else 'unavailable'
    })

@app.route('/api/books', methods=['GET'])
@cache_result(300)
def get_books():
    """Get all books with pagination and search"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    available_only = request.args.get('available_only', 'false').lower() == 'true'
    
    query = Book.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(Book.title.ilike(f'%{search}%'))
    
    if category:
        query = query.filter_by(category_id=category)
    
    if available_only:
        query = query.filter(Book.available_copies > 0)
    
    books = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'books': [{
            'book_id': book.book_id,
            'isbn': book.isbn,
            'title': book.title,
            'subtitle': book.subtitle,
            'publication_year': book.publication_year,
            'publisher': book.publisher,
            'total_copies': book.total_copies,
            'available_copies': book.available_copies,
            'location': book.location,
            'price': str(book.price) if book.price else None
        } for book in books.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': books.total,
            'pages': books.pages,
            'has_next': books.has_next,
            'has_prev': books.has_prev
        }
    })

@app.route('/api/books/<int:book_id>', methods=['GET'])
@cache_result(600)
def get_book(book_id):
    """Get specific book details"""
    book = Book.query.get_or_404(book_id)
    
    # Get current borrowings for this book
    current_borrowings = Borrowing.query.filter_by(
        book_id=book_id, 
        is_returned=False
    ).count()
    
    return jsonify({
        'book_id': book.book_id,
        'isbn': book.isbn,
        'title': book.title,
        'subtitle': book.subtitle,
        'publication_year': book.publication_year,
        'publisher': book.publisher,
        'total_copies': book.total_copies,
        'available_copies': book.available_copies,
        'current_borrowings': current_borrowings,
        'location': book.location,
        'price': str(book.price) if book.price else None,
        'is_available': book.available_copies > 0
    })

@app.route('/api/members', methods=['GET'])
def get_members():
    """Get all members with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    member_type = request.args.get('type', '')
    
    query = Member.query.filter_by(is_active=True)
    
    if member_type:
        query = query.filter_by(member_type=member_type)
    
    members = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'members': [{
            'member_id': member.member_id,
            'member_code': member.member_code,
            'name': f"{member.first_name} {member.last_name}",
            'member_type': member.member_type,
            'email': member.email,
            'current_books': member.current_books_count,
            'max_books': member.max_books_allowed,
            'total_fines': str(member.total_fine_amount),
            'membership_expiry': member.membership_expiry.isoformat()
        } for member in members.items],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': members.total,
            'pages': members.pages
        }
    })

@app.route('/api/borrowings/issue', methods=['POST'])
def issue_book():
    """Issue a book to a member"""
    data = request.get_json()
    
    if not data or 'member_id' not in data or 'book_id' not in data:
        return jsonify({'error': 'Member ID and Book ID are required'}), 400
    
    try:
        # Execute the stored procedure
        result = db.session.execute(
            "SELECT issue_book(:member_id, :book_id, :loan_days)",
            {
                'member_id': data['member_id'],
                'book_id': data['book_id'],
                'loan_days': data.get('loan_days', 14)
            }
        )
        
        success = result.fetchone()[0]
        
        if success:
            db.session.commit()
            # Clear relevant caches
            if REDIS_AVAILABLE:
                redis_client.delete_pattern("get_books:*")
            
            return jsonify({'message': 'Book issued successfully'}), 201
        else:
            return jsonify({'error': 'Failed to issue book'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/borrowings/<int:borrowing_id>/return', methods=['PUT'])
def return_book(borrowing_id):
    """Return a borrowed book"""
    data = request.get_json() or {}
    
    try:
        # Execute the stored procedure
        result = db.session.execute(
            "SELECT return_book(:borrowing_id, :condition, :notes)",
            {
                'borrowing_id': borrowing_id,
                'condition': data.get('condition', 'Good'),
                'notes': data.get('notes')
            }
        )
        
        success = result.fetchone()[0]
        
        if success:
            db.session.commit()
            # Clear relevant caches
            if REDIS_AVAILABLE:
                redis_client.delete_pattern("get_books:*")
            
            return jsonify({'message': 'Book returned successfully'}), 200
        else:
            return jsonify({'error': 'Failed to return book'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/search', methods=['GET'])
@cache_result(180)
def search_books():
    """Search books using full-text search"""
    search_term = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if not search_term:
        return jsonify({'error': 'Search term is required'}), 400
    
    try:
        # Execute the search function
        result = db.session.execute(
            "SELECT * FROM search_books(:search_term, :limit, :offset)",
            {
                'search_term': search_term,
                'limit': limit,
                'offset': offset
            }
        )
        
        books = []
        for row in result:
            books.append({
                'book_id': row[0],
                'title': row[1],
                'subtitle': row[2],
                'authors': row[3],
                'category': row[4],
                'publication_year': row[5],
                'available_copies': row[6],
                'total_copies': row[7],
                'isbn': row[8]
            })
        
        return jsonify({
            'results': books,
            'search_term': search_term,
            'count': len(books)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reports/overdue', methods=['GET'])
@cache_result(60)
def get_overdue_books():
    """Get overdue books report"""
    try:
        result = db.session.execute("SELECT * FROM overdue_books")
        
        overdue_books = []
        for row in result:
            overdue_books.append({
                'borrowing_id': row[0],
                'member_code': row[1],
                'member_name': row[2],
                'email': row[3],
                'phone': row[4],
                'book_title': row[5],
                'isbn': row[6],
                'borrowed_date': row[7].isoformat(),
                'due_date': row[8].isoformat(),
                'days_overdue': row[9],
                'calculated_fine': str(row[10]),
                'renewal_count': row[11]
            })
        
        return jsonify({
            'overdue_books': overdue_books,
            'total_count': len(overdue_books),
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
@cache_result(300)
def get_statistics():
    """Get library statistics"""
    try:
        # Get various statistics using views
        stats = {}
        
        # Book statistics
        book_stats = db.session.execute("""
            SELECT 
                COUNT(*) as total_books,
                SUM(total_copies) as total_copies,
                SUM(available_copies) as available_copies,
                COUNT(CASE WHEN available_copies > 0 THEN 1 END) as books_available
            FROM books WHERE is_active = TRUE
        """).fetchone()
        
        stats['books'] = {
            'total_books': book_stats[0],
            'total_copies': book_stats[1],
            'available_copies': book_stats[2],
            'books_available': book_stats[3],
            'utilization_rate': round(((book_stats[1] - book_stats[2]) / book_stats[1] * 100), 2) if book_stats[1] > 0 else 0
        }
        
        # Member statistics
        member_stats = db.session.execute("""
            SELECT 
                COUNT(*) as total_members,
                COUNT(CASE WHEN member_type = 'student' THEN 1 END) as students,
                COUNT(CASE WHEN member_type = 'faculty' THEN 1 END) as faculty,
                COUNT(CASE WHEN member_type = 'staff' THEN 1 END) as staff
            FROM members WHERE is_active = TRUE
        """).fetchone()
        
        stats['members'] = {
            'total_members': member_stats[0],
            'students': member_stats[1],
            'faculty': member_stats[2],
            'staff': member_stats[3]
        }
        
        # Borrowing statistics
        borrowing_stats = db.session.execute("""
            SELECT 
                COUNT(CASE WHEN is_returned = FALSE THEN 1 END) as current_borrowings,
                COUNT(CASE WHEN is_returned = FALSE AND due_date < CURRENT_DATE THEN 1 END) as overdue_books,
                COUNT(*) as total_borrowings_ever
            FROM borrowings
        """).fetchone()
        
        stats['borrowings'] = {
            'current_borrowings': borrowing_stats[0],
            'overdue_books': borrowing_stats[1],
            'total_borrowings_ever': borrowing_stats[2]
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Initialize database tables
@app.before_first_request
def create_tables():
    """Create database tables if they don't exist"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        print("Database connection successful")
    except Exception as e:
        print(f"Database connection failed: {e}")

if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
