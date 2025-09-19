# 🚀 Quick Start Deployment Guide

## Prerequisites Checklist
- [ ] VPS with Ubuntu 20.04+ (2GB RAM minimum)
- [ ] Domain name (optional but recommended)
- [ ] GitHub account
- [ ] Docker Hub account

## 1. GitHub Setup (5 minutes)

### Create Repository
```bash
git init
git add .
git commit -m "Initial commit"
# Create repo on GitHub, then:
git remote add origin https://github.com/YOURUSERNAME/drycleanershop.git
git push -u origin main
```

### Add GitHub Secrets
Repository → Settings → Secrets → Actions:
```
DOCKER_USERNAME: your_dockerhub_username
DOCKER_PASSWORD: your_dockerhub_password_or_token
VPS_HOST: your_vps_ip_address
VPS_USERNAME: root (or ubuntu)
VPS_SSH_KEY: (see SSH setup below)
```

### SSH Key Setup
```bash
# Generate key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/github_actions

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/github_actions.pub root@YOUR_VPS_IP

# Copy private key content to GitHub secret
cat ~/.ssh/github_actions
```

## 2. VPS Setup (10 minutes)

### Connect and Install Docker
```bash
ssh root@YOUR_VPS_IP

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl start docker && systemctl enable docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### Setup Application
```bash
# Create directory
mkdir -p /opt/drycleanershop && cd /opt/drycleanershop

# Clone repository
git clone https://github.com/YOURUSERNAME/drycleanershop.git .

# Setup environment
cp .env.production.example .env.production
```

### Configure Environment
```bash
# Generate secret key
python3 -c "import secrets; print(secrets.token_urlsafe(50))"

# Edit production config
nano .env.production
```

**Update these values:**
- `SECRET_KEY`: Use generated key above
- `ALLOWED_HOSTS`: Add your domain/IP
- `DB_PASSWORD`: Strong password (20+ chars)
- `DB_ROOT_PASSWORD`: Strong password (20+ chars)
- `CORS_ALLOWED_ORIGINS`: Your domain with https://

## 3. SSL Setup (5 minutes)

### Get Let's Encrypt Certificate
```bash
# Install certbot
snap install --classic certbot

# Get certificate (replace YOUR_DOMAIN)
certbot certonly --standalone -d YOUR_DOMAIN.com

# Copy certificates
mkdir -p /opt/drycleanershop/ssl
cp /etc/letsencrypt/live/YOUR_DOMAIN.com/fullchain.pem /opt/drycleanershop/ssl/cert.pem
cp /etc/letsencrypt/live/YOUR_DOMAIN.com/privkey.pem /opt/drycleanershop/ssl/key.pem

# Auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### Update Nginx Config
```bash
# Edit nginx.conf
nano nginx.conf
# Replace 'your-domain.com' with your actual domain
```

## 4. Initial Deployment (5 minutes)

### Manual First Deploy
```bash
cd /opt/drycleanershop

# Copy production environment
cp .env.production .env

# Start services
docker-compose up -d

# Wait for services to start
sleep 30

# Run migrations
docker-compose exec web python app/manage.py migrate

# Create superuser
docker-compose exec web python app/manage.py createsuperuser

# Collect static files
docker-compose exec web python app/manage.py collectstatic --noinput
```

### Verify Deployment
```bash
# Check containers
docker-compose ps

# Test API
curl https://YOUR_DOMAIN.com/api/auth/login/

# Check logs if issues
docker-compose logs web
```

## 5. Automatic Deployment

**That's it!** Now every push to `main` branch automatically deploys:

```bash
# Make changes
git add .
git commit -m "My changes"
git push origin main

# GitHub Actions will automatically:
# 1. Run tests
# 2. Build Docker image
# 3. Deploy to VPS
# 4. Run health checks
```

## 🎯 Access Your Application

- **API**: `https://YOUR_DOMAIN.com/api/`
- **Admin**: `https://YOUR_DOMAIN.com/admin/`
- **API Docs**: See `API_DOCUMENTATION.md`

## 🔧 Quick Commands

```bash
# View logs
docker-compose logs -f web

# Restart application
docker-compose restart web

# Update containers
docker-compose pull && docker-compose up -d

# Database backup
docker-compose exec db mysqldump -u root -p dryCleanShop > backup.sql

# Clean up
docker system prune -f
```

## 🚨 Troubleshooting

**GitHub Actions fails?**
- Check secrets are correctly set
- Verify SSH key works: `ssh -i ~/.ssh/github_actions root@YOUR_VPS_IP`

**Application not starting?**
- Check logs: `docker-compose logs web`
- Verify environment variables in `.env`

**Database issues?**
- Check DB logs: `docker-compose logs db`
- Verify passwords match in environment

**SSL issues?**
- Verify domain points to VPS IP
- Check certificate paths in nginx.conf
- Restart nginx: `docker-compose restart nginx`

## ⏱️ Total Setup Time: ~25 minutes

You're now running a production-ready Django API with automatic deployments! 🎉