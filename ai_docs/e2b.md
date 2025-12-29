# E2B - Secure Cloud Sandboxes for AI-Generated Code

E2B is an open-source runtime for executing AI-generated code in secure cloud sandboxes. Perfect for agentic AI use cases, data analysis, code interpretation, and more.

## What is E2B?

E2B provides secure, isolated cloud sandboxes that can run AI-generated code safely. Each sandbox is a small VM that starts quickly (~150ms) and can be used for various AI applications like data analysis, visualization, coding agents, and full AI-generated apps.

### Key Features

- **Fast startup**: Sandboxes start in under 200ms (no cold starts)
- **Secure**: Powered by Firecracker microVMs for untrusted code execution
- **LLM-agnostic**: Works with OpenAI, Anthropic, Mistral, Llama, and custom models
- **Multiple languages**: Python, JavaScript, Ruby, C++, and more
- **Persistent sessions**: Up to 24-hour sandbox sessions
- **Internet access**: Full internet connectivity with public URLs
- **Package installation**: Install custom packages via pip, npm, apt-get
- **File operations**: Upload, download, and manipulate files

## Quick Start (Python)

### 1. Installation

```bash
pip install e2b-code-interpreter
```

### 2. Set Environment Variable

```bash
export E2B_API_KEY="your_api_key_here"
```

Get your API key from the [E2B Dashboard](https://www.e2b.dev/dashboard?tab=keys).

### 3. Basic Usage

```python
from e2b_code_interpreter import Sandbox

# Create a sandbox
with Sandbox() as sandbox:
    # Run Python code
    execution = sandbox.run_code("print('Hello, E2B!')")
    print(execution.text)  # Output: Hello, E2B!
    
    # List files in sandbox
    files = sandbox.files.list('/')
    print(files)
```

### 4. Advanced Example with Data Analysis

```python
from e2b_code_interpreter import Sandbox
import pandas as pd

with Sandbox() as sandbox:
    # Upload a CSV file
    csv_data = "name,age,city\nJohn,25,NYC\nJane,30,LA"
    sandbox.files.write('/tmp/data.csv', csv_data)
    
    # Analyze data with pandas
    code = """
import pandas as pd
import matplotlib.pyplot as plt

# Load and analyze data
df = pd.read_csv('/tmp/data.csv')
print("Data shape:", df.shape)
print("\\nData preview:")
print(df.head())

# Create a simple plot
plt.figure(figsize=(8, 6))
plt.bar(df['name'], df['age'])
plt.title('Age by Name')
plt.xlabel('Name')
plt.ylabel('Age')
plt.savefig('/tmp/plot.png')
print("\\nPlot saved to /tmp/plot.png")
"""
    
    execution = sandbox.run_code(code)
    print(execution.text)
    
    # Download the generated plot
    plot_data = sandbox.files.read('/tmp/plot.png')
    with open('plot.png', 'wb') as f:
        f.write(plot_data)
```

## Quick Start (JavaScript/TypeScript)

### 1. Installation

```bash
npm install @e2b/code-interpreter dotenv
```

### 2. Environment Setup

Create a `.env` file:
```
E2B_API_KEY=your_api_key_here
```

### 3. Basic Usage

```typescript
import 'dotenv/config'
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create()

// Execute Python code
const execution = await sandbox.runCode('print("Hello from E2B!")')
console.log(execution.logs)

// List files
const files = await sandbox.files.list('/')
console.log(files)

await sandbox.kill()
```

### 4. LLM Integration Example

```typescript
import { openai } from '@ai-sdk/openai'
import { generateText } from 'ai'
import { Sandbox } from '@e2b/code-interpreter'
import z from 'zod'

const model = openai('gpt-4o')

const { text } = await generateText({
  model,
  prompt: "Calculate how many r's are in the word 'strawberry'",
  tools: {
    codeInterpreter: {
      description: 'Execute python code and return result',
      parameters: z.object({
        code: z.string().describe('Python code to execute'),
      }),
      execute: async ({ code }) => {
        const sandbox = await Sandbox.create()
        const { text, results } = await sandbox.runCode(code)
        await sandbox.kill()
        return results
      },
    },
  },
  maxSteps: 2
})

console.log(text)
```

## Sandbox Management

### Create Sandbox with Custom Timeout

```python
# Python
with Sandbox(timeout=300) as sandbox:  # 5 minutes
    # Your code here
    pass

# Or extend timeout during runtime
sandbox.set_timeout(600)  # 10 minutes
```

```typescript
// TypeScript
const sandbox = await Sandbox.create({
  timeoutMs: 300_000  // 5 minutes
})

// Extend timeout during runtime
await sandbox.setTimeout(600_000)  // 10 minutes
```

### Sandbox Information

```python
# Get sandbox details
info = sandbox.get_info()
print(f"Sandbox ID: {info['sandboxId']}")
print(f"Started at: {info['startedAt']}")
print(f"Ends at: {info['endAt']}")
```

### Sandbox Persistence (Beta)

Pause and resume sandboxes to maintain state across sessions:

```python
# Pause sandbox (saves filesystem + memory state)
sandbox_id = sandbox.pause()
print(f"Sandbox paused: {sandbox_id}")

# Resume later from exact same state
resumed_sandbox = Sandbox.resume(sandbox_id)
```

## Package Installation

### Runtime Installation

```python
with Sandbox() as sandbox:
    # Install Python packages
    sandbox.commands.run('pip install requests beautifulsoup4')
    
    # Install system packages
    sandbox.commands.run('apt-get update && apt-get install -y curl git')
    
    # Install Node.js packages
    sandbox.commands.run('npm install axios')
    
    # Now use the packages
    sandbox.run_code("""
import requests
response = requests.get('https://api.github.com/users/e2b-dev')
print(response.json()['name'])
""")
```

### Custom Sandbox Templates

For pre-installed packages, create a custom template:

1. **Install E2B CLI**:
```bash
npm install -g @e2b/cli
# or
brew install e2b
```

2. **Login and Initialize**:
```bash
e2b auth login
e2b template init
```

3. **Edit `e2b.Dockerfile`**:
```dockerfile
FROM e2bdev/code-interpreter:latest

RUN pip install pandas numpy matplotlib seaborn
RUN npm install axios express
RUN apt-get update && apt-get install -y curl git vim
```

4. **Build Template**:
```bash
e2b template build -c "/root/.jupyter/start-up.sh"
```

5. **Use Custom Template**:
```python
sandbox = Sandbox(template='your_template_id')
```

## File Operations

### Upload/Download Files

```python
with Sandbox() as sandbox:
    # Write text file
    sandbox.files.write('/tmp/hello.txt', 'Hello, World!')
    
    # Write binary file
    with open('local_image.png', 'rb') as f:
        image_data = f.read()
    sandbox.files.write('/tmp/image.png', image_data)
    
    # Read file
    content = sandbox.files.read('/tmp/hello.txt', text=True)
    print(content)
    
    # List directory
    files = sandbox.files.list('/tmp')
    for file in files:
        print(f"{file.name}: {file.type}")
    
    # Download file
    result_data = sandbox.files.read('/tmp/result.csv')
    with open('local_result.csv', 'wb') as f:
        f.write(result_data)
```

## Internet Access & Servers

Sandboxes have full internet access and can host services:

```python
with Sandbox() as sandbox:
    # Start a web server
    process = sandbox.commands.run('python -m http.server 8000', background=True)
    
    # Get public URL
    host = sandbox.get_host(8000)
    url = f"https://{host}"
    print(f"Server running at: {url}")
    
    # Make requests from outside
    import requests
    response = requests.get(url)
    print(response.text)
    
    # Clean up
    process.kill()
```

## LLM Provider Examples

### OpenAI Integration

```python
from openai import OpenAI
from e2b_code_interpreter import Sandbox

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant that writes Python code. Only respond with code, no explanations."},
        {"role": "user", "content": "Create a bar chart showing sales data: Q1=100, Q2=150, Q3=200, Q4=175"}
    ]
)

code = response.choices[0].message.content

with Sandbox() as sandbox:
    execution = sandbox.run_code(code)
    print(execution.text)
```

### Anthropic Integration

```python
from anthropic import Anthropic
from e2b_code_interpreter import Sandbox

anthropic = Anthropic()

response = anthropic.messages.create(
    model="claude-3-5-sonnet-20240620",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Write Python code to analyze this CSV data and create visualizations"}
    ]
)

code = response.content[0].text

with Sandbox() as sandbox:
    execution = sandbox.run_code(code)
    print(execution.text)
```

## Common Use Cases

### 1. AI Data Analysis

```python
with Sandbox() as sandbox:
    # Upload dataset
    sandbox.files.write('/tmp/sales.csv', sales_data)
    
    # Generate analysis code with LLM
    analysis_code = """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('/tmp/sales.csv')
print("Dataset Summary:")
print(df.describe())

# Create visualizations
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
df.hist(bins=20, ax=axes)
plt.tight_layout()
plt.savefig('/tmp/analysis.png')
"""
    
    execution = sandbox.run_code(analysis_code)
    
    # Download results
    chart = sandbox.files.read('/tmp/analysis.png')
    with open('analysis.png', 'wb') as f:
        f.write(chart)
```

### 2. Code Generation & Testing

```python
with Sandbox() as sandbox:
    # Generate function with LLM
    generated_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Test the function
for i in range(10):
    print(f"fib({i}) = {fibonacci(i)}")
"""
    
    execution = sandbox.run_code(generated_code)
    print("Code execution result:", execution.text)
```

### 3. Web Scraping & Analysis

```python
with Sandbox() as sandbox:
    # Install required packages
    sandbox.commands.run('pip install requests beautifulsoup4')
    
    scraping_code = """
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Scrape data
url = 'https://quotes.toscrape.com'
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

quotes = []
for quote in soup.find_all('div', class_='quote'):
    text = quote.find('span', class_='text').text
    author = quote.find('small', class_='author').text
    quotes.append({'text': text, 'author': author})

df = pd.DataFrame(quotes)
print(f"Scraped {len(df)} quotes")
print(df.head())

# Save results
df.to_csv('/tmp/quotes.csv', index=False)
"""
    
    execution = sandbox.run_code(scraping_code)
    
    # Download scraped data
    quotes_data = sandbox.files.read('/tmp/quotes.csv', text=True)
    print("Scraped data:", quotes_data[:200])
```

## CLI Commands

### List Running Sandboxes

```bash
# List all sandboxes
e2b sandbox list

# Filter by state
e2b sandbox list --state running,paused

# Filter by metadata
e2b sandbox list --metadata project=demo,env=dev

# Limit results
e2b sandbox list --limit 10
```

### Template Management

```bash
# List templates
e2b template list

# Build new template
e2b template build

# Delete template
e2b template delete <template_id>
```

## Best Practices

### 1. Resource Management

```python
# Always use context managers
with Sandbox() as sandbox:
    # Your code here
    pass  # Sandbox automatically cleaned up

# Or explicitly kill
sandbox = Sandbox.create()
try:
    # Your code here
    pass
finally:
    sandbox.kill()
```

### 2. Error Handling

```python
with Sandbox() as sandbox:
    execution = sandbox.run_code("print(1/0)")  # This will error
    
    if execution.error:
        print(f"Error occurred: {execution.error}")
        print(f"Error type: {execution.error.name}")
        print(f"Error message: {execution.error.value}")
    else:
        print(f"Success: {execution.text}")
```

### 3. Long-Running Processes

```python
with Sandbox() as sandbox:
    # For background processes
    process = sandbox.commands.run('python long_script.py', background=True)
    
    # Check if still running
    if process.is_alive():
        print("Process still running...")
    
    # Kill if needed
    process.kill()
```

### 4. File Management

```python
with Sandbox() as sandbox:
    # Create directories
    sandbox.commands.run('mkdir -p /tmp/project/data')
    
    # Set permissions
    sandbox.commands.run('chmod +x /tmp/script.sh')
    
    # Basic environment variables (see detailed section below)
    result = sandbox.commands.run('export MY_VAR=value && echo $MY_VAR')
    print(result.stdout)
```

## Environment Variables

E2B sandboxes provide flexible environment variable management for secure configuration and runtime customization.

### Default Environment Variables

#### Detecting Sandbox Environment
Every E2B sandbox automatically sets `E2B_SANDBOX=true`, allowing code to detect when running in a sandbox:

```python
import os

if os.environ.get('E2B_SANDBOX'):
    print("Running inside E2B sandbox!")
else:
    print("Running locally")
```

```javascript
const sandbox = await Sandbox.create()
const result = await sandbox.commands.run('echo $E2B_SANDBOX')
console.log(result.stdout) // Output: true
```

### Setting Environment Variables

E2B supports three ways to set environment variables with different scopes and priorities:

#### 1. Global Environment Variables (Sandbox Creation)
Set environment variables that persist for the entire sandbox session:

```python
# Python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox(envs={
    'DATABASE_URL': 'postgresql://localhost:5432/mydb',
    'API_KEY': 'secret-key-123',
    'DEBUG': 'true'
})

# All code execution will have access to these variables
sandbox.run_code('import os; print(os.environ["DATABASE_URL"])')
```

```javascript
// JavaScript/TypeScript
import { Sandbox } from '@e2b/code-interpreter'

const sandbox = await Sandbox.create({
  envs: {
    'DATABASE_URL': 'postgresql://localhost:5432/mydb',
    'API_KEY': 'secret-key-123',
    'DEBUG': 'true'
  }
})

// All commands will have access to these variables
await sandbox.commands.run('echo $DATABASE_URL')
```

#### 2. Code Execution Environment Variables
Set environment variables for specific code execution (overrides global variables):

```python
# Python
with Sandbox() as sandbox:
    # This execution gets specific environment variables
    result = sandbox.run_code(
        'import os; print(f"API Key: {os.environ.get(\"API_KEY\")}")',
        envs={
            'API_KEY': 'temporary-key-456',
            'ENVIRONMENT': 'testing'
        }
    )
    print(result.text)
```

```javascript
// JavaScript/TypeScript
const sandbox = await Sandbox.create()

const result = await sandbox.runCode(
  'import os; print(os.environ.get("API_KEY"))',
  {
    envs: {
      'API_KEY': 'temporary-key-456',
      'ENVIRONMENT': 'testing'
    }
  }
)
```

#### 3. Command Execution Environment Variables
Set environment variables for specific command execution:

```python
# Python
with Sandbox() as sandbox:
    # Run command with specific environment
    result = sandbox.commands.run(
        'echo "Database: $DATABASE_URL, Environment: $ENV"',
        envs={
            'DATABASE_URL': 'sqlite:///temp.db',
            'ENV': 'development'
        }
    )
    print(result.stdout)
```

```javascript
// JavaScript/TypeScript
const sandbox = await Sandbox.create()

await sandbox.commands.run('echo $MY_VAR', {
  envs: {
    'MY_VAR': 'command-specific-value'
  }
})
```

### Environment Variable Priority

Variables are resolved in this order (highest to lowest priority):
1. **Command/Code execution variables** (highest priority)
2. **Global sandbox variables** 
3. **Default sandbox variables** (like `E2B_SANDBOX`)

### Common Use Cases

#### Secure API Key Management
```python
# Pass secrets safely to sandbox code
with Sandbox(envs={'OPENAI_API_KEY': os.environ['OPENAI_API_KEY']}) as sandbox:
    code = """
import os
import openai

client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
"""
    sandbox.run_code(code)
```

#### Configuration Management
```python
# Different configurations for different environments
config_envs = {
    'production': {
        'DATABASE_URL': 'postgresql://prod-db:5432/app',
        'LOG_LEVEL': 'WARNING',
        'CACHE_TTL': '3600'
    },
    'development': {
        'DATABASE_URL': 'sqlite:///dev.db',
        'LOG_LEVEL': 'DEBUG',
        'CACHE_TTL': '60'
    }
}

env = 'development'
with Sandbox(envs=config_envs[env]) as sandbox:
    sandbox.run_code('import os; print(f"Using {os.environ[\"DATABASE_URL\"]}")')
```

#### Dynamic Environment Setup
```python
# Set environment based on runtime conditions
def create_sandbox_with_env(user_id, permissions):
    envs = {
        'USER_ID': str(user_id),
        'USER_PERMISSIONS': ','.join(permissions),
        'SESSION_ID': generate_session_id(),
        'SANDBOX_MODE': 'user_session'
    }
    
    return Sandbox(envs=envs)

# Usage
sandbox = create_sandbox_with_env(123, ['read', 'write'])
sandbox.run_code('import os; print(f"User {os.environ[\"USER_ID\"]} permissions: {os.environ[\"USER_PERMISSIONS\"]}")')
```

### Best Practices

#### Security
- Never log or print sensitive environment variables
- Use sandbox-scoped variables for secrets rather than global system env vars
- Clean up sensitive variables after use

#### Performance
- Set common variables globally to avoid repetitive passing
- Use command-specific variables for one-off customizations
- Consider variable resolution overhead for high-frequency operations

#### Debugging
```python
# Debug environment variables in sandbox
with Sandbox() as sandbox:
    # Check what environment variables are available
    result = sandbox.commands.run('env | sort')
    print("Available environment variables:")
    print(result.stdout)
    
    # Check specific variable
    check = sandbox.commands.run('echo "E2B_SANDBOX is set to: $E2B_SANDBOX"')
    print(check.stdout)
```

## Pricing & Limits

- **Free tier**: $100 in credits for new accounts
- **Pro tier**: Available for startups and research programs
- **Enterprise**: Custom pricing for large-scale deployments
- **Timeout**: Default 5 minutes, up to 24 hours (Pro)
- **Persistence**: Free during beta period

## Troubleshooting

### Common Issues

1. **Timeout errors**: Increase sandbox timeout or optimize code
2. **Package not found**: Install packages at runtime or use custom templates
3. **Memory issues**: Monitor resource usage and optimize algorithms
4. **Network connectivity**: Ensure sandbox has internet access for external APIs

### Debug Tips

```python
with Sandbox() as sandbox:
    # Check system info
    info = sandbox.commands.run('uname -a && python --version && node --version')
    print(info.stdout)
    
    # Monitor resources
    resources = sandbox.commands.run('free -h && df -h')
    print(resources.stdout)
    
    # Check network
    network = sandbox.commands.run('curl -I https://google.com')
    print(network.stdout)
```

## Resources

- **Documentation**: https://www.e2b.dev/docs
- **GitHub**: https://github.com/e2b-dev
- **Discord Community**: https://discord.com/invite/U7KEcGErtQ
- **Dashboard**: https://www.e2b.dev/dashboard
- **Cookbook Examples**: https://github.com/e2b-dev/e2b-cookbook

E2B makes it easy to run AI-generated code safely and efficiently. Start building your AI applications with secure, scalable sandbox execution today!