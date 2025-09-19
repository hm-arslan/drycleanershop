# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django REST API for a dry cleaning shop management system. The application manages multiple dry cleaning shops, their services, items, pricing, and user accounts with role-based access control.

## Development Commands

### Environment Setup
- Activate virtual environment: `source env/bin/activate`
- Install dependencies: `pip install -r requirements.txt` (if requirements.txt exists)

### Database Operations
- Run migrations: `python app/manage.py migrate`
- Create migrations: `python app/manage.py makemigrations`
- Create superuser: `python app/manage.py createsuperuser`

### Development Server
- Start development server: `python app/manage.py runserver`
- Admin interface: Available at `/admin/` when server is running

### Testing
- Run tests: `python app/manage.py test`
- Run specific app tests: `python app/manage.py test <app_name>`

## Architecture

### Database Configuration
- Uses MySQL database (`dryCleanShop`)
- Database settings in `app/settings.py:87-99`
- Custom User model defined in `accounts.User`

### API Structure
All API endpoints are prefixed with `/api/`:
- `/api/auth/` - Authentication endpoints (accounts app)
- `/api/shop/` - Shop management (shops app)
- `/api/services/` - Service management (services app)
- `/api/items/` - Item and pricing management (items app)

### Core Models Relationships
1. **User** (accounts) - Custom user model with roles (admin, staff, customer)
2. **Shop** (shops) - Each shop has one owner (User), OneToOne relationship
3. **Service** (services) - Services belong to shops, unique per shop
4. **Item** (items) - Items belong to shops, unique per shop
5. **ServicePrice** (items) - Junction model linking Service + Item + Price per shop

### Authentication
- JWT authentication using `djangorestframework-simplejwt`
- Token blacklisting enabled for logout functionality
- Access tokens: 12 hours, Refresh tokens: 7 days
- Refresh token rotation enabled

### Django Apps Structure
Each app follows standard Django structure:
- `models.py` - Data models
- `views.py` - API views  
- `serializers.py` - DRF serializers
- `urls.py` - URL routing
- `admin.py` - Django admin configuration
- `tests.py` - Test cases

## Key Files
- `app/manage.py` - Django management script
- `app/app/settings.py` - Main settings file
- `app/app/urls.py` - Root URL configuration