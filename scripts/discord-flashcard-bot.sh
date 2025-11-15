#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config"
LOG_FILE="$SCRIPT_DIR/flashcard-bot.log"

log() {
	echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
	log "ERROR: $1"
	exit 1
}

if [! -f "$CONFIG_FILE" ]; then
	error_exit "Config file not found at $CONFIG_FILE. Please create it from config.example"
fi

source $CONFIG_FILE

[ -z "$API_BASE_URL" ] && error_exit "API_BASE_URL not set in config"
[ -z "$API_USERNAME" ] && error_exit "API_USERNAME not set in config"
[ -z "$API_PASSWORD" ] && error_exit "API_PASSWORD not set in config"
[ -z "$DISCORD_WEBHOOK_URL" ] && error_exit "DISCORD_WEBHOOK_URL not set in config"

log "Starting Discord flashacard bot..."

log "Logging in to API at $API_BASE_URL..."
LOGIN_RESPONSE=$(curl -X POST "$API_BASE_URL/auth/login" -H "Content-Type: x-www-form-urlencoded" -d "username=$API_USERNAME&password=$API_PASSWORD")

if [[ $? -ne 0 ]]; then          # $? : exit status of last command
	error_exit "Failed to connect to API at $API_BASE_URL"
fi

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r ".access_token")         # extract raw the contents of 'access_token' field

if [ -z "$ACCESS_TOKEN" ] || [ "$ACCESS_TOKEN" == "null"]; then
	error_exit "Failed to get access token. Check your credentials"
fi

log "Successfully authenticated!"

log "Fetching daily flashcard..."
FLASHCARD_RESPONSE=$(curl -X GET "$API_BASE_URL/automation/daily-flashcard" -H "Authorization: Bearer $ACCESS_TOKEN")

if [ $? -ne 0 ]; then
	error_exit "Failed to fetch flashcard from API"
fi


FLASHCARD_ID=$(echo "$FLASHCARD_RESPONSE" | jq -r ".flashcard_id")
TOPIC_NAME=$(echo "$FLASHCARD_RESPONSE" | jq -r ".topic_name")
QUESTION=$(echo "$FLASHCARD_RESPONSE" | jq -r ".question")
ANSWER=$(echo "$FLASHCARD_RESPONSE" | jq -r ".answer")
DIFFICULTY=$(echo "$FLASHCARD_RESPONSE" | jq -r ".difficulty")
ACCURACY=$(echo "$FLASHCARD_RESPONSE" | jq -r ".user_progress.accuracy")
STREAK=$(echo "$FLASHCARD_RESPONSE" | jq -r ".user_progress.streak_days")
CARDS_REVIEWED=$(echo "$FLASHCARD_RESPONSE" | jq -r ".user_progress.flashcards_reviewed")

if [ -z "$FLASHCARD_ID" ] || [ "$FLASHCARD_ID" == "null" ]; then
	error_exit "Failed to parse flashcard data. Response: $FLASHCARD_RESPONSE"
fi

log "Fetched flashcard: $FLASHCARD_ID - $TOPIC_NAME - $DIFFICULTY"


case "${DIFFICULTY,,}" in        # all lowercase
	easy)
		COLOR=5763719
		;;
	moderate)
		COLOR=16776960
		;;
	hard)
		COLOR=15548997
		;;
	*)
		COLOR=3447003
		;;
esac


DIFFICULTY_DISPLAY="${DIFFICULTY^}"    # uppercase first letter

# heredoc : set the variale with the text marked by the EOF
DISCORD_PAYLOAD=$(cat <<EOF    
  {
    "embeds": [{
      "title": "Daily Flashcard - $FLASHCARD_ID | $TOPIC_NAME",
      "description": "**Difficulty:** $DIFFICULTY_DISPLAY\n\nTime to keep your study streak going!",
      "color": $COLOR,
      "fields": [
        {
          "name": "Question",
          "value": "$QUESTION",
          "inline": false
        },
        {
          "name": "Answer",
          "value": "||$ANSWER||",
          "inline": false
        },
        {
          "name": "Your Progress",
          "value": "**Accuracy:** ${ACCURACY}%\n**Streak:** $STREAK days\n**Cards Reviewed:** $CARDS_REVIEWED",
          "inline": false
        }
      ],
      "footer": {
        "text": "Open the app to study and improve your progress!"
      },
      "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
    }]
  }
EOF
)

log "Sending to Discord..."
DISCORD_RESPONSE=$(curl -s -X POST "$DISCORD_WEBHOOK_URL" -H "Content-Type: application/json" -d "$DISCORD_PAYLOAD")

if [ $? -ne 0 ]; then
	error_exit "Failed to send message to Discord"
fi

log "Successfully sent flashcard to Discord"
log "Flashcard ID: $FLASHCARD_ID | Topic: $TOPIC_NAME | Difficulty: $DIFFICULTY | Accuracy: ${ACCURACY}%"


