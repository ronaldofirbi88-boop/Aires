# Ares Travel - Trip Booking System

## Overview

Ares Travel is a web-based travel booking platform that allows users to browse and book travel packages. The system provides a simple interface for displaying available trips with details like destinations, prices, dates, and available seats. Users can view trip information and make bookings through a web interface.

The application is built as a full-stack solution with a Python FastAPI backend serving both API endpoints and static files, combined with a frontend that presents travel packages in an attractive, responsive design.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: FastAPI (Python) serves as the primary web framework
- **API Design**: RESTful API endpoints for trip management and booking operations
- **Data Models**: Pydantic models for data validation and serialization (Trip, Booking, BookingRequest)
- **CORS Support**: Configured to allow cross-origin requests for frontend-backend communication

### Frontend Architecture
- **Technology**: Vanilla HTML/CSS/JavaScript served as static files
- **3D Globe**: CesiumJS professional 3D globe with realistic lighting and terrain
- **Styling**: CSS Grid/Flexbox with modern responsive design patterns
- **UI Design**: Gradient backgrounds, card-based layouts, and smooth animations
- **Responsive Design**: Mobile-first approach with clamp() functions and viewport-based sizing
- **Internationalization**: Complete i18n support for 4 languages (IT, EN, FR, ES) with localStorage persistence
- **AI Assistant**: Advanced chat interface with Web Speech API integration for voice input/output

### Data Storage
- **Format**: JSON file-based storage system (`data.json`)
- **Structure**: Simple object structure with separate arrays for trips and bookings
- **Persistence**: File I/O operations for reading and writing data
- **Data Models**: 
  - Trips: ID, title, destination, origin, description, price, dates, seat availability, images
  - Bookings: ID, trip reference, customer details, party size, notes, booking date

### File Structure
- **Static Files**: `/public/` directory for frontend assets
- **Data Layer**: JSON file for data persistence
- **Application Logic**: Single `main.py` file containing all backend logic
- **Dependencies**: Minimal requirements focused on FastAPI ecosystem

### Key Design Decisions
- **Simplicity**: File-based storage chosen over database for ease of deployment and maintenance
- **Monolithic Structure**: Single backend file keeps the application simple and self-contained
- **Static File Serving**: FastAPI serves both API and static content, reducing deployment complexity
- **Image Integration**: External image URLs (Unsplash) for travel photos without local storage requirements

## External Dependencies

### Python Packages
- **FastAPI**: Web framework for API development and static file serving
- **Uvicorn**: ASGI server for running the FastAPI application
- **Python-multipart**: Form data handling for booking submissions
- **Pydantic**: Built into FastAPI for data validation and serialization

### External Services
- **Unsplash**: Image hosting service for travel destination photos
- **No Database**: Uses local JSON file storage instead of external database services
- **No Authentication Services**: Simple booking system without user accounts or authentication

### Browser APIs
- **Fetch API**: For frontend-backend communication
- **CSS Grid/Flexbox**: Modern layout technologies for responsive design
- **CSS Animations**: Native CSS animations for enhanced user experience