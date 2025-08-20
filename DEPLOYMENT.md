# 🚀 Supper Bot Deployment Guide

This guide will help you deploy your Supper Bot to production.

## 🎯 **Deployment Options**

### **Option 1: Railway (Recommended - Easy & Free)**
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy deployment
- ✅ Good for small to medium bots

### **Option 2: Heroku**
- ✅ Popular platform
- ✅ Good free tier
- ❌ Requires credit card
- ❌ Free tier limitations

### **Option 3: DigitalOcean/AWS**
- ✅ Full control
- ✅ Scalable
- ❌ More complex setup
- ❌ Costs money

---

## 🚂 **Option 1: Deploy on Railway**

### **Step 1: Prepare Your Repository**

1. **Commit all changes:**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Ensure these files exist:**
   - ✅ `requirements.txt` - Python dependencies
   - ✅ `Procfile` - Tells Railway how to run your app
   - ✅ `runtime.txt` - Python version
   - ✅ `deploy.py` - Webhook setup script

### **Step 2: Deploy on Railway**

1. **Go to [Railway.app](https://railway.app)**
2. **Sign up/Login** with GitHub
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repository**
6. **Wait for deployment** (usually 2-5 minutes)

### **Step 3: Configure Environment Variables**

In your Railway project dashboard:

1. **Go to "Variables" tab**
2. **Add these variables:**

   ```
   BOT_TOKEN=your_telegram_bot_token_here
   SECRET_TOKEN=your_random_secret_string
   WEBHOOK_HOST=your-app-name.railway.app
   ```

3. **Get your app URL** from the "Settings" tab
4. **Set WEBHOOK_URL** to: `https://your-app-name.railway.app/your_secret_token`

### **Step 4: Set Up Webhook**

1. **Go to "Deployments" tab**
2. **Click on your latest deployment**
3. **Open terminal/console**
4. **Run the webhook setup:**

   ```bash
   python deploy.py
   ```

   Or manually:
   ```bash
   python -c "
   import asyncio
   from src.tgbot.infrastructure.bot import bot
   
   async def setup():
       await bot.remove_webhook()
       await bot.set_webhook('https://your-app-name.railway.app/your_secret_token')
       print('Webhook set!')
       await bot.close_session()
   
   asyncio.run(setup())
   "
   ```

---

## 🎪 **Option 2: Deploy on Heroku**

### **Step 1: Install Heroku CLI**

```bash
# macOS
brew install heroku/brew/heroku

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

### **Step 2: Deploy**

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-supper-bot-name

# Add buildpack
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set BOT_TOKEN=your_bot_token
heroku config:set SECRET_TOKEN=your_secret_token
heroku config:set WEBHOOK_HOST=your-app-name.herokuapp.com

# Deploy
git push heroku main

# Set up webhook
heroku run python deploy.py
```

---

## 🐳 **Option 3: Docker Deployment**

### **Create Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "src.tgbot.infrastructure.api"]
```

### **Deploy with Docker**

```bash
# Build image
docker build -t supper-bot .

# Run container
docker run -p 8000:8000 \
  -e BOT_TOKEN=your_token \
  -e SECRET_TOKEN=your_secret \
  -e WEBHOOK_HOST=your_domain \
  supper-bot
```

---

## 🔧 **Post-Deployment Setup**

### **1. Test Your Bot**

1. **Send `/start`** to your bot
2. **Create a jio** and add items
3. **Test inline mode** in a group chat
4. **Verify webhook** is working

### **2. Monitor Logs**

- **Railway:** View logs in the dashboard
- **Heroku:** `heroku logs --tail`
- **Docker:** `docker logs container_name`

### **3. Set Up Monitoring**

Consider adding:
- Health check endpoint
- Error logging
- Performance monitoring

---

## 🚨 **Common Issues & Solutions**

### **Webhook Not Working**

```bash
# Check webhook status
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"

# Set webhook manually
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/your_secret_token"}'
```

### **Bot Not Responding**

1. **Check environment variables** are set correctly
2. **Verify webhook URL** is accessible
3. **Check logs** for errors
4. **Ensure bot token** is valid

### **Inline Mode Issues**

1. **Enable inline mode** in @BotFather
2. **Check bot permissions**
3. **Verify webhook** is working
4. **Test with simple commands** first

---

## 📱 **Testing Your Deployed Bot**

### **Local Testing**
```bash
# Test webhook locally
ngrok http 8000
# Use ngrok URL as webhook
```

### **Production Testing**
1. **Send commands** to your bot
2. **Test inline mode** in groups
3. **Verify real-time updates**
4. **Check performance** under load

---

## 🎉 **You're Ready!**

Your Supper Bot is now deployed and ready to serve users! 

**Next steps:**
- 🧪 Test all functionality
- 📊 Monitor performance
- 🚀 Scale as needed
- 💡 Add new features

**Need help?** Check the logs and use the debug commands:
- `/bot_info` - Check bot status
- `/debug` - Detailed debugging info
- `/test_inline` - Test inline functionality

Happy deploying! 🚀🍽️
