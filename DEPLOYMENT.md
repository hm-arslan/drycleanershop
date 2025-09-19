# Deployment Guide - Dry Cleaner Shop API

This guide covers the complete deployment workflow from GitHub to your VPS using Docker and GitHub Actions.

## 🏗️ Architecture Overview

```
GitHub Repository → GitHub Actions CI/CD → Docker Hub → VPS → Production
```

**Components:**
- **Django App**: Dockerized application
- **MySQL Database**: Containerized database
- **Nginx**: Reverse proxy and load balancer
- **GitHub Actions**: CI/CD pipeline
- **Docker Hub**: Container registry

## 📋 Prerequisites

### Local Development
- Docker and Docker Compose installed
- Python 3.12+
- Git

### VPS Requirements
- Ubuntu 20.04+ or CentOS 8+
- Minimum 2GB RAM, 20GB storage
- Docker and Docker Compose installed
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt recommended)

### Accounts Needed
- GitHub account
- Docker Hub account
- VPS provider (DigitalOcean, AWS, Linode, etc.)

## 🚀 Step-by-Step Deployment

### 1. Prepare GitHub Repository

#### Create Repository
```bash
# Initialize git in your project
git init
git add .
git commit -m "Initial commit"

# Create repository on GitHub (via web interface)
# Then add remote and push
git remote add origin https://github.com/yourusername/drycleanershop.git
git branch -M main
git push -u origin main
```

#### Set up GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:
```
DOCKER_USERNAME=your_dockerhub_username
DOCKER_PASSWORD=your_dockerhub_password
VPS_HOST=your_vps_ip_address
VPS_USERNAME=your_vps_username
VPS_SSH_KEY=your_private_ssh_key_content
```

### 2. Set Up VPS

#### Install Docker and Docker Compose
```bash
# Connect to your VPS
ssh root@your_vps_ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start Docker service
systemctl start docker
systemctl enable docker

# Add user to docker group (optional)
usermod -aG docker $USER
```

#### Create Application Directory
```bash
# Create application directory
mkdir -p /opt/drycleanershop
cd /opt/drycleanershop

# Clone your repository
git clone https://github.com/yourusername/drycleanershop.git .

# Set up environment file for production
cp .env.example .env.production
```

#### Configure Production Environment
Edit `/opt/drycleanershop/.env.production`:
```bash
# Generate a strong secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Edit the file
nano .env.production
```

Update these values:
```env
DEBUG=False
SECRET_KEY=your_generated_secret_key_here
ALLOWED_HOSTS=your-domain.com,your-vps-ip,localhost,127.0.0.1
DB_PASSWORD=strong_database_password
DB_ROOT_PASSWORD=strong_root_password
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

#### Set Up SSL Certificate (Let's Encrypt)
```bash
# Install certbot
apt install snapd
snap install core; snap refresh core
snap install --classic certbot

# Generate certificate
certbot certonly --standalone -d your-domain.com

# Create SSL directory and copy certificates
mkdir -p /opt/drycleanershop/ssl
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/drycleanershop/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/drycleanershop/ssl/key.pem

# Set up automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

#### Update Nginx Configuration
Edit `/opt/drycleanershop/nginx.conf` and replace `your-domain.com` with your actual domain.

### 3. Configure GitHub Actions

The GitHub Actions workflow is already set up in `.github/workflows/deploy.yml`. It will:

1. **Test Phase**: Run tests on every push/PR
2. **Build Phase**: Build and push Docker image to Docker Hub
3. **Deploy Phase**: Deploy to VPS (only on main branch)
4. **Health Check**: Verify deployment success

### 4. Initial Deployment

#### Manual First Deployment
```bash
# On your VPS
cd /opt/drycleanershop

# Copy production environment
cp .env.production .env

# Build and start containers
docker-compose up -d

# Run initial migrations
docker-compose exec web python app/manage.py migrate

# Create superuser
docker-compose exec web python app/manage.py createsuperuser

# Collect static files
docker-compose exec web python app/manage.py collectstatic --noinput

# Check container status
docker-compose ps
```

#### Verify Deployment
```bash
# Check if API is responding
curl -k https://your-domain.com/api/auth/login/

# Check container logs
docker-compose logs web
docker-compose logs nginx
docker-compose logs db
```

### 5. Automated Deployment

After the initial setup, every push to the `main` branch will trigger automatic deployment:

