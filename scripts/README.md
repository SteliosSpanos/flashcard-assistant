# Discord Flashcard Bot Script

A bash script that sends daily flashcard reminders to Discord.

## Requirements

- `curl` - Pre-installed on Debian
- `jq` - JSON parser

## Installation

### 1. Install jq

```bash
sudo apt update
sudo apt install jq
```

### 2. Configure

```bash
cd ~/.../flashcard-assistant/scripts

# Copy config template
cp config.example config

# Edit with your credentials
nano config (or nvim)
```

Fill in your API URL, username, password, and Discord webhook URL.

### 3. Make Executable

```bash
chmod +x discord-flashcard-bot.sh
```

### 4. Test

```bash
# Start your API first
cd ~/Desktop/Py_Projects/flashcard-assistant
uvicorn app.main:app --reload &

# Run the script
cd scripts
./discord-flashcard-bot.sh
```

Check Discord for the flashcard message.

### 5. Automate with Cron

```bash
crontab -e
```

Add this line to run daily at 9:00 AM:

```
0 9 * * * /home/steliosspanos/Desktop/Py_Projects/flashcard-assistant/scripts/discord-flashcard-bot.sh
```

## Common Cron Schedules

```
0 9 * * *      # Every day at 9:00 AM
0 12 * * *     # Every day at 12:00 PM
0 9 * * 1-5    # Weekdays at 9:00 AM
0 9,18 * * *   # Every day at 9:00 AM and 6:00 PM
```

## Troubleshooting

### Check Logs

```bash
cat flashcard-bot.log
```

### Common Issues

**jq not found**
```bash
sudo apt install jq
```

**Authentication failed**
- Check username and password in config
- Verify API is running
- Ensure user account exists

**No flashcards found**
- Create topics with flashcards in the app
- Verify you're using the correct username

**Discord webhook failed**
- Verify webhook URL is correct
- Check webhook still exists in Discord

## Security

Keep your `config` file private. It contains credentials and is in .gitignore.
