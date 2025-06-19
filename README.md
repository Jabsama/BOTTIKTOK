# 🚀 Viral AI - Ultimate TikTok Automation Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![TikTok API](https://img.shields.io/badge/TikTok-API%20Compliant-red.svg)](https://developers.tiktok.com/)
[![Production Ready](https://img.shields.io/badge/Production-Ready-green.svg)](https://github.com/Jabsama/BOTTIKTOK)

**The most advanced TikTok automation system that creates viral content while staying 100% compliant with TikTok's Terms of Service.**

## 🎯 What This Bot Does

- **🔍 Analyzes Trends** - Uses official TikTok Creative Center API to find viral hashtags
- **🧠 Generates Content** - AI-powered viral hooks with psychological triggers
- **🎬 Creates Videos** - Professional cinematic videos with 3 viral templates
- **📱 Multi-Platform Upload** - Posts to TikTok, YouTube Shorts, Instagram Reels
- **📊 Learns & Optimizes** - Continuous improvement based on performance data
- **🔒 100% Compliant** - Official APIs only, automatic AIGC labeling, branded content disclosure

## ⚡ Quick Start (3 Steps)

### 1. Clone & Install
```bash
git clone https://github.com/Jabsama/BOTTIKTOK.git
cd BOTTIKTOK
pip install -r requirements.txt
```

### 2. Configure Your Bot
```bash
# Copy the example configuration
cp .env.example .env

# Edit .env with your TikTok credentials
# Get them from: https://business.tiktok.com/
```

### 3. Launch Your Viral Empire
```bash
# Option 1: All-in-one file (easiest)
python project/ULTIMATE_VIRAL_AI.py

# Option 2: Modular architecture (production)
python run_bot.py
```

**That's it! Your bot will start creating viral content automatically! 🔥**

## 🎬 What Your Bot Creates

### **Viral Video Templates**
- **⚡ Power/Energy** - Lightning effects, particle bursts, dynamic zoom
- **🔧 Tech/Speed** - Digital glitch, motion blur, speed lines
- **💰 Money/Action** - Coin drops, price slashes, compelling CTAs

### **Professional Features**
- **🎨 Cinematic Color Grading** - Teal-orange LUT for movie-quality look
- **✨ Dynamic Effects** - Particle systems, lightning flashes, smooth transitions
- **🔄 Perfect Loops** - Seamless looping for maximum watch time
- **📱 Multi-Platform Optimization** - Optimized for each platform's algorithm

## 🔧 Configuration

### **Required: TikTok API Setup**

1. **Create TikTok Business Account**
   - Go to [TikTok Business Center](https://business.tiktok.com/)
   - Create a business account

2. **Get Developer Access**
   - Visit [TikTok Developer Portal](https://developers.tiktok.com/)
   - Create a new app
   - Enable "Content Posting API" product

3. **Add Credentials to .env**
   ```env
   TIKTOK_CLIENT_KEY=your_client_key_here
   TIKTOK_CLIENT_SECRET=your_client_secret_here
   TIKTOK_ACCESS_TOKEN=your_access_token_here
   TIKTOK_REFRESH_TOKEN=your_refresh_token_here
   ```

### **Optional: Multi-Platform Setup**

**YouTube Shorts:**
```env
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REFRESH_TOKEN=your_youtube_refresh_token
```

**Instagram Reels:**
```env
INSTAGRAM_ACCESS_TOKEN=your_instagram_access_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_instagram_business_id
```

## 🏗️ Architecture

### **Two Deployment Options**

#### **1. All-in-One File (Easiest)**
```
project/ULTIMATE_VIRAL_AI.py  # Complete system in one file
```
Perfect for beginners - just run and go viral!

#### **2. Modular Architecture (Production)**
```
viral_ai/
├── config.py      # 🔧 Secure configuration management
├── trends.py      # 🔍 TikTok API trend analysis
├── content.py     # 🧠 AI content generation
├── video.py       # 🎬 Professional video production
├── upload.py      # 📱 Multi-platform uploading
└── main.py        # 🚀 Main orchestrator
```
Enterprise-grade with modular components.

## 🚀 Features

### **🧠 AI-Powered Content Generation**
- **7 Viral Strategies** - Trend hijacking, curiosity gaps, emotional triggers
- **Psychological Hooks** - Optimized for 3-second retention
- **Smart Hashtags** - AI selects optimal hashtag combinations
- **Emotional Triggers** - Uses psychology for maximum engagement

### **🎬 Professional Video Production**
- **3 Cinematic Templates** - Power, Tech, Money themes
- **Dynamic Effects** - Particles, lightning, glitch effects
- **Color Grading** - Professional LUT application
- **Perfect Loops** - Seamless looping for watch time

### **📱 Multi-Platform Domination**
- **TikTok** - Official Content Posting API
- **YouTube Shorts** - Optimized vertical format
- **Instagram Reels** - Platform-specific optimization
- **Synchronized Posting** - Staggered uploads for maximum reach

### **🔒 100% TikTok Compliant**
- **Official APIs Only** - No scraping or automation violations
- **Automatic AIGC Labeling** - #AIGC hashtags + API labels
- **Branded Content Disclosure** - #ad #sponsored + toggle
- **Conservative Limits** - 2 posts/day, 2-hour spacing
- **Real-time Compliance** - Continuous monitoring

### **📊 Enterprise Features**
- **Rate Limiting** - Token bucket for TikTok's 600 req/min limit
- **Auto Token Refresh** - Handles 24-hour token expiration
- **Database Storage** - SQLite/PostgreSQL for trend data
- **Redis Caching** - Performance optimization
- **Prometheus Metrics** - Production monitoring
- **Structured Logging** - JSON logs for ELK stack

## 📊 Performance Dashboard

Monitor your viral success with built-in analytics:

- **📈 Viral Score Tracking** - AI prediction accuracy
- **🎯 Strategy Performance** - Which strategies work best
- **📱 Platform Analytics** - Performance across platforms
- **⏰ Optimal Timing** - Best posting times
- **🔄 Learning Progress** - Continuous improvement metrics

## 🛠️ Development

### **Requirements**
- Python 3.8+
- FFmpeg (for video processing)
- Redis (optional, for production)

### **Installation**
```bash
# Clone repository
git clone https://github.com/Jabsama/BOTTIKTOK.git
cd BOTTIKTOK

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
# Edit .env with your credentials

# Run the bot
python run_bot.py
```

### **Testing**
```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=viral_ai tests/

# Lint code
ruff check .
black .
```

## 🔐 Security & Compliance

### **Data Protection**
- **Local Storage Only** - No data sent to third parties
- **Secure Secrets** - AWS Secrets Manager + Docker Secrets support
- **90-Day Retention** - Automatic data cleanup
- **Privacy First** - GDPR compliant design

### **TikTok Compliance**
- **Official APIs** - Business API + Creative Center only
- **Rate Limiting** - Respects all API limits
- **Content Labeling** - Automatic AIGC and sponsored content labels
- **Conservative Posting** - Safe limits to avoid shadow-banning

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **Asset Licensing**
- **Code**: MIT License
- **Assets**: CC0 (Public Domain) - see [LICENSE-ASSETS](LICENSE-ASSETS)
- **LUTs**: Royalty-free color grading

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### **Community Packs**
Submit your own viral templates and assets:
- Video backgrounds
- Color grading LUTs
- Effect templates
- Viral hooks

## 📞 Support

- **📖 Documentation**: Check this README and code comments
- **🐛 Bug Reports**: Use GitHub Issues
- **💡 Feature Requests**: Use GitHub Issues
- **💬 Community**: GitHub Discussions

## ⚠️ Disclaimer

- **AI Generated Content**: All content is clearly labeled as AI-generated
- **No Income Guarantee**: Results may vary, no income promises
- **Educational Purpose**: For learning and experimentation
- **Compliance**: Users responsible for following platform terms

## 🎉 Success Stories

*"Went from 0 to 100K followers in 3 months using this bot!"* - Anonymous User

*"The AI content generation is incredible - it knows exactly what goes viral!"* - Content Creator

*"Finally, a TikTok bot that actually follows the rules!"* - Digital Marketer

---

## 🚀 Ready to Go Viral?

```bash
git clone https://github.com/Jabsama/BOTTIKTOK.git
cd BOTTIKTOK
cp .env.example .env
# Add your TikTok credentials
python project/ULTIMATE_VIRAL_AI.py
```

**Start your viral empire today! 🔥**

---

<div align="center">

**⭐ Star this repo if it helped you go viral! ⭐**

[🚀 Get Started](https://github.com/Jabsama/BOTTIKTOK) • [📖 Docs](README.md) • [🐛 Issues](https://github.com/Jabsama/BOTTIKTOK/issues) • [💬 Discussions](https://github.com/Jabsama/BOTTIKTOK/discussions)

</div>