1. Push code to GitHub
2. GitHub Actions runs tests
3. If tests pass, builds Docker image
4. Pushes image to Docker Hub
5. Connects to VPS and deploys
6. Runs health checks

```bash
# Make changes to your code
git add .
git commit -m "Your changes"
git push origin main

# GitHub Actions will automatically deploy!
```

## 🔧 Environment Variables Guide

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generate with Django utils |
| `DEBUG` | Debug mode | `False` for production |
| `ALLOWED_HOSTS` | Allowed hosts | `your-domain.com,127.0.0.1` |
| `DB_NAME` | Database name | `dryCleanShop` |
| `DB_USER` | Database user | `dryclean_user` |
| `DB_PASSWORD` | Database password | Strong password |
| `DB_HOST` | Database host | `db` (for Docker) |
| `DB_ROOT_PASSWORD` | MySQL root password | Strong password |

### GitHub Secrets

| Secret | Description | How to Get |
|--------|-------------|------------|
| `DOCKER_USERNAME` | Docker Hub username | Your Docker Hub account |
| `DOCKER_PASSWORD` | Docker Hub password/token | Docker Hub access token |
| `VPS_HOST` | VPS IP address | Your VPS provider |
| `VPS_USERNAME` | VPS username | Usually `root` or `ubuntu` |
| `VPS_SSH_KEY` | Private SSH key | Generate with `ssh-keygen` |

### Setting Up SSH Key

```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -C "github-actions"

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/id_rsa.pub user@your_vps_ip

# Copy private key content to GitHub secret VPS_SSH_KEY
cat ~/.ssh/id_rsa
```

## 🔍 Monitoring and Maintenance

### Viewing Logs
```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# Nginx logs
docker-compose logs -f nginx

# All logs
docker-compose logs -f
```

### Database Backup
```bash
# Create backup
docker-compose exec db mysqldump -u root -p dryCleanShop > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T db mysql -u root -p dryCleanShop < backup_file.sql
```

### Updates and Maintenance
```bash
# Update application (automatic via GitHub Actions)
git push origin main

# Manual update containers
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f

# Check disk space
df -h
docker system df
```

### SSL Certificate Renewal
```bash
# Check certificate status
certbot certificates

# Manual renewal (usually automatic)
certbot renew

# Update certificates in Docker
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/drycleanershop/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/drycleanershop/ssl/key.pem
docker-compose restart nginx
```

## 🚨 Troubleshooting

### Common Issues

#### 1. GitHub Actions Deployment Fails
```bash
# Check GitHub Actions logs
# Common causes:
# - Wrong VPS credentials
# - VPS not accessible
# - Docker Hub credentials incorrect

# Test SSH connection manually
ssh -i your_private_key user@vps_ip
```

#### 2. Application Not Starting
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs web

# Common causes:
# - Environment variables missing
# - Database connection issues
# - Port conflicts
```

#### 3. Database Connection Issues
```bash
# Check database container
docker-compose logs db

# Test database connection
docker-compose exec web python app/manage.py dbshell

# Reset database (careful!)
docker-compose down -v
docker-compose up -d
```

#### 4. SSL/Nginx Issues
```bash
# Check nginx logs
docker-compose logs nginx

# Test nginx configuration
docker-compose exec nginx nginx -t

# Reload nginx
docker-compose restart nginx
```

### Performance Optimization

#### 1. Database Optimization
```bash
# Add to docker-compose.yml under db service environment:
MYSQL_INNODB_BUFFER_POOL_SIZE=512M
MYSQL_INNODB_LOG_FILE_SIZE=128M
```

#### 2. Application Scaling
```bash
# Scale web containers
docker-compose up -d --scale web=3

# Update nginx.conf to use all containers
upstream django {
    server web_1:8000;
    server web_2:8000;
    server web_3:8000;
}
```

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

## 🔒 Security Best Practices

1. **Keep secrets secure**: Never commit sensitive data to git
2. **Use strong passwords**: Generate random passwords for all services
3. **Keep systems updated**: Regularly update VPS and containers
4. **Monitor logs**: Set up log monitoring and alerts
5. **Backup regularly**: Automate database and file backups
6. **Use HTTPS**: Always use SSL certificates in production
7. **Firewall**: Configure UFW or iptables to limit access
8. **Fail2ban**: Install fail2ban to prevent brute force attacks

---

## 🎉 You're Ready to Deploy!

Follow these steps and your Django application will be automatically deployed to your VPS every time you push to the main branch!