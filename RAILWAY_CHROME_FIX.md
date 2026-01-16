# Fixing Chrome Issue on Railway

The error "No chrome executable found on PATH" means Railway doesn't have Chrome installed.

## Solution: Add Build Script

Railway needs to install Chrome during the build process. Here's how to fix it:

### Option 1: Use Nixpacks Configuration (Recommended)

I've created `nixpacks.toml` which tells Railway to install Chrome.

**Steps:**
1. Make sure `nixpacks.toml` is in your repo (it is now)
2. Railway will automatically use it
3. Redeploy your service

### Option 2: Add Build Command in Railway Dashboard

1. Go to your Railway service
2. Click "Settings"
3. Under "Build & Deploy", find "Build Command"
4. Replace with:
```bash
apt-get update && apt-get install -y wget gnupg && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && apt-get update && apt-get install -y google-chrome-stable && pip install -r requirements.txt
```

### Option 3: Use Dockerfile (Most Reliable)

Create a `Dockerfile` in your repo (I've already created one). Railway should auto-detect it.

If Railway doesn't auto-detect Docker, you may need to configure it in settings.

## Quick Fix Right Now

**Easiest solution:**
1. Go to Railway dashboard
2. Service → Settings → Build & Deploy
3. Set Build Command to:
```bash
apt-get update && apt-get install -y wget gnupg google-chrome-stable && pip install -r requirements.txt
```

**Note:** Railway's free tier might have limitations. If this doesn't work, consider:
- Using AWS EC2 (see `FREE_SETUP_GUIDE.md`) - has Chrome pre-installed
- Or switch to a different approach (requests library instead of Selenium)
