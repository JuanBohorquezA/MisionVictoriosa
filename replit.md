# Misión Victoriosa

## Overview

Misión Victoriosa is a Flask-based web application for managing community projects. The platform serves as a public showcase for organizational projects while providing administrative capabilities for authenticated users. The application features a clean, accessible design using a light color palette (yellow and blue tones) and supports full CRUD operations for both projects and users.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 for responsive design
- **Styling**: Custom CSS with CSS variables for consistent theming using the specified light color palette
- **UI Components**: Font Awesome icons for visual enhancement
- **Layout**: Master template (base.html) with section-specific templates extending the base

### Backend Architecture
- **Framework**: Flask web framework with Python
- **Session Management**: Flask sessions with configurable secret key (fallback to development key)
- **Authentication**: Username/password authentication with Werkzeug password hashing
- **File Handling**: Secure filename handling for image uploads with BLOB storage
- **Database Layer**: Flask-SQLAlchemy ORM with PostgreSQL integration
- **Migration**: Fully migrated from SQLite to PostgreSQL for production readiness

### Data Storage
- **Database**: PostgreSQL with three main tables:
  - `usuarios`: User management with hashed passwords
  - `proyectos`: Project storage including BLOB image data
  - `recursos`: Additional project resources (multiple images per project)
- **Database Initialization**: Automatic table creation via SQLAlchemy models
- **Data Seeding**: Automated setup script for database and admin user creation
- **Migration Completed**: August 18, 2025 - Full migration to Replit environment with PostgreSQL
- **Project Cleanup**: August 18, 2025 - Removed test files and cleaned up codebase

### Authentication & Authorization
- **Authentication Method**: Session-based authentication using Flask sessions
- **Password Security**: Werkzeug password hashing for secure credential storage
- **Access Control**: 
  - Login required decorators for administrative functions
  - Admin-only decorators for user management operations
  - Role-based access: Only 'admin' user can manage other users
- **User Management**: Admin-only user creation and management (no public registration)
- **User Roles**: 
  - Admin: Full access to users and projects
  - Regular Users: Project management only

### Project Management
- **Image Handling**: Direct BLOB storage in SQLite database with base64 conversion for display
- **File Upload**: Enhanced drag-and-drop interface with live preview functionality
- **CRUD Operations**: Full create, read, update, delete functionality for projects
- **Public Display**: All projects visible to public users without authentication
- **Enhanced UI**: 
  - Clickable project cards with hover effects
  - Detailed project view with image modal and comprehensive information
  - Enriched project creation form with live preview and drag-and-drop upload
  - Character counter and real-time form validation

## External Dependencies

### Python Packages
- **Flask**: Web framework for routing and request handling
- **Werkzeug**: Security utilities for password hashing and file handling
- **SQLite3**: Database connectivity (built-in Python module)

### Frontend Libraries
- **Bootstrap 5.1.3**: CSS framework for responsive design and components
- **Font Awesome 6.0.0**: Icon library for UI enhancement

### Database
- **PostgreSQL**: Production-ready database with full ACID compliance
- **Replit Integration**: Configured with Replit's PostgreSQL service
- **Environment Variables**: DATABASE_URL, PGPORT, PGUSER, PGPASSWORD, PGDATABASE, PGHOST
- **Migration Status**: Successfully migrated to Replit environment on August 17, 2025
- **Critical Bug Fix**: August 17, 2025 - Fixed image upload validation logic by making file input fields visible instead of hidden with JavaScript dependency

### Configuration
- **Environment Variables**: SESSION_SECRET for production security
- **Development Mode**: Debug mode enabled for development environment
- **Host Configuration**: Configured for local development (0.0.0.0:5000)