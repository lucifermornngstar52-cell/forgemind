# FORGEMIND — Oracle Cloud Deployment Guide

## Always Free Tier Setup

### 1. Create Oracle Cloud Account
- Go to oracle.com/cloud/free
- Sign up (requires credit card for verification, won't be charged)
- You get: 4 ARM cores, 24GB RAM, 200GB storage — FREE FOREVER

### 2. Create VM Instance
- Go to Compute → Instances → Create Instance
- Image: Canonical Ubuntu 22.04 (or 24.04)
- Shape: VM.Standard.A1.Flex (ARM, 4 OCPU, 24GB RAM)
- Add SSH key (generate or upload your public key)
- Wait for instance to be ready

### 3. Initial Setup
```bash
# SSH into the instance
ssh ubuntu@<instance-public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.12
sudo apt install -y python3.12 python3.12-venv git

# Clone FORGEMIND
git clone https://github.com/lucifermornngstar52-cell/forgemind.git
cd forgemind

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Set Environment Variables
```bash
# Create .env file
cat > .env << 'ENV'
OPENAI_API_KEY=your-openai-key
GITHUB_TOKEN_2=your-github-pat
TELEGRAM_BOT_TOKEN=your-bot-token
GOOGLE_EMAIL=your-google-email
GOOGLE_PASSWORD=your-google-password
GOOGLE_GEMINI_KEY=your-gemini-key
ENV

chmod 600 .env
```

### 5. Set Up Systemd Services

#### Self-Improvement Cycle (every 2 hours)
```bash
sudo cat > /etc/systemd/system/forgemind-cycle.service << 'SVC'
[Unit]
Description=FORGEMIND Self-Improvement Cycle
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/forgemind
EnvironmentFile=/home/ubuntu/forgemind/.env
ExecStart=/home/ubuntu/forgemind/venv/bin/python main.py --loop 3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVC

sudo cat > /etc/systemd/system/forgemind-cycle.timer << 'TMR'
[Unit]
Description=Run FORGEMIND cycle every 2 hours

[Timer]
OnBootSec=5min
OnUnitActiveSec=2h
Unit=forgemind-cycle.service

[Install]
WantedBy=timers.target
TMR

sudo systemctl enable forgemind-cycle.timer
sudo systemctl start forgemind-cycle.timer
```

#### Telegram Bot (24/7)
```bash
sudo cat > /etc/systemd/system/forgemind-bot.service << 'SVC'
[Unit]
Description=FORGEMIND Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/forgemind
EnvironmentFile=/home/ubuntu/forgemind/.env
ExecStart=/home/ubuntu/forgemind/venv/bin/python main.py --bot
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVC

sudo systemctl enable forgemind-bot
sudo systemctl start forgemind-bot
```

### 6. Auto-Commit Changes
```bash
# Set up git credentials
git config --global user.name "Forgemind Bot"
git config --global user.email "forgemind@bot.local"

# Add auto-commit to cycle script
echo 'git add -A && git commit -m "auto: cycle $(date)" && git push' >> post_cycle.sh
chmod +x post_cycle.sh
```

### 7. Monitoring
```bash
# Check bot status
sudo systemctl status forgemind-bot

# Check cycle timer
sudo systemctl status forgemind-cycle.timer

# View logs
journalctl -u forgemind-bot -f
journalctl -u forgemind-cycle -f

# Check timers
systemctl list-timers forgemind-cycle.timer
```

## Cost: $0/month (Always Free Tier)
## Specs: 4 ARM cores, 24GB RAM, 200GB storage
## Uptime: 24/7
