#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv"]
# ///

"""
GitHub Webhook Trigger - AI Developer Workflow (ADW)

FastAPI webhook endpoint that receives GitHub issue events and triggers ADW workflows.
Responds immediately to meet GitHub's 10-second timeout by launching adw_plan_build.py
in the background.

Usage: uv run trigger_webhook.py

Environment Requirements:
- PORT: Server port (default: 8001)
- All adw_plan_build.py requirements (GITHUB_PAT, ANTHROPIC_API_KEY, etc.)
"""

import os
import subprocess
import sys
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
from utils import make_adw_id

# Load environment variables
load_dotenv()

# Configuration
PORT = int(os.getenv("PORT", "8001"))

# Create FastAPI app
app = FastAPI(title="ADW Webhook Trigger", description="GitHub webhook endpoint for ADW")

print(f"Starting ADW Webhook Trigger on port {PORT}")


@app.post("/gh-webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook events."""
    try:
        # Get event type from header
        event_type = request.headers.get("X-GitHub-Event", "")
        
        # Parse webhook payload
        payload = await request.json()
        
        # Extract event details
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_number = issue.get("number")
        
        print(f"Received webhook: event={event_type}, action={action}, issue_number={issue_number}")
        
        should_trigger = False
        trigger_reason = ""
        
        # Check if this is an issue opened event
        if event_type == "issues" and action == "opened" and issue_number:
            should_trigger = True
            trigger_reason = "New issue opened"
        
        # Check if this is an issue comment with 'adw' text
        elif event_type == "issue_comment" and action == "created" and issue_number:
            comment = payload.get("comment", {})
            comment_body = comment.get("body", "").strip().lower()
            
            print(f"Comment body: '{comment_body}'")
            
            if comment_body == "adw":
                should_trigger = True
                trigger_reason = "Comment with 'adw' command"
        
        if should_trigger:
            # Generate ADW ID for this workflow
            adw_id = make_adw_id()
            
            # Build command to run adw_plan_build.py with adw_id
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            trigger_script = os.path.join(script_dir, "adw_plan_build.py")
            
            cmd = ["uv", "run", trigger_script, str(issue_number), adw_id]
            
            print(f"Launching background process: {' '.join(cmd)} (reason: {trigger_reason})")
            
            # Launch in background using Popen
            # Run from project root - adw_plan_build.py will handle its own logging
            process = subprocess.Popen(
                cmd,
                cwd=project_root,  # Run from project root, not adws directory
                env=os.environ.copy()  # Pass all environment variables
            )
            
            print(f"Background process started for issue #{issue_number} with ADW ID: {adw_id}")
            print(f"Logs will be written to: agents/{adw_id}/adw_plan_build/execution.log")
            
            # Return immediately
            return {
                "status": "accepted",
                "issue": issue_number,
                "adw_id": adw_id,
                "message": f"ADW workflow triggered for issue #{issue_number}",
                "reason": trigger_reason,
                "logs": f"agents/{adw_id}/adw_plan_build/"
            }
        else:
            print(f"Ignoring webhook: event={event_type}, action={action}, issue_number={issue_number}")
            return {
                "status": "ignored",
                "reason": f"Not a triggering event (event={event_type}, action={action})"
            }
            
    except Exception as e:
        print(f"Error processing webhook: {e}")
        # Always return 200 to GitHub to prevent retries
        return {
            "status": "error",
            "message": "Internal error processing webhook"
        }


@app.get("/health")
async def health():
    """Health check endpoint - runs comprehensive system health check."""
    try:
        # Run the health check script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        health_check_script = os.path.join(script_dir, "health_check.py")
        
        # Run health check with timeout
        result = subprocess.run(
            ["uv", "run", health_check_script],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=script_dir
        )
        
        # Print the health check output for debugging
        print("=== Health Check Output ===")
        print(result.stdout)
        if result.stderr:
            print("=== Health Check Errors ===")
            print(result.stderr)
        
        # Parse the output - look for the overall status
        output_lines = result.stdout.strip().split('\n')
        is_healthy = result.returncode == 0
        
        # Extract key information from output
        warnings = []
        errors = []
        
        capturing_warnings = False
        capturing_errors = False
        
        for line in output_lines:
            if "⚠️  Warnings:" in line:
                capturing_warnings = True
                capturing_errors = False
                continue
            elif "❌ Errors:" in line:
                capturing_errors = True
                capturing_warnings = False
                continue
            elif "📝 Next Steps:" in line:
                break
            
            if capturing_warnings and line.strip().startswith("-"):
                warnings.append(line.strip()[2:])
            elif capturing_errors and line.strip().startswith("-"):
                errors.append(line.strip()[2:])
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "service": "adw-webhook-trigger",
            "health_check": {
                "success": is_healthy,
                "warnings": warnings,
                "errors": errors,
                "details": "Run health_check.py directly for full report"
            }
        }
        
    except subprocess.TimeoutExpired:
        return {
            "status": "unhealthy",
            "service": "adw-webhook-trigger",
            "error": "Health check timed out"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "service": "adw-webhook-trigger",
            "error": f"Health check failed: {str(e)}"
        }


if __name__ == "__main__":
    print(f"Starting server on http://0.0.0.0:{PORT}")
    print(f"Webhook endpoint: POST /gh-webhook")
    print(f"Health check: GET /health")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT)