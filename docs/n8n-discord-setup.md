# Discord Daily Flashcard Automation with n8n

This guide will help you set up automated daily flashcard reminders sent to Discord using n8n.

## Overview

The automation workflow:
1. Runs daily at a scheduled time (default: 9:00 AM)
2. Logs into your API to get an authentication token
3. Fetches a flashcard from your topic with the lowest accuracy
4. Formats the flashcard as a beautiful Discord embed
5. Sends it to your Discord channel via webhook

## Prerequisites

- Running instance of the Flashcard Assistant API
- n8n instance (cloud or self-hosted)
- Discord server with webhook access

## Step 1: Create Discord Webhook

1. Open your Discord server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Configure the webhook:
   - **Name**: "Flashcard Bot" (or any name you prefer)
   - **Channel**: Select the channel where you want flashcards posted
5. Click **Copy Webhook URL** and save it securely
6. Click **Save**

Your webhook URL will look like:
```
https://discord.com/api/webhooks/123456789/AbCdEfGhIjKlMnOpQrStUvWxYz
```

## Step 2: Set Up n8n Environment Variables

In your n8n instance, set up the following environment variables:

### For n8n Cloud:
1. Go to **Settings** → **Environments**
2. Add the following variables:

| Variable Name | Example Value | Description |
|--------------|---------------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Your API base URL (no trailing slash) |
| `API_USERNAME` | `your_username` | Your flashcard app username |
| `API_PASSWORD` | `your_password` | Your flashcard app password |
| `DISCORD_WEBHOOK_URL` | `https://discord.com/api/webhooks/...` | Your Discord webhook URL |

### For Self-Hosted n8n:
Add to your `.env` file or docker-compose environment:
```bash
API_BASE_URL=http://localhost:8000
API_USERNAME=your_username
API_PASSWORD=your_password
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/123456789/AbCdEfGhIjKlMnOpQrStUvWxYz
```

## Step 3: Import the Workflow

1. Log into your n8n instance
2. Click **Workflows** → **Add Workflow** → **Import from File**
3. Select the file: `n8n-workflows/discord-daily-flashcard.json`
4. Click **Import**

The workflow will be imported with all nodes configured.

## Step 4: Customize the Schedule

The default schedule is **9:00 AM daily**. To change this:

1. Click on the **Schedule Trigger** node
2. Modify the **Cron Expression**:
   - `0 9 * * *` = 9:00 AM daily
   - `0 12 * * *` = 12:00 PM daily
   - `0 20 * * *` = 8:00 PM daily
   - `0 9 * * 1-5` = 9:00 AM weekdays only

### Common Cron Patterns:
```
0 9 * * *     → Every day at 9:00 AM
0 12,18 * * * → Every day at 12:00 PM and 6:00 PM
0 9 * * 1-5   → Weekdays at 9:00 AM
30 8 * * *    → Every day at 8:30 AM
```

## Step 5: Test the Workflow

1. Click **Execute Workflow** button in the top right
2. Watch each node execute (they will turn green when successful)
3. Check your Discord channel for the flashcard message

If any node fails, click on it to see the error details.

## Step 6: Activate the Workflow

1. Toggle the **Active** switch in the top right corner to ON
2. The workflow will now run automatically on the schedule

## What the Discord Message Looks Like

The automation sends a rich embed with:

- **Title**: Topic name with emoji
- **Difficulty**: Color-coded (🟢 Easy, 🟡 Medium, 🔴 Hard)
- **Question**: Clearly displayed
- **Answer**: Hidden with spoiler tags (click to reveal)
- **Your Progress**: Shows accuracy, streak, and cards reviewed
- **Footer**: Motivational message to study

### Example Message:
```
📚 Daily Flashcard - Python Basics
Difficulty: Medium

Time to keep your study streak going! 🔥

❓ Question
What is a decorator in Python?

💡 Answer
||A function that modifies another||

📊 Your Progress
Accuracy: 75%
Streak: 5 days
Cards Reviewed: 23

💡 Open the app to study and improve your progress!
```

## How Topic Selection Works

The automation automatically selects flashcards from the topic where you need the most practice:
- Topics with **0% accuracy** (unstudied) are prioritized
- Otherwise, it picks the topic with the **lowest accuracy percentage**
- A random flashcard from that topic is selected each day

This ensures you're always working on your weakest areas!

## Troubleshooting

### Authentication Errors
- Verify `API_USERNAME` and `API_PASSWORD` are correct
- Check that your API is running and accessible from n8n
- Ensure `API_BASE_URL` doesn't have a trailing slash

### No Flashcards Found
- Make sure you have created at least one topic
- Add flashcards to your topics (manually or via AI generation)
- Check that you're logged in with the correct user account

### Discord Webhook Errors
- Verify the webhook URL is correct and hasn't been deleted
- Check that the webhook still has permission to post in the channel
- Ensure the webhook URL is the full URL including the token

### Workflow Not Running on Schedule
- Check that the workflow is **Active** (toggle in top right)
- Verify the cron expression is valid
- Check n8n execution logs for any errors

## Advanced Customization

### Changing the Message Format

Edit the **Format for Discord** node (Code node) to customize:
- Embed colors
- Message text
- Field layouts
- Additional information

### Multiple Daily Reminders

Duplicate the workflow and change the schedule trigger to different times.

### Different Topics for Different Times

Create multiple workflows with modified API calls to specify topic IDs.

## API Endpoint Details

The workflow uses the `/automation/daily-flashcard` endpoint:

**Endpoint**: `GET /automation/daily-flashcard`

**Authentication**: Bearer token (JWT)

**Response**:
```json
{
  "flashcard_id": 42,
  "topic_id": 5,
  "topic_name": "Python Basics",
  "question": "What is a decorator in Python?",
  "answer": "A function that modifies another",
  "difficulty": "medium",
  "user_progress": {
    "accuracy": 75.0,
    "streak_days": 5,
    "flashcards_reviewed": 23
  }
}
```

## Support

For issues with:
- **API**: Check the FastAPI logs and `/docs` endpoint
- **n8n**: Review execution logs in the n8n interface
- **Discord**: Verify webhook permissions and URL validity

