# Production Deployment Guide

This guide walks you through deploying the Django application on a VPS.

## Prerequisites

- Ubuntu/Debian VPS (or similar Linux distribution)
- Root or sudo access
- Domain name (optional, but recommended)
- PostgreSQL installed and running

## Step 1: Server Setup

### Update system packages
```bash
sudo apt update
sudo apt upgrade -y
```

### Install required packages
```bash
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git
```

## Step 2: Create System User

```bash
sudo adduser --system --group --no-create-home django
```

## Step 3: Clone and Setup Project

```bash
# Clone your repository
cd /opt
sudo git clone <your-repo-url> SYNAPSEPARQUET
sudo chown -R django:django /opt/SYNAPSEPARQUET
cd /opt/SYNAPSEPARQUET

# Create virtual environment
sudo -u django python3 -m venv .venv
sudo -u django .venv/bin/pip install --upgrade pip
sudo -u django .venv/bin/pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

```bash
sudo -u django nano /opt/SYNAPSEPARQUET/.env
```

Add the following (adjust values as needed):
```env
# Django Settings
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,IP_ADDRESS

# Database
DB_NAME=the_project_db
DB_USER=the_project_user
DB_PASSWORD=your-secure-db-password
DB_HOST=localhost
DB_PORT=5432

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Gunicorn (optional)
GUNICORN_PORT=8000
GUNICORN_ACCESS_LOG=/opt/SYNAPSEPARQUET/logs/access.log
GUNICORN_ERROR_LOG=/opt/SYNAPSEPARQUET/logs/error.log
GUNICORN_LOG_LEVEL=info
```

Generate a secure SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 5: Setup PostgreSQL Database

```bash
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE the_project_db;
CREATE USER the_project_user WITH PASSWORD 'your-secure-db-password';
ALTER ROLE the_project_user SET client_encoding TO 'utf8';
ALTER ROLE the_project_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE the_project_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE the_project_db TO the_project_user;
\q
```

## Step 6: Run Migrations and Collect Static Files

```bash
cd /opt/SYNAPSEPARQUET
sudo -u django .venv/bin/python manage.py migrate
sudo -u django .venv/bin/python manage.py collectstatic --noinput
sudo -u django .venv/bin/python manage.py createsuperuser
```

## Step 7: Create Logs Directory

```bash
sudo mkdir -p /opt/SYNAPSEPARQUET/logs
sudo chown django:django /opt/SYNAPSEPARQUET/logs
```

## Step 8: Configure Gunicorn Service

Edit the `gunicorn.service` file and update paths:
- Replace `/path/to/SYNAPSEPARQUET` with `/opt/SYNAPSEPARQUET`
- Update user/group if needed

Copy service file:
```bash
sudo cp gunicorn.service /etc/systemd/system/the_project.service
sudo systemctl daemon-reload
sudo systemctl enable the_project
sudo systemctl start the_project
sudo systemctl status the_project
```

## Step 9: Configure Nginx

Edit the `nginx.conf` file:
- Replace `/path/to/SYNAPSEPARQUET` with `/opt/SYNAPSEPARQUET`
- Replace `example.com` with your domain
- Update SSL certificate paths

Copy configuration:
```bash
sudo cp nginx.conf /etc/nginx/sites-available/the_project
sudo ln -s /etc/nginx/sites-available/the_project /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## Step 10: Setup SSL with Let's Encrypt (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically configure SSL and renew certificates.

## Step 11: Firewall Configuration

```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

## Step 12: Verify Deployment

1. Check Gunicorn service: `sudo systemctl status the_project`
2. Check Nginx: `sudo systemctl status nginx`
3. Check logs: `sudo tail -f /opt/SYNAPSEPARQUET/logs/django.log`
4. Visit your domain in a browser

## Maintenance Commands

### Restart application
```bash
sudo systemctl restart the_project
```

### View logs
```bash
# Application logs
sudo tail -f /opt/SYNAPSEPARQUET/logs/django.log

# Gunicorn logs
sudo journalctl -u the_project -f

# Nginx logs
sudo tail -f /var/log/nginx/the_project_error.log
```

### Update application
```bash
cd /opt/SYNAPSEPARQUET
sudo -u django git pull
sudo -u django .venv/bin/pip install -r requirements.txt
sudo -u django .venv/bin/python manage.py migrate
sudo -u django .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart the_project
```

## Troubleshooting

### Check if services are running
```bash
sudo systemctl status the_project
sudo systemctl status nginx
sudo systemctl status postgresql
```

### Check port usage
```bash
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :80
```

### Test database connection
```bash
sudo -u django .venv/bin/python manage.py dbshell
```

### Check file permissions
```bash
sudo ls -la /opt/SYNAPSEPARQUET
```

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY set
- [ ] ALLOWED_HOSTS configured
- [ ] Database user has limited privileges
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured
- [ ] Regular backups configured
- [ ] Logs are being monitored
- [ ] .env file has proper permissions (600)

## Backup Strategy

### Database backup
```bash
sudo -u postgres pg_dump the_project_db > backup_$(date +%Y%m%d).sql
```

### Restore database
```bash
sudo -u postgres psql the_project_db < backup_YYYYMMDD.sql
```

