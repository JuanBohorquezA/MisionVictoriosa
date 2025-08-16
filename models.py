# This file contains the database models for the application
# Since we're using raw SQLite queries in app.py, this file serves as documentation
# of the database schema

"""
Database Schema for Misión Victoriosa

Table: usuarios
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- username: TEXT UNIQUE NOT NULL
- password_hash: TEXT NOT NULL

Table: proyectos  
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- titulo: TEXT NOT NULL
- descripcion: TEXT NOT NULL
- imagen: BLOB (stores image binary data)
"""
