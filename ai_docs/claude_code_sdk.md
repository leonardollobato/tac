[Anthropic home page![light logo](https://mintlify.s3.us-west-1.amazonaws.com/anthropic/logo/light.svg)![dark logo](https://mintlify.s3.us-west-1.amazonaws.com/anthropic/logo/dark.svg)](https://docs.anthropic.com/)

English

Search...

Ctrl K

Search...

Navigation

Build with Claude

Claude Code SDK

[Welcome](https://docs.anthropic.com/en/home) [Developer Guide](https://docs.anthropic.com/en/docs/intro) [API Guide](https://docs.anthropic.com/en/api/overview) [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) [Model Context Protocol (MCP)](https://docs.anthropic.com/en/docs/mcp) [Resources](https://docs.anthropic.com/en/resources/overview) [Release Notes](https://docs.anthropic.com/en/release-notes/overview)

The Claude Code SDK enables running Claude Code as a subprocess, providing a way to build AI-powered coding assistants and tools that leverage Claude's capabilities.

The SDK is available for command line, TypeScript, and Python usage.

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#authentication)  Authentication

The Claude Code SDK supports multiple authentication methods:

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#anthropic-api-key)  Anthropic API key

To use the Claude Code SDK directly with Anthropic's API, we recommend creating a dedicated API key:

1. Create an Anthropic API key in the [Anthropic Console](https://console.anthropic.com/)
2. Then, set the `ANTHROPIC_API_KEY` environment variable. We recommend storing this key securely (e.g., using a Github [secret](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions))

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#third-party-api-credentials)  Third-Party API credentials

The SDK also supports third-party API providers:

- **Amazon Bedrock**: Set `CLAUDE_CODE_USE_BEDROCK=1` environment variable and configure AWS credentials
- **Google Vertex AI**: Set `CLAUDE_CODE_USE_VERTEX=1` environment variable and configure Google Cloud credentials

For detailed configuration instructions for third-party providers, see the [Amazon Bedrock](https://docs.anthropic.com/en/docs/claude-code/amazon-bedrock) and [Google Vertex AI](https://docs.anthropic.com/en/docs/claude-code/google-vertex-ai) documentation.

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#basic-sdk-usage)  Basic SDK usage

The Claude Code SDK allows you to use Claude Code in non-interactive mode from your applications.

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#command-line)  Command line

Here are a few basic examples for the command line SDK:

Copy

```bash
# Run a single prompt and exit (print mode)
$ claude -p "Write a function to calculate Fibonacci numbers"

# Using a pipe to provide stdin
$ echo "Explain this code" | claude -p

# Output in JSON format with metadata
$ claude -p "Generate a hello world function" --output-format json

# Stream JSON output as it arrives
$ claude -p "Build a React component" --output-format stream-json

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#typescript)  TypeScript

The TypeScript SDK is included in the main [`@anthropic-ai/claude-code`](https://www.npmjs.com/package/@anthropic-ai/claude-code) package on NPM:

Copy

```ts
import { query, type SDKMessage } from "@anthropic-ai/claude-code";

const messages: SDKMessage[] = [];

for await (const message of query({
  prompt: "Write a haiku about foo.py",
  abortController: new AbortController(),
  options: {
    maxTurns: 3,
  },
})) {
  messages.push(message);
}

console.log(messages);

```

The TypeScript SDK accepts all arguments supported by the command line SDK, as well as:

| Argument | Description | Default |
| --- | --- | --- |
| `abortController` | Abort controller | `new AbortController()` |
| `cwd` | Current working directory | `process.cwd()` |
| `executable` | Which JavaScript runtime to use | `node` when running with Node.js, `bun` when running with Bun |
| `executableArgs` | Arguments to pass to the executable | `[]` |
| `pathToClaudeCodeExecutable` | Path to the Claude Code executable | Executable that ships with `@anthropic-ai/claude-code` |

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#python)  Python

The Python SDK is available as [`claude-code-sdk`](https://github.com/anthropics/claude-code-sdk-python) on PyPI:

Copy

```bash
pip install claude-code-sdk

```

**Prerequisites:**

- Python 3.10+
- Node.js
- Claude Code CLI: `npm install -g @anthropic-ai/claude-code`

Basic usage:

Copy

```python
import anyio
from claude_code_sdk import query, ClaudeCodeOptions, Message

async def main():
    messages: list[Message] = []

    async for message in query(
        prompt="Write a haiku about foo.py",
        options=ClaudeCodeOptions(max_turns=3)
    ):
        messages.append(message)

    print(messages)

anyio.run(main)

```

The Python SDK accepts all arguments supported by the command line SDK through the `ClaudeCodeOptions` class:

Copy

```python
from claude_code_sdk import query, ClaudeCodeOptions
from pathlib import Path

options = ClaudeCodeOptions(
    max_turns=3,
    system_prompt="You are a helpful assistant",
    cwd=Path("/path/to/project"),  # Can be string or Path
    allowed_tools=["Read", "Write", "Bash"],
    permission_mode="acceptEdits"
)

async for message in query(prompt="Hello", options=options):
    print(message)

```

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#advanced-usage)  Advanced usage

The documentation below uses the command line SDK as an example, but can also be used with the TypeScript and Python SDKs.

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#multi-turn-conversations)  Multi-turn conversations

For multi-turn conversations, you can resume conversations or continue from the most recent session:

Copy

```bash
# Continue the most recent conversation
$ claude --continue

# Continue and provide a new prompt
$ claude --continue "Now refactor this for better performance"

# Resume a specific conversation by session ID
$ claude --resume 550e8400-e29b-41d4-a716-446655440000

# Resume in print mode (non-interactive)
$ claude -p --resume 550e8400-e29b-41d4-a716-446655440000 "Update the tests"

# Continue in print mode (non-interactive)
$ claude -p --continue "Add error handling"

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#custom-system-prompts)  Custom system prompts

You can provide custom system prompts to guide Claude's behavior:

Copy

```bash
# Override system prompt (only works with --print)
$ claude -p "Build a REST API" --system-prompt "You are a senior backend engineer. Focus on security, performance, and maintainability."

# System prompt with specific requirements
$ claude -p "Create a database schema" --system-prompt "You are a database architect. Use PostgreSQL best practices and include proper indexing."

```

You can also append instructions to the default system prompt:

Copy

```bash
# Append system prompt (only works with --print)
$ claude -p "Build a REST API" --append-system-prompt "After writing code, be sure to code review yourself."

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#mcp-configuration)  MCP Configuration

The Model Context Protocol (MCP) allows you to extend Claude Code with additional tools and resources from external servers. Using the `--mcp-config` flag, you can load MCP servers that provide specialized capabilities like database access, API integrations, or custom tooling.

Create a JSON configuration file with your MCP servers:

Copy

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [\
        "-y",\
        "@modelcontextprotocol/server-filesystem",\
        "/path/to/allowed/files"\
      ]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your-github-token"
      }
    }
  }
}

```

Then use it with Claude Code:

Copy

```bash
# Load MCP servers from configuration
$ claude -p "List all files in the project" --mcp-config mcp-servers.json

# Important: MCP tools must be explicitly allowed using --allowedTools
# MCP tools follow the format: mcp__$serverName__$toolName
$ claude -p "Search for TODO comments" \
  --mcp-config mcp-servers.json \
  --allowedTools "mcp__filesystem__read_file,mcp__filesystem__list_directory"

# Use an MCP tool for handling permission prompts in non-interactive mode
$ claude -p "Deploy the application" \
  --mcp-config mcp-servers.json \
  --allowedTools "mcp__permissions__approve" \
  --permission-prompt-tool mcp__permissions__approve

```

When using MCP tools, you must explicitly allow them using the `--allowedTools` flag. MCP tool names follow the pattern `mcp__<serverName>__<toolName>` where:

- `serverName` is the key from your MCP configuration file
- `toolName` is the specific tool provided by that server

This security measure ensures that MCP tools are only used when explicitly permitted.

If you specify just the server name (i.e., `mcp__<serverName>`), all tools from that server will be allowed.

Glob patterns (e.g., `mcp__go*`) are not supported.

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#custom-permission-prompt-tool)  Custom permission prompt tool

Optionally, use `--permission-prompt-tool` to pass in an MCP tool that we will use to check whether or not the user grants the model permissions to invoke a given tool. When the model invokes a tool the following happens:

1. We first check permission settings: all [settings.json files](https://docs.anthropic.com/en/docs/claude-code/settings), as well as `--allowedTools` and `--disallowedTools` passed into the SDK; if one of these allows or denies the tool call, we proceed with the tool call
2. Otherwise, we invoke the MCP tool you provided in `--permission-prompt-tool`

The `--permission-prompt-tool` MCP tool is passed the tool name and input, and must return a JSON-stringified payload with the result. The payload must be one of:

Copy

```ts
// tool call is allowed
{
  "behavior": "allow",
  "updatedInput": {...}, // updated input, or just return back the original input
}

// tool call is denied
{
  "behavior": "deny",
  "message": "..." // human-readable string explaining why the permission was denied
}

```

For example, a TypeScript MCP permission prompt tool implementation might look like this:

Copy

```ts
const server = new McpServer({
  name: "Test permission prompt MCP Server",
  version: "0.0.1",
});

server.tool(
  "approval_prompt",
  'Simulate a permission check - approve if the input contains "allow", otherwise deny',
  {
    tool_name: z.string().describe("The tool requesting permission"),
    input: z.object({}).passthrough().describe("The input for the tool"),
  },
  async ({ tool_name, input }) => {
    return {
      content: [\
        {\
          type: "text",\
          text: JSON.stringify(\
            JSON.stringify(input).includes("allow")\
              ? {\
                  behavior: "allow",\
                  updatedInput: input,\
                }\
              : {\
                  behavior: "deny",\
                  message: "Permission denied by test approval_prompt tool",\
                }\
          ),\
        },\
      ],
    };
  }
);

```

To use this tool, add your MCP server (eg. with `--mcp-config`), then invoke the SDK like so:

Copy

```sh
claude -p "..." \
  --permission-prompt-tool mcp__test-server__approval_prompt \
  --mcp-config my-config.json

```

Usage notes:

- Use `updatedInput` to tell the model that the permission prompt mutated its input; otherwise, set `updatedInput` to the original input, as in the example above. For example, if the tool shows a file edit diff to the user and lets them edit the diff manually, the permission prompt tool should return that updated edit.
- The payload must be JSON-stringified

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#available-cli-options)  Available CLI options

The SDK leverages all the CLI options available in Claude Code. Here are the key ones for SDK usage:

| Flag | Description | Example |
| --- | --- | --- |
| `--print`, `-p` | Run in non-interactive mode | `claude -p "query"` |
| `--output-format` | Specify output format ( `text`, `json`, `stream-json`) | `claude -p --output-format json` |
| `--resume`, `-r` | Resume a conversation by session ID | `claude --resume abc123` |
| `--continue`, `-c` | Continue the most recent conversation | `claude --continue` |
| `--verbose` | Enable verbose logging | `claude --verbose` |
| `--max-turns` | Limit agentic turns in non-interactive mode | `claude --max-turns 3` |
| `--system-prompt` | Override system prompt (only with `--print`) | `claude --system-prompt "Custom instruction"` |
| `--append-system-prompt` | Append to system prompt (only with `--print`) | `claude --append-system-prompt "Custom instruction"` |
| `--allowedTools` | Space-separated list of allowed tools, or <br> string of comma-separated list of allowed tools | `claude --allowedTools mcp__slack mcp__filesystem`<br>`claude --allowedTools "Bash(npm install),mcp__filesystem"` |
| `--disallowedTools` | Space-separated list of denied tools, or <br> string of comma-separated list of denied tools | `claude --disallowedTools mcp__splunk mcp__github`<br>`claude --disallowedTools "Bash(git commit),mcp__github"` |
| `--mcp-config` | Load MCP servers from a JSON file | `claude --mcp-config servers.json` |
| `--permission-prompt-tool` | MCP tool for handling permission prompts (only with `--print`) | `claude --permission-prompt-tool mcp__auth__prompt` |

For a complete list of CLI options and features, see the [CLI reference](https://docs.anthropic.com/en/docs/claude-code/cli-reference) documentation.

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#output-formats)  Output formats

The SDK supports multiple output formats:

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#text-output-default)  Text output (default)

Returns just the response text:

Copy

```bash
$ claude -p "Explain file src/components/Header.tsx"
# Output: This is a React component showing...

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#json-output)  JSON output

Returns structured data including metadata:

Copy

```bash
$ claude -p "How does the data layer work?" --output-format json

```

Response format:

Copy

```json
{
  "type": "result",
  "subtype": "success",
  "total_cost_usd": 0.003,
  "is_error": false,
  "duration_ms": 1234,
  "duration_api_ms": 800,
  "num_turns": 6,
  "result": "The response text here...",
  "session_id": "abc123"
}

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#streaming-json-output)  Streaming JSON output

Streams each message as it is received:

Copy

```bash
$ claude -p "Build an application" --output-format stream-json

```

Each conversation begins with an initial `init` system message, followed by a list of user and assistant messages, followed by a final `result` system message with stats. Each message is emitted as a separate JSON object.

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#message-schema)  Message schema

Messages returned from the JSON API are strictly typed according to the following schema:

Copy

```ts
type SDKMessage =
  // An assistant message
  | {
      type: "assistant";
      message: Message; // from Anthropic SDK
      session_id: string;
    }

  // A user message
  | {
      type: "user";
      message: MessageParam; // from Anthropic SDK
      session_id: string;
    }

  // Emitted as the last message
  | {
      type: "result";
      subtype: "success";
      duration_ms: float;
      duration_api_ms: float;
      is_error: boolean;
      num_turns: int;
      result: string;
      session_id: string;
      total_cost_usd: float;
    }

  // Emitted as the last message, when we've reached the maximum number of turns
  | {
      type: "result";
      subtype: "error_max_turns" | "error_during_execution";
      duration_ms: float;
      duration_api_ms: float;
      is_error: boolean;
      num_turns: int;
      session_id: string;
      total_cost_usd: float;
    }

  // Emitted as the first message at the start of a conversation
  | {
      type: "system";
      subtype: "init";
      apiKeySource: string;
      cwd: string;
      session_id: string;
      tools: string[];
      mcp_servers: {
        name: string;
        status: string;
      }[];
      model: string;
      permissionMode: "default" | "acceptEdits" | "bypassPermissions" | "plan";
    };

```

We will soon publish these types in a JSONSchema-compatible format. We use semantic versioning for the main Claude Code package to communicate breaking changes to this format.

`Message` and `MessageParam` types are available in Anthropic SDKs. For example, see the Anthropic [TypeScript](https://github.com/anthropics/anthropic-sdk-typescript) and [Python](https://github.com/anthropics/anthropic-sdk-python/) SDKs.

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#input-formats)  Input formats

The SDK supports multiple input formats:

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#text-input-default)  Text input (default)

Input text can be provided as an argument:

Copy

```bash
$ claude -p "Explain this code"

```

Or input text can be piped via stdin:

Copy

```bash
$ echo "Explain this code" | claude -p

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#streaming-json-input)  Streaming JSON input

A stream of messages provided via `stdin` where each message represents a user turn. This allows multiple turns of a conversation without re-launching the `claude` binary and allows providing guidance to the model while it is processing a request.

Each message is a JSON 'User message' object, following the same format as the output message schema. Messages are formatted using the [jsonl](https://jsonlines.org/) format where each line of input is a complete JSON object. Streaming JSON input requires `-p` and `--output-format stream-json`.

Currently this is limited to text-only user messages.

Copy

```bash
$ echo '{"type":"user","message":{"role":"user","content":[{"type":"text","text":"Explain this code"}]}}' | claude -p --output-format=stream-json --input-format=stream-json --verbose

```

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#examples)  Examples

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#simple-script-integration)  Simple script integration

Copy

```bash
#!/bin/bash

# Simple function to run Claude and check exit code
run_claude() {
    local prompt="$1"
    local output_format="${2:-text}"

    if claude -p "$prompt" --output-format "$output_format"; then
        echo "Success!"
    else
        echo "Error: Claude failed with exit code $?" >&2
        return 1
    fi
}

# Usage examples
run_claude "Write a Python function to read CSV files"
run_claude "Optimize this database query" "json"

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#processing-files-with-claude)  Processing files with Claude

Copy

```bash
# Process a file through Claude
$ cat mycode.py | claude -p "Review this code for bugs"

# Process multiple files
$ for file in *.js; do
    echo "Processing $file..."
    claude -p "Add JSDoc comments to this file:" < "$file" > "${file}.documented"
done

# Use Claude in a pipeline
$ grep -l "TODO" *.py | while read file; do
    claude -p "Fix all TODO items in this file" < "$file"
done

```

### [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#session-management)  Session management

Copy

```bash
# Start a session and capture the session ID
$ claude -p "Initialize a new project" --output-format json | jq -r '.session_id' > session.txt

# Continue with the same session
$ claude -p --resume "$(cat session.txt)" "Add unit tests"

```

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#best-practices)  Best practices

1. **Use JSON output format** for programmatic parsing of responses:





Copy









```bash
# Parse JSON response with jq
result=$(claude -p "Generate code" --output-format json)
code=$(echo "$result" | jq -r '.result')
cost=$(echo "$result" | jq -r '.cost_usd')

```

2. **Handle errors gracefully** \- check exit codes and stderr:





Copy









```bash
if ! claude -p "$prompt" 2>error.log; then
       echo "Error occurred:" >&2
       cat error.log >&2
       exit 1
fi

```

3. **Use session management** for maintaining context in multi-turn conversations

4. **Consider timeouts** for long-running operations:





Copy









```bash
timeout 300 claude -p "$complex_prompt" || echo "Timed out after 5 minutes"

```

5. **Respect rate limits** when making multiple requests by adding delays between calls


## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#real-world-applications)  Real-world applications

The Claude Code SDK enables powerful integrations with your development workflow. One notable example is the [Claude Code GitHub Actions](https://docs.anthropic.com/en/docs/claude-code/github-actions), which uses the SDK to provide automated code review, PR creation, and issue triage capabilities directly in your GitHub workflow.

## [​](https://docs.anthropic.com/en/docs/claude-code/sdk\#related-resources)  Related resources

- [CLI usage and controls](https://docs.anthropic.com/en/docs/claude-code/cli-reference) \- Complete CLI documentation
- [GitHub Actions integration](https://docs.anthropic.com/en/docs/claude-code/github-actions) \- Automate your GitHub workflow with Claude
- [Common workflows](https://docs.anthropic.com/en/docs/claude-code/common-workflows) \- Step-by-step guides for common use cases

Was this page helpful?

YesNo

[GitHub Actions](https://docs.anthropic.com/en/docs/claude-code/github-actions) [Troubleshooting](https://docs.anthropic.com/en/docs/claude-code/troubleshooting)

On this page

- [Authentication](https://docs.anthropic.com/en/docs/claude-code/sdk#authentication)
- [Anthropic API key](https://docs.anthropic.com/en/docs/claude-code/sdk#anthropic-api-key)
- [Third-Party API credentials](https://docs.anthropic.com/en/docs/claude-code/sdk#third-party-api-credentials)
- [Basic SDK usage](https://docs.anthropic.com/en/docs/claude-code/sdk#basic-sdk-usage)
- [Command line](https://docs.anthropic.com/en/docs/claude-code/sdk#command-line)
- [TypeScript](https://docs.anthropic.com/en/docs/claude-code/sdk#typescript)
- [Python](https://docs.anthropic.com/en/docs/claude-code/sdk#python)
- [Advanced usage](https://docs.anthropic.com/en/docs/claude-code/sdk#advanced-usage)
- [Multi-turn conversations](https://docs.anthropic.com/en/docs/claude-code/sdk#multi-turn-conversations)
- [Custom system prompts](https://docs.anthropic.com/en/docs/claude-code/sdk#custom-system-prompts)
- [MCP Configuration](https://docs.anthropic.com/en/docs/claude-code/sdk#mcp-configuration)
- [Custom permission prompt tool](https://docs.anthropic.com/en/docs/claude-code/sdk#custom-permission-prompt-tool)
- [Available CLI options](https://docs.anthropic.com/en/docs/claude-code/sdk#available-cli-options)
- [Output formats](https://docs.anthropic.com/en/docs/claude-code/sdk#output-formats)
- [Text output (default)](https://docs.anthropic.com/en/docs/claude-code/sdk#text-output-default)
- [JSON output](https://docs.anthropic.com/en/docs/claude-code/sdk#json-output)
- [Streaming JSON output](https://docs.anthropic.com/en/docs/claude-code/sdk#streaming-json-output)
- [Message schema](https://docs.anthropic.com/en/docs/claude-code/sdk#message-schema)
- [Input formats](https://docs.anthropic.com/en/docs/claude-code/sdk#input-formats)
- [Text input (default)](https://docs.anthropic.com/en/docs/claude-code/sdk#text-input-default)
- [Streaming JSON input](https://docs.anthropic.com/en/docs/claude-code/sdk#streaming-json-input)
- [Examples](https://docs.anthropic.com/en/docs/claude-code/sdk#examples)
- [Simple script integration](https://docs.anthropic.com/en/docs/claude-code/sdk#simple-script-integration)
- [Processing files with Claude](https://docs.anthropic.com/en/docs/claude-code/sdk#processing-files-with-claude)
- [Session management](https://docs.anthropic.com/en/docs/claude-code/sdk#session-management)
- [Best practices](https://docs.anthropic.com/en/docs/claude-code/sdk#best-practices)
- [Real-world applications](https://docs.anthropic.com/en/docs/claude-code/sdk#real-world-applications)
- [Related resources](https://docs.anthropic.com/en/docs/claude-code/sdk#related-resources)