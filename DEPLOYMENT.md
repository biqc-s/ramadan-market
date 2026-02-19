# 🚀 Deployment Guide: Ramadan Market Menu

This guide explains how to keep your Telegram Bot running 24/7 separately from your website.

## 1. Hosting Images (Cloudinary)
Since the bot will run on a cloud server that "resets" often, we cannot save images locally. We use **Cloudinary** (Free) to host them.

1.  Sign up for free at [cloudinary.com](https://cloudinary.com/).
2.  Go to the **Dashboard**.
3.  Copy your **Product Environment Credentials**:
    -   Cloud Name
    -   API Key
    -   API Secret
4.  Open `bot.py` and replace the placeholders with these values.

## 2. GitHub Setup
1.  Create a new repository on GitHub (e.g., `ramadan-market`).
2.  Upload/Push all your files (`bot.py`, `requirements.txt`, `data.json`, `index.html`) to this repository.

## 3. Web Hosting (GitHub Pages)
1.  Go to your GitHub Repository > **Settings** > **Pages**.
2.  Select `main` branch and `/root` folder.
3.  Click **Save**.
4.  Your website link will be: `https://your-username.github.io/ramadan-market/?v=shop1`

## 4. Bot Hosting (Render.com - 24/7)
1.  Sign up at [render.com](https://render.com/).
2.  Click **New +** and select **Background Worker**.
    -   *Background Worker is better for bots than Web Service.*
3.  Connect your GitHub repository.
4.  **Settings**:
    -   **Name**: `ramadan-bot`
    -   **Runtime**: `Python 3`
    -   **Build Command**: `pip install -r requirements.txt`
    -   **Start Command**: `python bot.py`
5.  Click **Create Background Worker**.

> **Note on Free Tier**: Render's free tier spins down after inactivity. For true 24/7 without pauses, you might need a paid plan ($7/mo) OR use **PythonAnywhere** ($5/mo) which is very stable for telegram bots.

## Alternative: PythonAnywhere (Recommended for Stability)
1.  Sign up at [pythonanywhere.com](https://www.pythonanywhere.com/).
2.  Go to **Consoles** > **Bash**.
3.  Clone your repo: `git clone https://github.com/your-username/ramadan-market.git`
4.  Install requirements: `pip install -r requirements.txt`
5.  Run bot: `python bot.py` (Note: Free tier has limited CPU seconds, Paid tier allows "Always-on tasks").
