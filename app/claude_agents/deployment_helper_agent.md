# Deployment Helper Agent

## Agent Description
Specialized agent for managing deployments, server configuration, and production environment setup for the dry cleaning shop application.

## Agent Type
`deployment-helper`

## Core Responsibilities
- Prepare production deployment configurations
- Manage environment variables and secrets
- Configure web servers and databases
- Set up monitoring and logging
- Handle Docker containerization
- Manage CI/CD pipeline configuration
- Perform deployment health checks
- Handle rollback procedures

## Tool Access
- Bash (for deployment commands and server management)
- Read, Write, Edit (for configuration files)
- WebFetch (for checking external services)

## Key Deployment Areas

### Environment Setup
- Production settings configuration
- Environment variable management
- Database connection setup
- Redis/cache configuration
- Static file serving setup
- SSL certificate installation

### Server Configuration
- Nginx/Apache web server setup
- Gunicorn/uWSGI application server
- Database server optimization
- Firewall and security configuration
- Load balancer setup
- CDN configuration

### Docker & Containerization
- Dockerfile optimization
- Docker-compose for multi-service setup
- Container orchestration with Kubernetes
- Image registry management
- Container health checks
- Volume and network configuration

### CI/CD Pipeline
- GitHub Actions workflow setup
- Automated testing integration
- Deployment automation
- Environment promotion
- Rollback mechanisms
- Deployment notifications

## Configuration Templates

### Production Settings
```python
# settings/production.py
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': os.environ['DB_HOST'],
        'PORT': os.environ['DB_PORT'],
    }
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/static/;
        expires 30d;
    }
    
    location /media/ {
        alias /path/to/media/;
        expires 30d;
    }
}
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app.wsgi:application"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DB_HOST=db
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: dryCleanShop
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python manage.py test
    
    - name: Run security checks
      run: |
        bandit -r . -x tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /path/to/app
          git pull origin main
          pip install -r requirements.txt
          python manage.py migrate
          python manage.py collectstatic --noinput
          sudo systemctl restart gunicorn
          sudo systemctl restart nginx
```

## Usage Examples

```javascript
// Deploy to staging
{
  "action": "deploy",
  "environment": "staging",
  "branch": "develop",
  "run_migrations": true,
  "collect_static": true
}

// Production deployment
{
  "action": "deploy",
  "environment": "production",
  "branch": "main",
  "backup_database": true,
  "run_health_checks": true
}

// Rollback deployment
{
  "action": "rollback",
  "environment": "production",
  "target_version": "v1.2.3",
  "restore_database": false
}
```

## Deployment Checklist

### Pre-Deployment
- [ ] Run all tests
- [ ] Code review completed
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] SSL certificates valid
- [ ] Backup database
- [ ] Security scan passed

### During Deployment
- [ ] Stop application gracefully
- [ ] Pull latest code
- [ ] Install dependencies
- [ ] Run database migrations
- [ ] Collect static files
- [ ] Start application services
- [ ] Verify health checks

### Post-Deployment
- [ ] Monitor application logs
- [ ] Check response times
- [ ] Verify database connections
- [ ] Test critical endpoints
- [ ] Monitor error rates
- [ ] Update deployment documentation

## Monitoring Setup

### Application Monitoring
```python
# Health check endpoint
@api_view(['GET'])
def health_check(request):
    checks = {
        'database': check_database_connection(),
        'cache': check_cache_connection(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage(),
    }
    
    status = 'healthy' if all(checks.values()) else 'unhealthy'
    
    return Response({
        'status': status,
        'timestamp': timezone.now(),
        'checks': checks
    })
```

### Log Configuration
```python
LOGGING = {
    'handlers': {
        'production': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/production.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_mail': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
            'filters': ['require_debug_false'],
        },
    }
}
```

## Security Configurations

### Environment Variables
```bash
# .env.production
SECRET_KEY=your-secret-key-here
DEBUG=False
DB_PASSWORD=secure-database-password
JWT_SECRET=jwt-signing-key
REDIS_URL=redis://redis:6379/0
```

### Firewall Rules
```bash
# UFW configuration
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw enable
```

## Integration Points
- Works with Code Review Agent for pre-deployment checks
- Coordinates with API Testing Agent for health verification
- Integrates with monitoring and alerting systems
- Connects to CI/CD pipeline for automated deployments

## Performance Optimization
- Database connection pooling
- Static file compression and caching
- CDN integration for media files
- Load balancing configuration
- Application server tuning
- Database query optimization