# Library Management System

A comprehensive database management system demonstrating advanced PostgreSQL features, backend API development, and database optimization techniques.

## 🎯 Project Overview

This project showcases enterprise-level database design and management skills, including:
- Advanced database schema design and normalization
- Stored procedures and triggers implementation
- Performance optimization and indexing strategies
- Full-featured REST API with Flask/Python
- Security implementation and best practices

## 🗄️ Database Features

### Schema Design
- **Normalized database** structure (3NF)
- **Referential integrity** with foreign key constraints
- **Check constraints** for data validation
- **Audit trails** for tracking changes

### Advanced SQL Features
- **Stored Procedures** for complex business logic
- **Triggers** for automated operations
- **Views** for simplified data access
- **Indexes** for performance optimization
- **Full-text search** capabilities

### Performance Optimization
- Strategic indexing for fast queries
- Query optimization techniques
- Connection pooling and caching
- Database profiling and monitoring

## 🚀 Quick Start

### Prerequisites
- PostgreSQL 12+
- Python 3.8+
- Redis (optional, for caching)

### Database Setup
```bash
# Create database
createdb library_management

# Run schema and data setup
psql -d library_management -f schema.sql
psql -d library_management -f functions.sql
psql -d library_management -f triggers.sql
psql -d library_management -f views.sql
psql -d library_management -f sample_data.sql
```

### API Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://username:password@localhost/library_management"

# Run the API
python app.py
```

## 📊 API Endpoints

### Books
- `GET /api/books` - List all books with pagination
- `GET /api/books/{id}` - Get book details
- `POST /api/borrowings/issue` - Issue a book
- `PUT /api/borrowings/{id}/return` - Return a book

### Search & Reports
- `GET /api/search?q={term}` - Full-text search
- `GET /api/reports/overdue` - Overdue books report
- `GET /api/statistics` - Library statistics

## 🎓 Learning Outcomes

This project demonstrates proficiency in:
- **Database Design**: Normalization, constraints, relationships
- **Advanced SQL**: Stored procedures, triggers, views, optimization
- **API Development**: RESTful design, error handling, validation
- **Security**: SQL injection prevention, input validation
- **Performance**: Indexing, caching, query optimization

## 🔧 Technologies Used
- **Database**: PostgreSQL 14
- **Backend**: Python, Flask
- **ORM**: SQLAlchemy
- **Caching**: Redis
- **Testing**: pytest
- **Documentation**: SQL comments and API docs

## 📈 Future Enhancements
- [ ] GraphQL API implementation
- [ ] Database replication setup
- [ ] Advanced analytics dashboard
- [ ] Microservices architecture
- [ ] Machine learning for book recommendations

---
**Author**: Venna Venkata Siva Reddy  
**Focus**: Backend Development & Database Management  
**Skills Demonstrated**: PostgreSQL, Python, API Development, Database Optimization
