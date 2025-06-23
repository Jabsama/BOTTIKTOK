# 🚀 Complete Setup Guide - Viral AI TikTok Bot

This guide will walk you through setting up your TikTok automation bot step by step.

---

## 📋 Prerequisites

- **Python 3.8+** installed on your computer
- **Git** for cloning the repository
- **TikTok Business Account** (free to create)
- **Basic command line knowledge**

---

## 🎯 Step 1: Get Your TikTok API Credentials

### 1.1 Create TikTok Business Account
1. Go to [TikTok Business Center](https://business.tiktok.com/)
2. Click "Create Account" 
3. Fill in your business information
4. Verify your email and phone number

### 1.2 Access Developer Portal
1. Visit [TikTok Developer Portal](https://developers.tiktok.com/)
2. Sign in with your TikTok Business account
3. Click "Manage Apps" in the top menu

### 1.3 Create Your App
1. Click "Create an App"
2. Fill in the app details:
   - **App Name**: "Viral AI Bot" (or your choice)
   - **App Description**: "AI-powered content automation"
   - **Category**: "Productivity"
   - **Platform**: "Web"
3. Click "Submit for Review"

### 1.4 Enable Content Posting API
1. Once your app is approved (usually 1-2 business days)
2. Go to your app dashboard
3. Click "Add Products"
4. Select "Content Posting API"
5. Click "Add Product"

### 1.5 Get Your Credentials
1. In your app dashboard, go to "Basic Information"
2. Copy these values:
   - **Client Key** (looks like: `aw7hr0k0b2kfjznv`)
   - **Client Secret** (looks like: `IUVK9KVxBhTath9LpjouKtHBEZk3SfXo`)

---

## 🎬 Step 2: Optional - YouTube API Setup

### 2.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project"
3. Name it "Viral AI YouTube"
4. Click "Create"

### 2.2 Enable YouTube API
1. In your project dashboard
2. Go to "APIs & Services" > "Library"
3. Search for "YouTube Data API v3"
4. Click on it and press "Enable"

### 2.3 Create Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure OAuth consent screen if prompted
4. Choose "Desktop Application"
5. Name it "Viral AI Bot"
6. Copy your:
   - **Client ID**
   - **Client Secret**

### 2.4 Get API Key
1. Click "Create Credentials" > "API Key"
2. Copy the generated API key
3. (Optional) Restrict the key to YouTube Data API v3

---

## 💻 Step 3: Install the Bot

### 3.1 Clone Repository
```bash
git clone https://github.com/yourusername/viral-ai-tiktok.git
cd viral-ai-tiktok
```

### 3.2 Install Dependencies
```bash
pip install -r requirements.txt
```

### 3.3 Create Configuration File
```bash
cp .env.example .env
```

---

## ⚙️ Step 4: Configure Your Bot

### 4.1 Edit .env File
Open `.env` in your favorite text editor and fill in:

```env
# 🎵 TIKTOK API CREDENTIALS (REQUIRED)
TIKTOK_CLIENT_KEY=your_client_key_here
TIKTOK_CLIENT_SECRET=your_client_secret_here

# 📺 YOUTUBE API CREDENTIALS (OPTIONAL)
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_API_KEY=your_youtube_api_key

# 🎨 BRAND CUSTOMIZATION
BRAND_PRIMARY_COLOR=#00BFA6
BRAND_SECONDARY_COLOR=#FFD54F
PROMO_CODE=YOUR_CODE
AFFILIATE_URL=https://your-site.com/?ref=YOUR_CODE
```

### 4.2 Generate Access Tokens

**Option A: Automatic (Recommended)**
```bash
python generate_tokens.py
```
- This will open your browser
- Authorize the app when prompted
- Tokens will be automatically added to your .env file

**Option B: Manual**
If the automatic method doesn't work:
1. Visit the OAuth URL shown in the terminal
2. Complete the authorization flow
3. Copy the authorization code
4. The script will exchange it for tokens

---

## 🚀 Step 5: Launch Your Bot

### 5.1 Test Configuration
```bash
python -c "from viral_ai.config import Config; print('✅ Configuration loaded successfully')"
```

### 5.2 Start the Bot
```bash
python run_bot.py
```

You should see:
```
🚀 Starting Viral AI System...
🔧 Initializing Viral AI components...
✅ All components initialized successfully
🎯 Viral AI System is now running!
📊 Dashboard available at: http://localhost:8000/metrics
🛑 Press Ctrl+C to stop
```

---

## 📊 Step 6: Monitor Your Bot

### 6.1 Check Dashboard
Open your browser and go to: `http://localhost:8000/metrics`

### 6.2 View Logs
The bot logs everything to the console. Look for:
- ✅ Success messages
- ⚠️ Warnings (usually safe to ignore)
- ❌ Errors (need attention)

### 6.3 Check Generated Content
- Videos are saved in the `output/` folder
- Database is stored as `viral_ai.db`
- Logs are in the `logs/` folder (if configured)

---

## 🔧 Troubleshooting

### Common Issues

#### "TikTok API credentials missing"
- Double-check your `.env` file
- Ensure no extra spaces around the `=` sign
- Verify your credentials are correct

#### "Failed to fetch trending hashtags"
- Your app might not be approved yet
- Check if Content Posting API is enabled
- Verify your access tokens are valid

#### "Rate limit exceeded"
- The bot respects TikTok's limits automatically
- Wait a few minutes and try again
- Check if you have other apps using the same credentials

#### "Video generation failed"
- Ensure FFmpeg is installed on your system
- Check if you have enough disk space
- Verify the `assets/` folder exists

### Getting Help

1. **Check the logs** - Most issues are explained in the error messages
2. **Read the error carefully** - The bot provides helpful troubleshooting tips
3. **Check GitHub Issues** - Someone might have had the same problem
4. **Create a new issue** - If you're still stuck, we're here to help!

---

## 🎯 What Happens Next?

Once your bot is running:

1. **Every 30 minutes**, it will:
   - Analyze trending hashtags on TikTok
   - Generate viral content ideas
   - Create professional videos
   - Upload to your configured platforms

2. **It will automatically**:
   - Add AIGC labels for compliance
   - Include sponsored content disclosures
   - Respect posting limits (2 posts/day max)
   - Learn from performance data

3. **You can monitor**:
   - Performance metrics on the dashboard
   - Generated videos in the output folder
   - Detailed logs for troubleshooting

---

## 🔒 Security Best Practices

1. **Never commit your .env file** - It's already in .gitignore
2. **Keep your credentials private** - Don't share them with anyone
3. **Regularly rotate your tokens** - Use the token generator monthly
4. **Monitor your usage** - Check the TikTok Developer dashboard
5. **Use strong passwords** - For your TikTok Business account

---

## 🎉 You're All Set!

Your Viral AI TikTok bot is now ready to help you dominate social media! 

Remember:
- Start with the default settings
- Monitor the first few posts carefully
- Adjust the configuration as needed
- Have fun going viral! 🚀

---

## 📞 Need Help?

- **Documentation**: Check the main README.md
- **Issues**: Create a GitHub issue
- **Community**: Join our GitHub Discussions
- **Updates**: Watch the repository for new features

**Happy viral content creation! 🔥**
