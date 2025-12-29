#!/bin/bash

# Kill the trigger_webhook.py process

echo "Stopping trigger_webhook.py server..."

# Find and kill the process
if pgrep -f "trigger_webhook.py" > /dev/null; then
    pkill -f "trigger_webhook.py"
    echo "✓ Webhook server stopped"
else
    echo "⚠ No webhook server process found"
fi

# Also check for any uvicorn processes on port 8001
if lsof -i :8001 > /dev/null 2>&1; then
    echo "Found process on port 8001, killing..."
    lsof -ti :8001 | xargs kill -9 2>/dev/null
    echo "✓ Port 8001 cleared"
fi

echo "Done."