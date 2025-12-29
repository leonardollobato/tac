#!/bin/bash

# Delete a pull request and optionally its branch
# Usage: ./scripts/delete_pr.sh <pr-number> [--delete-branch]

set -e

# Check if PR number is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <pr-number> [--delete-branch]"
    echo "Example: $0 123"
    echo "Example: $0 123 --delete-branch"
    exit 1
fi

PR_NUMBER=$1
DELETE_BRANCH=false

# Check for --delete-branch flag
if [ "$2" = "--delete-branch" ]; then
    DELETE_BRANCH=true
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Get repository URL from git remote
GITHUB_REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$GITHUB_REPO_URL" ]; then
    echo "Error: Not in a git repository or no 'origin' remote found"
    exit 1
fi

# Extract repo path from URL
REPO_PATH=$(echo $GITHUB_REPO_URL | sed 's|https://github.com/||' | sed 's|.git$||')

# Set GitHub token for gh CLI if available
if [ -n "$GITHUB_PAT" ]; then
    export GH_TOKEN=$GITHUB_PAT
fi

echo "Fetching PR #$PR_NUMBER details..."

# Get PR details including branch name
PR_INFO=$(gh pr view $PR_NUMBER -R $REPO_PATH --json number,title,state,headRefName 2>/dev/null || echo "")

if [ -z "$PR_INFO" ]; then
    echo "Error: PR #$PR_NUMBER not found in $REPO_PATH"
    exit 1
fi

# Extract PR details
PR_TITLE=$(echo $PR_INFO | jq -r '.title')
PR_STATE=$(echo $PR_INFO | jq -r '.state')
PR_BRANCH=$(echo $PR_INFO | jq -r '.headRefName')

echo "PR #$PR_NUMBER: $PR_TITLE"
echo "State: $PR_STATE"
echo "Branch: $PR_BRANCH"

# Confirm deletion
echo
if [ "$DELETE_BRANCH" = true ]; then
    echo "⚠️  This will close PR #$PR_NUMBER and DELETE branch '$PR_BRANCH'"
    read -p "Are you sure? (y/N) " -n 1 -r
else
    echo "⚠️  This will close PR #$PR_NUMBER (branch will be kept)"
    read -p "Are you sure? (y/N) " -n 1 -r
fi
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

# Close the PR if it's open
if [ "$PR_STATE" = "OPEN" ]; then
    echo "Closing PR #$PR_NUMBER..."
    gh pr close $PR_NUMBER -R $REPO_PATH
else
    echo "PR is already closed"
fi

# Delete the branch if requested
if [ "$DELETE_BRANCH" = true ]; then
    echo "Deleting branch '$PR_BRANCH'..."
    
    # Delete remote branch
    git push origin --delete $PR_BRANCH 2>/dev/null || echo "Note: Could not delete remote branch (may already be deleted)"
    
    # Delete local branch if it exists
    if git show-ref --verify --quiet refs/heads/$PR_BRANCH; then
        # Make sure we're not on the branch we're trying to delete
        CURRENT_BRANCH=$(git branch --show-current)
        if [ "$CURRENT_BRANCH" = "$PR_BRANCH" ]; then
            echo "Switching to main branch first..."
            git checkout main
        fi
        git branch -D $PR_BRANCH 2>/dev/null || echo "Note: Could not delete local branch"
    fi
    
    echo "✅ Successfully closed PR #$PR_NUMBER and deleted branch '$PR_BRANCH'"
else
    echo "✅ Successfully closed PR #$PR_NUMBER (branch kept: '$PR_BRANCH')"
fi