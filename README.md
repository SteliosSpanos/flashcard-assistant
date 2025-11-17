# Flashcard Study Assistant

A modern, AI-powered flashcard API built with FastAPI and PostgreSQL. Create study topics, generate flashcards automatically using OpenAI, and track your learning progress with interactive study sessions.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Local Development](#local-development)
  - [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Authentication](#authentication)
  - [Managing Topics and Flashcards](#managing-topics-and-flashcards)
  - [Study Sessions](#study-sessions)
  - [Progress Tracking](#progress-tracking)
  - [Automation Endpoint](#automation-endpoint)
- [Discord Automation](#discord-automation)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [License](#license)

## Features

- **User Authentication**: Secure JWT-based authentication system with registration and login
- **Topic Management**: Organize flashcards into topics with full CRUD operations
- **AI-Powered Generation**: Automatically generate flashcards using OpenAI GPT-4o-mini based on topic and difficulty level
- **Manual Flashcard Creation**: Create and edit flashcards manually with question-answer pairs
- **Interactive Study Sessions**:
  - Randomized flashcard presentation
  - Real-time answer validation
  - Session-based progress tracking
  - Live accuracy calculations
- **Progress Analytics**:
  - Per-topic statistics (accuracy, cards reviewed, total attempts)
  - Study streak tracking with daily continuity detection
  - All-time performance metrics
- **Discord Automation**:
  - Automated daily flashcard reminders via bash script and cron
  - Smart topic selection (prioritizes topics with lowest accuracy)
  - Rich Discord embeds with color-coded difficulty levels
- **RESTful API**: Clean, well-documented API with automatic Swagger UI documentation
- **Docker Support**: Containerized deployment with docker-compose for easy setup

## Architecture

- **Backend Framework**: Python FastAPI 
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens using python-jose and bcrypt password hashing
- **AI Integration**: OpenAI API with structured JSON output for reliable flashcard generation
- **Session Management**: In-memory study session storage with UUID-based identification

**Data Model**:
```
User (1) ─── (N) Topic (1) ─── (N) Flashcard
  │                │
  └────────(N)─────┘
       UserProgress
```

Study sessions are temporary and stored in-memory during active study. Progress statistics are persisted to the database only when sessions complete successfully.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher (not required for Docker setup)
- OpenAI API key (required for AI flashcard generation feature)
- Docker and Docker Compose (optional, for containerized deployment)

## Installation

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/flashcard-assistant.git
   cd flashcard-assistant
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL database**:
   ```bash
   # Create a database for the application
   createdb flashcard_db
   ```

5. **Configure environment variables** (see [Configuration](#configuration))

6. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/flashcard-assistant.git
   cd flashcard-assistant
   ```

2. **Configure environment variables** (see [Configuration](#configuration))

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

   This will start both the PostgreSQL database and the FastAPI application.

4. **Verify deployment**:
   ```bash
   docker-compose ps
   ```

   The API will be available at `http://localhost:8000`

5. **View logs**:
   ```bash
   docker-compose logs -f web
   ```

6. **Stop the services**:
   ```bash
   docker-compose down
   ```

## Configuration

Create a `.env` file in the project root directory. You can use `.env.example` as a template:

```bash
cp .env.example .env
```

**Required environment variables**:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/flashcard_db` |
| `SECRET_KEY` | JWT signing key (use a strong random string) | `your-secure-random-secret-key-here` |
| `OPENAI_API_KEY` | OpenAI API key for AI flashcard generation | `sk-...` |

**For Docker Compose**, also configure these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_USER` | PostgreSQL username | `flashcard_user` |
| `DB_PASSWORD` | PostgreSQL password | `secure_password` |
| `DB_NAME` | PostgreSQL database name | `flashcard_db` |

**Generating a secure SECRET_KEY**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Note**: The database schema is automatically created on application startup. No manual migrations are required.

## Usage

### Authentication

**Register a new user**:
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student",
    "email": "student@example.com",
    "password": "securepass123"
  }'
```

**Login to receive JWT token**:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=student&password=securepass123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Include the token in subsequent requests**:
```bash
curl -X GET "http://localhost:8000/topics" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Managing Topics and Flashcards

**Create a new topic**:
```bash
curl -X POST "http://localhost:8000/topics" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Fundamentals",
    "description": "Core Python concepts and syntax"
  }'
```

**Generate flashcards with AI**:
```bash
curl -X POST "http://localhost:8000/topics/1/flashcards/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 5,
    "difficulty": "intermediate"
  }'
```

The AI will generate flashcards based on the topic name and specified difficulty level (beginner, intermediate or advanced).

**Create a flashcard manually**:
```bash
curl -X POST "http://localhost:8000/topics/1/flashcards" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is a Python decorator?",
    "answer": "A function that modifies another function"
  }'
```

### Study Sessions

**Start a study session**:
```bash
curl -X POST "http://localhost:8000/study/1/start" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response includes a `session_id` and the first flashcard:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic_id" : 1,
  "topic_name" : "Python Fundamentals",
  "total_flashcards" : 7,
  "current_index" : 1,
  "flashcard": {
    "id": 5,
    "question": "What is a Python decorator?",
    "answer": "A function that modifies another function"
  },
}
```

**Submit an answer**:
```bash
curl -X POST "http://localhost:8000/study/answer" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "flashcard_id": 5,
    "is_correct": true
  }'
```

**Get the next flashcard**:
```bash
curl -X GET "http://localhost:8000/study/next/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get session summary** (finalizes the session and updates progress):
```bash
curl -X GET "http://localhost:8000/study/summary/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{ 
  "session_id" : "550e8400-e29b-41d4-a716-446655440000",
  "topic_name" : "Python Fundamentals"
  "total_reviewed": 10,
  "correct_count": 8,
  "accuracy": 80.0,
  "streak_days" : 1
}
```

**Cancel a session** (without saving progress):
```bash
curl -X DELETE "http://localhost:8000/study/cancel/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Progress Tracking

**View progress for a specific topic**:
```bash
curl -X GET "http://localhost:8000/progress/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "topic_id": 1,
  "topic_name" : "Python Fundamentals"
  "flashcards_reviewed": 25,
  "accuracy": 80.0,
  "streak_days": 5,
  "last_study_date": "2025-10-31T10:30:00"
}
```

**Study Streak Logic**:
- Increments by 1 when you study on consecutive days
- Resets to 1 if you skip a day
- Remains unchanged if you study multiple times on the same day

### Automation Endpoint

**Get a daily flashcard** (for automated reminders):
```bash
curl -X GET "http://localhost:8000/automation/daily-flashcard" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
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

This endpoint automatically selects a flashcard from the topic where you need the most practice (lowest accuracy), making it ideal for automated daily reminders via bash scripts, Discord bots, or other automation tools.

## Discord Automation

Set up automated daily flashcard reminders sent directly to your Discord server using a bash script.

### Features

- **Automated Daily Reminders**: Schedule flashcards to be sent at specific times
- **Smart Topic Selection**: Automatically selects flashcards from your weakest topics
- **Rich Discord Embeds**: Beautiful, color-coded messages based on difficulty
  - 🟢 Green for Easy
  - 🟡 Yellow for Medium
  - 🔴 Red for Hard
- **Progress Stats**: Shows your current accuracy, streak, and cards reviewed

### Quick Setup

1. **Install jq** (JSON parser):
   ```bash
   sudo apt update && sudo apt install jq
   ```

2. **Create a Discord webhook** in your server:
   - Server Settings → Integrations → Webhooks → New Webhook
   - Copy the webhook URL

3. **Configure the script**:
   ```bash
   cd scripts
   cp config.example config
   nano config
   ```
   Fill in your API URL, username, password, and Discord webhook URL.

4. **Make the script executable**:
   ```bash
   chmod +x discord-flashcard-bot.sh
   ```

5. **Test it**:
   ```bash
   ./discord-flashcard-bot.sh
   ```

6. **Set up daily automation with cron**:
   ```bash
   crontab -e
   ```
   Add this line for 9:00 AM daily:
   ```
   0 9 * * * /bin/bash /path/to/flashcard-assistant/scripts/discord-flashcard-bot.sh >> /path/to/flashcard-assistant/scripts/cron.log 2>&1
   ```

### Example Discord Message

```
Daily Flashcard - 5 | Python Basics
Difficulty: Moderate

Time to keep your study streak going!

Question
What is a decorator in Python?

Answer
||A function that modifies another||

Your Progress
Accuracy: 75%
Streak: 5 days
Cards Reviewed: 23

Open the app to study and improve your progress!
```

**For detailed setup instructions**, see [`scripts/README.md`](scripts/README.md)

## API Documentation

Interactive API documentation is automatically generated and available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

The Swagger UI provides a comprehensive interface to:
- Explore all available endpoints
- View request/response schemas
- Test API calls directly from the browser
- Authenticate and interact with protected endpoints

### Core Endpoints

**Authentication**:
- `POST /auth/register` - Create a new user account
- `POST /auth/login` - Authenticate and receive JWT token

**Topics**:
- `GET /topics/` - List all topics for the authenticated user
- `POST /topics/` - Create a new topic
- `GET /topics/{topic_id}` - Get topic details
- `PATCH /topics/{topic_id}` - Update a topic
- `DELETE /topics/{topic_id}` - Delete a topic and all its flashcards

**Flashcards**:
- `GET /topics/{topic_id}/flashcards/` - List all flashcards for a topic
- `POST /topics/{topic_id}/flashcards/` - Create a flashcard manually
- `POST /topics/{topic_id}/flashcards/generate` - Generate flashcards with AI
- `GET /topics/{topic_id}/flashcards/{flashcard_id}` - Get flashcard details
- `PATCH /topics/{topic_id}/flashcards/{flashcard_id}` - Update a flashcard
- `DELETE /topics/{topic_id}/flashcards/{flashcard_id}` - Delete a flashcard

**Study Sessions**:
- `POST /study/{topic_id}/start` - Start a new study session
- `POST /study/answer` - Submit an answer for the current flashcard
- `GET /study/next/{session_id}` - Get the next flashcard in the session
- `GET /study/summary/{session_id}` - Complete session and get summary
- `DELETE /study/cancel/{session_id}` - Cancel an active session

**Progress**:
- `GET /progress/{topic_id}` - Get progress statistics for a topic
- `GET /progress/` - Get all-time progress across all the topics
- `DELETE /progress/{topic_id}` - Delete the progress in a topic

**Automation**:
- `GET /automation/daily-flashcard` - Get a flashcard for automated reminders
  - Returns flashcard from topic with lowest accuracy
  - Includes user progress stats (accuracy, streak, cards reviewed)
  - Designed for bash scripts and Discord integration

## Project Structure

```
flashcard-assistant/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── database.py                # Database connection and session management
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── schemas.py                 # Pydantic request/response models
│   ├── auth.py                    # JWT authentication logic
│   ├── settings.py                # Configuration management
│   └── routes/
│       ├── authentication.py      # User registration and login
│       ├── topics.py              # Topic CRUD operations
│       ├── flashcards.py          # Flashcard management and AI generation
│       ├── study.py               # Study session management
│       ├── progress.py            # Progress tracking and statistics
│       └── automation.py          # Automation endpoints for integrations
├── scripts/
│   ├── discord-flashcard-bot.sh   # Bash script for Discord automation
│   ├── config.example             # Configuration template
│   └── README.md                  # Script setup guide
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker image definition
├── docker-compose.yml             # Multi-container Docker setup
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore rules
├── LICENSE                        # MIT License
└── README.md                      # This file
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Contributing**: Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

**Support**: For questions or issues, please open a GitHub issue with detailed information about your environment and the problem you're encountering.

