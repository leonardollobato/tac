"""Claude Code agent module for executing prompts programmatically."""

import subprocess
import sys
import os
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv
from data_types import (
    AgentPromptRequest,
    AgentPromptResponse,
    AgentTemplateRequest,
    ClaudeCodeResultMessage,
)

# Load environment variables
load_dotenv()

# Get Claude Code CLI path from environment
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")


def check_claude_installed() -> Optional[str]:
    """Check if Claude Code CLI is installed. Return error message if not."""
    try:
        result = subprocess.run(
            [CLAUDE_PATH, "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    except FileNotFoundError:
        return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    return None


def parse_jsonl_output(output_file: str) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse JSONL output file and return all messages and the result message.
    
    Returns:
        Tuple of (all_messages, result_message) where result_message is None if not found
    """
    try:
        with open(output_file, "r") as f:
            # Read all lines and parse each as JSON
            messages = [json.loads(line) for line in f if line.strip()]
            
            # Find the result message (should be the last one)
            result_message = None
            for message in reversed(messages):
                if message.get("type") == "result":
                    result_message = message
                    break
                    
            return messages, result_message
    except Exception as e:
        print(f"Error parsing JSONL file: {e}", file=sys.stderr)
        return [], None


def convert_jsonl_to_json(jsonl_file: str) -> str:
    """Convert JSONL file to JSON array file.
    
    Creates a .json file with the same name as the .jsonl file,
    containing all messages as a JSON array.
    
    Returns:
        Path to the created JSON file
    """
    # Create JSON filename by replacing .jsonl with .json
    json_file = jsonl_file.replace('.jsonl', '.json')
    
    # Parse the JSONL file
    messages, _ = parse_jsonl_output(jsonl_file)
    
    # Write as JSON array
    with open(json_file, 'w') as f:
        json.dump(messages, f, indent=2)
    
    print(f"Created JSON file: {json_file}")
    return json_file


def get_claude_env() -> Dict[str, str]:
    """Get only the required environment variables for Claude Code execution.
    
    Returns a dictionary containing only the necessary environment variables
    based on .env.sample configuration.
    
    Subprocess env behavior:
    - env=None → Inherits parent's environment (default)
    - env={} → Empty environment (no variables)
    - env=custom_dict → Only uses specified variables
    
    So this will work with gh authentication:
    # These are equivalent:
    result = subprocess.run(cmd, capture_output=True, text=True)
    result = subprocess.run(cmd, capture_output=True, text=True, env=None)
    
    But this will NOT work (no PATH, no auth):
    result = subprocess.run(cmd, capture_output=True, text=True, env={})
    """
    required_env_vars = {
        # Anthropic Configuration (required)
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        
        # Claude Code Configuration
        "CLAUDE_CODE_PATH": os.getenv("CLAUDE_CODE_PATH", "claude"),
        "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": os.getenv("CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR", "true"),
        
        # Agent Cloud Sandbox Environment (optional)
        "E2B_API_KEY": os.getenv("E2B_API_KEY"),
        
        # Basic environment variables Claude Code might need
        "HOME": os.getenv("HOME"),
        "USER": os.getenv("USER"),
        "PATH": os.getenv("PATH"),
        "SHELL": os.getenv("SHELL"),
        "TERM": os.getenv("TERM"),
    }
    
    # Only add GitHub tokens if GITHUB_PAT exists
    github_pat = os.getenv("GITHUB_PAT")
    if github_pat:
        required_env_vars["GITHUB_PAT"] = github_pat
        required_env_vars["GH_TOKEN"] = github_pat  # Claude Code uses GH_TOKEN
    
    # Filter out None values
    return {k: v for k, v in required_env_vars.items() if v is not None}


def save_prompt(prompt: str, adw_id: str, agent_name: str = "ops") -> None:
    """Save a prompt to the appropriate logging directory."""
    # Extract slash command from prompt
    match = re.match(r'^(/\w+)', prompt)
    if not match:
        return
    
    slash_command = match.group(1)
    # Remove leading slash for filename
    command_name = slash_command[1:]
    
    # Create directory structure at project root (parent of adws)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompt_dir = os.path.join(project_root, "agents", adw_id, agent_name, "prompts")
    os.makedirs(prompt_dir, exist_ok=True)
    
    # Save prompt to file
    prompt_file = os.path.join(prompt_dir, f"{command_name}.txt")
    with open(prompt_file, "w") as f:
        f.write(prompt)
    
    print(f"Saved prompt to: {prompt_file}")


def prompt_claude_code(request: AgentPromptRequest) -> AgentPromptResponse:
    """Execute Claude Code with the given prompt configuration."""

    # Check if Claude Code CLI is installed
    error_msg = check_claude_installed()
    if error_msg:
        return AgentPromptResponse(output=error_msg, success=False, session_id=None)
    
    # Save prompt before execution
    save_prompt(request.prompt, request.adw_id, request.agent_name)

    # Create output directory if needed
    output_dir = os.path.dirname(request.output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Build command - always use stream-json format and verbose
    cmd = [CLAUDE_PATH, "-p", request.prompt]
    cmd.extend(["--model", request.model])
    cmd.extend(["--output-format", "stream-json"])
    cmd.append("--verbose")

    # Add dangerous skip permissions flag if enabled
    if request.dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    # Set up environment with only required variables
    env = get_claude_env()

    try:
        # Execute Claude Code and pipe output to file
        with open(request.output_file, "w") as f:
            result = subprocess.run(
                cmd, stdout=f, stderr=subprocess.PIPE, text=True, env=env
            )

        if result.returncode == 0:
            print(f"Output saved to: {request.output_file}")
            
            # Parse the JSONL file
            messages, result_message = parse_jsonl_output(request.output_file)
            
            # Convert JSONL to JSON array file
            json_file = convert_jsonl_to_json(request.output_file)
            
            if result_message:
                # Extract session_id from result message
                session_id = result_message.get("session_id")
                
                # Check if there was an error in the result
                is_error = result_message.get("is_error", False)
                result_text = result_message.get("result", "")
                
                return AgentPromptResponse(
                    output=result_text, 
                    success=not is_error,
                    session_id=session_id
                )
            else:
                # No result message found, return raw output
                with open(request.output_file, "r") as f:
                    raw_output = f.read()
                return AgentPromptResponse(
                    output=raw_output, 
                    success=True,
                    session_id=None
                )
        else:
            error_msg = f"Claude Code error: {result.stderr}"
            print(error_msg, file=sys.stderr)
            return AgentPromptResponse(output=error_msg, success=False, session_id=None)

    except subprocess.TimeoutExpired:
        error_msg = "Error: Claude Code command timed out after 5 minutes"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False, session_id=None)
    except Exception as e:
        error_msg = f"Error executing Claude Code: {e}"
        print(error_msg, file=sys.stderr)
        return AgentPromptResponse(output=error_msg, success=False, session_id=None)


def execute_template(request: AgentTemplateRequest) -> AgentPromptResponse:
    """Execute a Claude Code template with slash command and arguments."""
    # Construct prompt from slash command and args
    prompt = f"{request.slash_command} {' '.join(request.args)}"
    
    # Create output directory with adw_id at project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(project_root, "agents", request.adw_id, request.agent_name)
    os.makedirs(output_dir, exist_ok=True)

    # Build output file path
    output_file = os.path.join(output_dir, "raw_output.jsonl")

    # Create prompt request with specific parameters
    prompt_request = AgentPromptRequest(
        prompt=prompt,
        adw_id=request.adw_id,
        agent_name=request.agent_name,
        model=request.model,
        dangerously_skip_permissions=True,
        output_file=output_file,
    )

    # Execute and return response (prompt_claude_code now handles all parsing)
    return prompt_claude_code(prompt_request)
