#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "schedule",
#     "python-dotenv",
#     "pydantic",
# ]
# ///

"""
Cron-based ADW trigger system that monitors GitHub issues and automatically processes them.

This script polls GitHub every 20 seconds to detect:
1. New issues without comments
2. Issues where the latest comment contains 'adw'

When a qualifying issue is found, it triggers the existing manual workflow script.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Set, Optional

import schedule
from dotenv import load_dotenv

from github import fetch_open_issues, fetch_issue_comments, get_repo_url, extract_repo_path

# Load environment variables from current or parent directories
load_dotenv()

# Optional environment variables
GITHUB_PAT = os.getenv("GITHUB_PAT")

# Get repository URL from git remote
try:
    GITHUB_REPO_URL = get_repo_url()
    REPO_PATH = extract_repo_path(GITHUB_REPO_URL)
except ValueError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# Track processed issues
processed_issues: Set[int] = set()
# Track issues with their last processed comment ID
issue_last_comment: Dict[int, Optional[int]] = {}

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    print(f"\nINFO: Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def should_process_issue(issue_number: int) -> bool:
    """Determine if an issue should be processed based on comments."""
    comments = fetch_issue_comments(REPO_PATH, issue_number)
    
    # If no comments, it's a new issue - process it
    if not comments:
        print(f"INFO: Issue #{issue_number} has no comments - marking for processing")
        return True
    
    # Get the latest comment
    latest_comment = comments[-1]
    comment_body = latest_comment.get("body", "").lower()
    comment_id = latest_comment.get("id")
    
    # Check if we've already processed this comment
    last_processed_comment = issue_last_comment.get(issue_number)
    if last_processed_comment == comment_id:
        # DEBUG level - not printing
        return False
    
    # Check if latest comment is exactly 'adw' (after stripping whitespace)
    if comment_body.strip() == "adw":
        print(f"INFO: Issue #{issue_number} - latest comment is 'adw' - marking for processing")
        issue_last_comment[issue_number] = comment_id
        return True
    
    # DEBUG level - not printing
    return False


def trigger_adw_workflow(issue_number: int) -> bool:
    """Trigger the ADW plan and build workflow for a specific issue."""
    try:
        script_path = Path(__file__).parent / "adw_plan_build.py"
        
        print(f"INFO: Triggering ADW workflow for issue #{issue_number}")
        
        cmd = [sys.executable, str(script_path), str(issue_number)]
        
        # Run the manual trigger script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_path.parent
        )
        
        if result.returncode == 0:
            print(f"INFO: Successfully triggered workflow for issue #{issue_number}")
            # DEBUG level - not printing output
            return True
        else:
            print(f"ERROR: Failed to trigger workflow for issue #{issue_number}")
            print(f"ERROR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"ERROR: Exception while triggering workflow for issue #{issue_number}: {e}")
        return False


def check_and_process_issues():
    """Main function that checks for issues and processes qualifying ones."""
    if shutdown_requested:
        print(f"INFO: Shutdown requested, skipping check cycle")
        return
    
    start_time = time.time()
    print(f"INFO: Starting issue check cycle")
    
    try:
        # Fetch all open issues
        issues = fetch_open_issues(REPO_PATH)
        
        if not issues:
            print(f"INFO: No open issues found")
            return
        
        # Track newly qualified issues
        new_qualifying_issues = []
        
        # Check each issue
        for issue in issues:
            issue_number = issue.number
            if not issue_number:
                continue
            
            # Skip if already processed in this session
            if issue_number in processed_issues:
                continue
            
            # Check if issue should be processed
            if should_process_issue(issue_number):
                new_qualifying_issues.append(issue_number)
        
        # Process qualifying issues
        if new_qualifying_issues:
            print(f"INFO: Found {len(new_qualifying_issues)} new qualifying issues: {new_qualifying_issues}")
            
            for issue_number in new_qualifying_issues:
                if shutdown_requested:
                    print(f"INFO: Shutdown requested, stopping issue processing")
                    break
                
                # Trigger the workflow
                if trigger_adw_workflow(issue_number):
                    processed_issues.add(issue_number)
                else:
                    print(f"WARNING: Failed to process issue #{issue_number}, will retry in next cycle")
        else:
            print(f"INFO: No new qualifying issues found")
        
        # Log performance metrics
        cycle_time = time.time() - start_time
        print(f"INFO: Check cycle completed in {cycle_time:.2f} seconds")
        print(f"INFO: Total processed issues in session: {len(processed_issues)}")
        
    except Exception as e:
        print(f"ERROR: Error during check cycle: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the cron trigger."""
    print(f"INFO: Starting ADW cron trigger")
    print(f"INFO: Repository: {REPO_PATH}")
    print(f"INFO: Polling interval: 20 seconds")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Schedule the check function
    schedule.every(20).seconds.do(check_and_process_issues)
    
    # Run initial check immediately
    check_and_process_issues()
    
    # Main loop
    print(f"INFO: Entering main scheduling loop")
    while not shutdown_requested:
        schedule.run_pending()
        time.sleep(1)
    
    print(f"INFO: Shutdown complete")


if __name__ == "__main__":
    # Support --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print(__doc__)
        print("\nUsage: ./trigger_cron.py")
        print("\nEnvironment variables:")
        print("  GITHUB_PAT - (Optional) GitHub Personal Access Token")
        print("\nThe script will poll GitHub issues every 20 seconds and trigger")
        print("the ADW workflow for qualifying issues.")
        print("\nNote: Repository URL is automatically detected from git remote.")
        sys.exit(0)
    
    main()