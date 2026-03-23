# Hostinger VPS Deployment Guide

Complete guide for deploying the Chef Candidate Evaluation Platform on a Hostinger VPS.

## Prerequisites

- Hostinger VPS with Ubuntu 22.04+ (recommended: 4GB RAM, 2 CPU cores, 80GB SSD)
- Domain name pointed to VPS IP address
- SSH access to VPS
- Root or sudo privileges

---

## Step 1: Initial VPS Setup

### 1.1 Connect to VPS

```bash
ssh root@your-vps-ip
```

### 1.2 Update System

```bash
apt update && apt upgrade -y
```

### 1.3 Create Application User

```bash
adduser chef-eval
usermod -aG sudo chef-eval
su - chef-eval
```

---

## Step 2: Install Dependencies

### 2.1 Install Python 3.11+

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
```

### 2.2 Install Node.js 20+

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2.3 Install PostgreSQL 15

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2.4 Install Redis

```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2.5 Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Step 3: Configure PostgreSQL

### 3.1 Create Database and User

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE chef_candidates;
CREATE USER chef_eval_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE chef_candidates TO chef_eval_user;
\q
```

### 3.2 Test Connection

```bash
psql -h localhost -U chef_eval_user -d chef_candidates
```

---

## Step 4: Upload Application Files

### 4.1 Create Application Directory

```bash
sudo mkdir -p /var/www/chef-eval
sudo chown chef-eval:chef-eval /var/www/chef-eval
cd /var/www/chef-eval
```

### 4.2 Upload Files via SFTP

**From your local machine:**

```bash
# Upload entire project
scp -r /path/to/Test-Kitchen-Website/* chef-eval@your-vps-ip:/var/www/chef-eval/

# Or use an SFTP client like FileZilla
# Host: your-vps-ip
# Username: chef-eval
# Password: your_password
# Remote directory: /var/www/chef-eval
```

**Verify upload:**

```bash
ls -la /var/www/chef-eval
# Should see: backend/, frontend/, docker-compose.yml, README.md, etc.
```

---

## Step 5: Configure Backend

### 5.1 Set Up Python Environment

```bash
cd /var/www/chef-eval/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5.2 Create Environment File

```bash
cp .env.example .env
nano .env
```

**Edit `.env` with your configuration:**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://chef_eval_user:your_secure_password_here@localhost:5432/chef_candidates

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage (Local Filesystem)
STORAGE_TYPE=local
STORAGE_BASE_PATH=/var/www/chef-candidate-media
STORAGE_BASE_URL=https://yourdomain.com/media

# AssemblyAI
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

# JWT
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256

# Application
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 5.3 Create Storage Directory

```bash
sudo mkdir -p /var/www/chef-candidate-media/{videos,documents,photos,transcripts}
sudo chown -R chef-eval:www-data /var/www/chef-candidate-media
sudo chmod -R 775 /var/www/chef-candidate-media
```

### 5.4 Run Database Migrations

```bash
cd /var/www/chef-eval/backend
source .venv/bin/activate
alembic upgrade head
```

### 5.5 Test Backend

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
# Visit http://your-vps-ip:8000/health
# Should see: {"status": "healthy", ...}
# Ctrl+C to stop
```

---

## Step 6: Configure Frontend

### 6.1 Install Dependencies

```bash
cd /var/www/chef-eval/frontend
npm install
```

### 6.2 Create Environment File

```bash
cp .env.example .env.local
nano .env.local
```

**Edit `.env.local`:**

```bash
NEXT_PUBLIC_API_URL=https://yourdomain.com/api/v1
NEXT_PUBLIC_S3_BUCKET_URL=https://yourdomain.com/media
NEXT_PUBLIC_APP_NAME="Chef Candidate Evaluation Platform"
```

### 6.3 Build Frontend

```bash
npm run build
```

---

## Step 7: Configure Systemd Services

### 7.1 Create Backend Service

```bash
sudo nano /etc/systemd/system/chef-eval-backend.service
```

```ini
[Unit]
Description=Chef Evaluation Backend (FastAPI)
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=chef-eval
WorkingDirectory=/var/www/chef-eval/backend
Environment="PATH=/var/www/chef-eval/backend/.venv/bin"
ExecStart=/var/www/chef-eval/backend/.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7.2 Create Worker Service (for transcription jobs)

```bash
sudo nano /etc/systemd/system/chef-eval-worker.service
```

```ini
[Unit]
Description=Chef Evaluation Worker (ARQ)
After=network.target redis.service

[Service]
Type=simple
User=chef-eval
WorkingDirectory=/var/www/chef-eval/backend
Environment="PATH=/var/www/chef-eval/backend/.venv/bin"
ExecStart=/var/www/chef-eval/backend/.venv/bin/arq src.workers.transcription_worker.WorkerSettings
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7.3 Create Frontend Service

```bash
sudo nano /etc/systemd/system/chef-eval-frontend.service
```

```ini
[Unit]
Description=Chef Evaluation Frontend (Next.js)
After=network.target

[Service]
Type=simple
User=chef-eval
WorkingDirectory=/var/www/chef-eval/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm run start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7.4 Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable chef-eval-backend chef-eval-worker chef-eval-frontend
sudo systemctl start chef-eval-backend chef-eval-worker chef-eval-frontend
```

### 7.5 Check Service Status

```bash
sudo systemctl status chef-eval-backend
sudo systemctl status chef-eval-worker
sudo systemctl status chef-eval-frontend
```

---

## Step 8: Configure Nginx

### 8.1 Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/chef-eval
```

```nginx
# Chef Candidate Evaluation Platform Nginx Configuration

upstream backend {
    server 127.0.0.1:8000;
}

upstream frontend {
    server 127.0.0.1:3000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (will be updated by Certbot)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size (100MB for videos)
    client_max_body_size 100M;

    # Backend API
    location /api {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts for long uploads
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
    }

    # Media files (serve directly from filesystem)
    location /media {
        alias /var/www/chef-candidate-media;
        expires 1y;
        add_header Cache-Control "public, immutable";

        # Security: Prevent directory listing
        autoindex off;
    }

    # Frontend (Next.js)
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 8.2 Enable Site and Test Configuration

```bash
sudo ln -s /etc/nginx/sites-available/chef-eval /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 9: Install SSL Certificate (Let's Encrypt)

### 9.1 Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 9.2 Obtain SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow prompts to:
- Enter email address
- Agree to terms
- Choose whether to redirect HTTP to HTTPS (recommended: yes)

### 9.3 Auto-Renewal

Certbot automatically sets up renewal. Test it:

```bash
sudo certbot renew --dry-run
```

---

## Step 10: Firewall Configuration

### 10.1 Configure UFW

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

---

## Step 11: Verify Deployment

### 11.1 Check Services

```bash
sudo systemctl status chef-eval-backend
sudo systemctl status chef-eval-worker
sudo systemctl status chef-eval-frontend
sudo systemctl status nginx
```

### 11.2 Access Application

Visit: **https://yourdomain.com**

Test:
- ✅ Homepage loads
- ✅ Candidate signup page
- ✅ Admin login page
- ✅ Backend API docs: https://yourdomain.com/api/docs (if DEBUG=true)
- ✅ Health check: https://yourdomain.com/api/health

---

## Maintenance & Updates

### Updating Application

```bash
# 1. Upload new files via SFTP to /var/www/chef-eval

# 2. Update backend
cd /var/www/chef-eval/backend
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart chef-eval-backend chef-eval-worker

# 3. Update frontend
cd /var/www/chef-eval/frontend
npm install
npm run build
sudo systemctl restart chef-eval-frontend
```

### View Logs

```bash
# Backend logs
sudo journalctl -u chef-eval-backend -f

# Worker logs
sudo journalctl -u chef-eval-worker -f

# Frontend logs
sudo journalctl -u chef-eval-frontend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup Database

```bash
# Create backup
sudo -u postgres pg_dump chef_candidates > ~/backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql chef_candidates < ~/backup_20250113.sql
```

### Backup Media Files

```bash
# Create backup
sudo tar -czf ~/media_backup_$(date +%Y%m%d).tar.gz /var/www/chef-candidate-media

# Restore backup
sudo tar -xzf ~/media_backup_20250113.tar.gz -C /
```

---

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
sudo journalctl -u chef-eval-backend -n 50

# Common issues:
# - Database connection error: Check DATABASE_URL in .env
# - Storage path error: Ensure /var/www/chef-candidate-media exists and has correct permissions
```

### Frontend Not Starting

```bash
# Check logs
sudo journalctl -u chef-eval-frontend -n 50

# Common issues:
# - Build failed: Run npm run build manually to see errors
# - Port 3000 in use: Check if another process is using port 3000
```

### 502 Bad Gateway

```bash
# Check if backend/frontend services are running
sudo systemctl status chef-eval-backend
sudo systemctl status chef-eval-frontend

# Check Nginx configuration
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### File Upload Errors

```bash
# Check storage directory permissions
ls -la /var/www/chef-candidate-media

# Fix permissions
sudo chown -R chef-eval:www-data /var/www/chef-candidate-media
sudo chmod -R 775 /var/www/chef-candidate-media
```

---

## Performance Tuning

### PostgreSQL

Edit `/etc/postgresql/15/main/postgresql.conf`:

```conf
shared_buffers = 512MB
effective_cache_size = 2GB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 8MB
min_wal_size = 1GB
max_wal_size = 4GB
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### Nginx

Edit `/etc/nginx/nginx.conf`:

```nginx
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

Reload Nginx:

```bash
sudo systemctl reload nginx
```

---

## Security Checklist

- [ ] Firewall configured (UFW)
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Strong database password
- [ ] JWT secret key generated securely
- [ ] Storage directory permissions correct (775, chef-eval:www-data)
- [ ] DEBUG=false in production .env
- [ ] SSH key authentication enabled (disable password login)
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Database backups automated
- [ ] Media backups automated

---

## Support

For deployment issues, check:
- Service logs: `sudo journalctl -u chef-eval-*`
- Nginx logs: `/var/log/nginx/`
- Application logs: Check backend console output

---

**Deployment Date**: _____________
**Deployed By**: _____________
**VPS IP**: _____________
**Domain**: _____________
