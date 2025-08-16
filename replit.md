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
- **Session Management**: Flask sessions with configurable secret key
- **Authentication**: Username/password authentication with Werkzeug password hashing
- **File Handling**: Secure filename handling for image uploads with BLOB storage
- **Database Layer**: Raw SQLite queries with connection management utilities

### Data Storage
- **Database**: SQLite with two main tables:
  - `usuarios`: User management with hashed passwords
  - `proyectos`: Project storage including BLOB image data
- **Database Initialization**: Automatic table creation on application startup
- **Data Seeding**: Separate seed script for creating initial admin user

### Authentication & Authorization
- **Authentication Method**: Session-based authentication using Flask sessions
- **Password Security**: Werkzeug password hashing for secure credential storage
- **Access Control**: Login required decorators for administrative functions
- **User Management**: Admin-only user creation (no public registration)

### Project Management
- **Image Handling**: Direct BLOB storage in SQLite database
- **File Upload**: Werkzeug secure filename processing
- **CRUD Operations**: Full create, read, update, delete functionality for projects
- **Public Display**: All projects visible to public users without authentication

## External Dependencies

### Python Packages
- **Flask**: Web framework for routing and request handling
- **Werkzeug**: Security utilities for password hashing and file handling
- **SQLite3**: Database connectivity (built-in Python module)

### Frontend Libraries
- **Bootstrap 5.1.3**: CSS framework for responsive design and components
- **Font Awesome 6.0.0**: Icon library for UI enhancement

### Database
- **SQLite**: Embedded database for development and small-scale deployment
- **File Storage**: Local file system storage for the SQLite database file

### Configuration
- **Environment Variables**: SESSION_SECRET for production security
- **Development Mode**: Debug mode enabled for development environment
- **Host Configuration**: Configured for local development (0.0.0.0:5000)