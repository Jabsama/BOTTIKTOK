# Professional Deployment Guide

This guide provides step-by-step instructions for deploying the TikTok Video Automation Bot in production environments.

## 🚀 Quick Deployment Commands

### GitHub Repository Setup
```bash
# Initialize repository
git init
git add .
git commit -m "Initial commit: TikTok Video Automation Bot"
git branch -M main
git remote add origin https://github.com/Jabsama/BOTTIKTOK.git
git push -u origin main
```

### One-Line Docker Deployment
```bash
docker run -e TZ=UTC -v $(pwd)/project:/app --env-file .env tiktok-bot:latest
```

## 📋 Pre-Deployment Checklist

### Repository Configuration
- [ ] Repository created: `https://github.com/Jabsama/BOTTIKTOK.git`
- [ ] GitHub Actions enabled
- [ ] Branch protection rules configured
- [ ] Security alerts enabled
- [ ] Dependabot configured

### Credentials Setup
- [ ] TikTok API credentials obtained
- [ ] `.env` file configured (never commit this!)
- [ ] Discord webhook configured (optional)
- [ ] Multi-platform API keys ready (optional)

### Infrastructure Ready
- [ ] Docker installed and configured
- [ ] Monitoring tools setup (Prometheus/Grafana)
- [ ] Log aggregation configured
- [ ] Backup strategy implemented

## 🔧 GitHub Repository Setup

### 1. Create Repository
```bash
# Create repository on GitHub: https://github.com/Jabsama/BOTTIKTOK.git
# Then clone and setup locally:

git clone https://github.com/Jabsama/BOTTIKTOK.git
cd BOTTIKTOK

# Copy project files
cp -r /path/to/project/* .

# Initial commit
git add .
git commit -m "feat: initial TikTok automation bot implementation

- Complete video automation pipeline
- Viral remix system with compliance
- Multi-armed bandit optimization
- Professional CI/CD setup
- Comprehensive documentation"

git push origin main
```

### 2. Enable GitHub Actions
1. Go to repository **Settings** → **Actions** → **General**
2. Enable **"Allow all actions and reusable workflows"**
3. Set **Workflow permissions** to **"Read and write permissions"**
4. Enable **"Allow GitHub Actions to create and approve pull requests"**

### 3. Configure Branch Protection
1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Include administrators

### 4. Setup Security Features
1. **Security Alerts**: Settings → Security & analysis → Enable all
2. **Dependabot**: Enable dependency updates
3. **Code Scanning**: Enable CodeQL analysis
4. **Secret Scanning**: Enable for private repos

## 📊 Codecov Integration

### 1. Setup Codecov
```bash
# Add to repository secrets (Settings → Secrets → Actions)
CODECOV_TOKEN=your_codecov_token_here
```

### 2. Badge Configuration
Add to README.md:
```markdown
[![codecov](https://codecov.io/gh/Jabsama/BOTTIKTOK/branch/main/graph/badge.svg)](https://codecov.io/gh/Jabsama/BOTTIKTOK)
```

## 🐳 Docker Production Deployment

### 1. Build Production Image
```bash
# Build optimized production image
docker build -t tiktok-bot:latest .

# Verify image size (should be <700MB)
docker images tiktok-bot:latest

# Test image
docker run --rm tiktok-bot:latest python -c "import yaml, requests, moviepy; print('✅ Dependencies OK')"
```

