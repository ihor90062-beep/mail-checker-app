# Overview

This is an Advanced Email & Proxy Checker application built with Flask. The system provides a web-based interface for testing email accounts across multiple protocols (POP3, IMAP, SMTP) and validating proxy servers (HTTP/HTTPS, SOCKS4, SOCKS5). The application supports major email providers like Gmail, Yahoo, Hotmail/Outlook and features batch processing capabilities for testing multiple accounts simultaneously. It includes user authentication, a responsive Bootstrap interface, and real-time progress tracking for long-running validation operations.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 with dark theme support and custom CSS styling
- **JavaScript**: Vanilla JavaScript for form validation, auto-refresh functionality, and interactive features
- **Icons**: Font Awesome for consistent iconography throughout the interface
- **Responsive Design**: Mobile-first approach with Bootstrap grid system

## Backend Architecture
- **Web Framework**: Flask with session-based user authentication
- **Data Storage**: In-memory dictionaries for storing user data, email accounts, proxy servers, and check results
- **Authentication**: Werkzeug password hashing with Flask sessions for user management
- **Email Protocols**: Native Python libraries (smtplib, poplib, imaplib) for email account validation
- **Proxy Testing**: Socket-based connectivity testing for various proxy protocols
- **Concurrency**: Threading module for background processing of batch operations
- **Logging**: Python logging module for debugging and monitoring

## Core Features
- **User Management**: Registration and login system with secure password storage
- **Email Provider Detection**: Automatic configuration for major email providers (Gmail, Yahoo, Outlook)
- **Multi-Protocol Testing**: Support for POP3, IMAP, and SMTP email protocol validation
- **Proxy Validation**: Testing capabilities for HTTP, HTTPS, SOCKS4, and SOCKS5 proxies
- **Batch Processing**: Concurrent checking of multiple email accounts or proxy servers
- **Real-time Progress**: Live status updates and progress tracking for batch operations
- **Dashboard Analytics**: Statistics and overview of checked accounts and servers

## Security Implementation
- **Password Security**: Werkzeug-based password hashing for user credentials
- **Session Management**: Flask sessions with configurable secret key for authentication
- **Input Validation**: Client and server-side validation for email addresses and proxy configurations
- **Error Handling**: Comprehensive exception handling for network operations and user inputs

# External Dependencies

## Python Libraries
- **Flask**: Core web framework for routing, templating, and request handling
- **Werkzeug**: Security utilities for password hashing and authentication
- **smtplib/poplib/imaplib**: Built-in Python libraries for email protocol communication
- **socket**: Low-level network operations for proxy connectivity testing
- **threading**: Concurrent processing support for batch operations
- **logging**: Application monitoring and debugging capabilities

## Frontend Dependencies
- **Bootstrap 5**: UI framework with dark theme variant for responsive design
- **Font Awesome**: Icon library for consistent visual elements
- **Vanilla JavaScript**: Client-side functionality without additional frameworks

## Email Provider Integrations
- **Gmail**: SMTP, IMAP, and POP3 configuration for Google email services
- **Yahoo Mail**: Complete protocol support for Yahoo email accounts
- **Outlook/Hotmail**: Microsoft email service integration with Office365 endpoints

## Network Testing Capabilities
- **HTTP/HTTPS Proxies**: Web proxy validation with connectivity testing
- **SOCKS4/SOCKS5 Proxies**: Socket-based proxy server validation
- **Connection Speed Testing**: Performance metrics for proxy server evaluation