### 2. Production Docker Compose
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  tiktok-bot:
    image: tiktok-bot:latest
    container_name: tiktok-automation
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - TZ=UTC
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./output:/app/output
      - ./backups:/app/backups
    healthcheck:
      test: ["CMD", "python", "-c", "import yaml; print('OK')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

volumes:
  prometheus_data:
```

### 3. Deploy with Docker Compose
```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f tiktok-bot
```

## ☁️ Cloud Deployment Options

### Oracle Cloud Free Tier
```bash
# Create VM instance
# Shape: VM.Standard.E2.1.Micro (1 OCPU, 1GB RAM)
# OS: Ubuntu 22.04 LTS
# Storage: 47GB boot volume

# Connect and setup
ssh ubuntu@your-instance-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Deploy application
git clone https://github.com/Jabsama/BOTTIKTOK.git
cd BOTTIKTOK
cp .env.example .env
# Edit .env with your credentials
docker-compose -f docker-compose.prod.yml up -d
```

### AWS EC2 Deployment
```bash
# Launch t2.micro instance with Ubuntu 22.04
# Configure security group (SSH: 22, HTTP: 80, HTTPS: 443)

# User data script for automatic setup:
#!/bin/bash
apt-get update
apt-get install -y docker.io docker-compose git
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Clone and setup application
cd /home/ubuntu
git clone https://github.com/Jabsama/BOTTIKTOK.git
chown -R ubuntu:ubuntu BOTTIKTOK
```

### Google Cloud Run
```bash
# Build and push to Container Registry
docker build -t gcr.io/your-project/tiktok-bot .
docker push gcr.io/your-project/tiktok-bot

# Deploy to Cloud Run
gcloud run deploy tiktok-bot \
  --image gcr.io/your-project/tiktok-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 3600
```

## 📊 Monitoring Setup

### 1. Prometheus Configuration
Create `monitoring/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'tiktok-bot'
    static_configs:
      - targets: ['tiktok-bot:8000']
    metrics_path: /metrics
    scrape_interval: 30s
```

### 2. Grafana Dashboard
```bash
# Add Grafana to docker-compose
grafana:
  image: grafana/grafana:latest
  container_name: grafana
  restart: unless-stopped
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana_data:/var/lib/grafana
```

### 3. Key Metrics to Monitor
- Video creation success rate
- Upload success rate
- API response times
- Memory usage
- Disk space
- Error rates
- Engagement metrics

## 🔒 Security Hardening

### 1. Environment Security
```bash
# Set proper file permissions
chmod 600 .env
chmod 700 logs/
chmod 755 output/

# Use non-root user in Docker
USER app
WORKDIR /app
```

### 2. Network Security
```bash
# Configure firewall (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. Secrets Management
```bash
# Use Docker secrets for production
echo "your_secret_value" | docker secret create tiktok_api_key -

# Reference in docker-compose
secrets:
  - tiktok_api_key
```

## 📈 Performance Optimization

### 1. Resource Limits
```yaml
# Docker resource limits
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 1G
```

### 2. Caching Strategy
```bash
# Redis for caching (optional)
redis:
  image: redis:alpine
  container_name: redis
  restart: unless-stopped
  volumes:
    - redis_data:/data
```

### 3. Database Optimization
```bash
# SQLite optimization for production
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=memory;
```

## 🔄 Backup and Recovery

### 1. Automated Backups
```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf "backup_${DATE}.tar.gz" data/ logs/ trends.db
aws s3 cp "backup_${DATE}.tar.gz" s3://your-backup-bucket/
```

### 2. Database Backup
```bash
# SQLite backup
sqlite3 trends.db ".backup backup_$(date +%Y%m%d).db"
```

### 3. Recovery Procedures
```bash
# Restore from backup
tar -xzf backup_20241201_120000.tar.gz
docker-compose -f docker-compose.prod.yml restart
```

## 📋 Production Checklist

### Pre-Launch
- [ ] All tests passing in CI/CD
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Monitoring configured
- [ ] Backup strategy implemented
- [ ] Documentation updated

### Launch
- [ ] Deploy to production environment
- [ ] Verify all services running
- [ ] Check monitoring dashboards
- [ ] Test core functionality
- [ ] Monitor error rates

### Post-Launch
- [ ] Monitor performance metrics
- [ ] Check log files for errors
- [ ] Verify backup creation
- [ ] Update documentation
- [ ] Plan next iteration

## 🚨 Troubleshooting

### Common Issues
```bash
# Container won't start
docker logs tiktok-bot

# High memory usage
docker stats tiktok-bot

# Database locked
sqlite3 trends.db "PRAGMA wal_checkpoint;"

# Permission issues
sudo chown -R 1000:1000 /app/data
```

### Health Checks
```bash
# Application health
curl http://localhost:8000/health

# Database health
sqlite3 trends.db "SELECT COUNT(*) FROM trends;"

# Disk space
df -h
```

## 📞 Support

### Getting Help
1. **Documentation**: Check README.md and CONTRIBUTING.md
2. **Issues**: Create GitHub issue with logs
3. **Monitoring**: Check Grafana dashboards
4. **Logs**: Review application logs

### Emergency Contacts
- **Technical Issues**: Create GitHub issue
- **Security Issues**: Email security@project.com
- **Infrastructure**: Check cloud provider status

---

**🚀 Ready for Production!**

Your TikTok Video Automation Bot is now ready for professional deployment. Follow this guide step-by-step for a successful production launch.
