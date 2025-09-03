# 🚀 Quick Start: Using OpenTelemetry Logging in Your CLI

## ⚡ TL;DR - 3 Step Process

1. **Import the logger**: `from codegen.shared.logging.get_logger import get_logger`
1. **Add `extra={}` to your log calls**: `logger.info("message", extra={"key": "value"})`
1. **Enable telemetry**: `codegen config telemetry enable`

**That's it!** Your logs automatically go to Grafana Cloud when telemetry is enabled.

## 🎯 Immediate Actions You Can Take

### 1. Quick Enhancement of Existing Commands

Pick **any existing CLI command** and add 2-3 lines:

```python
# Add this import at the top
from codegen.shared.logging.get_logger import get_logger

# Add this line after imports
logger = get_logger(__name__)

# Find any existing console.print() or error handling and add:
logger.info(
    "Operation completed",
    extra={
        "operation": "command_name",
        "org_id": org_id,  # if available
        "success": True,
    },
)
```

### 2. Test the Integration Right Now

```bash
# 1. Enable telemetry
codegen config telemetry enable

# 2. Run the demo
python example_enhanced_agent_command.py

# 3. Run any CLI command
codegen agents  # or any other command

# 4. Check status
codegen config telemetry status
```

## 📝 Copy-Paste Patterns

### Pattern 1: Operation Start/End

```python
logger = get_logger(__name__)

# At start of function
logger.info("Operation started", extra={"operation": "command.subcommand", "user_input": relevant_input})

# At end of function
logger.info("Operation completed", extra={"operation": "command.subcommand", "success": True})
```

### Pattern 2: Error Handling

```python
try:
    # your existing code
    pass
except SomeSpecificError as e:
    logger.error("Specific error occurred", extra={"operation": "command.subcommand", "error_type": "specific_error", "error_details": str(e)}, exc_info=True)
    # your existing error handling
```

### Pattern 3: API Calls

```python
# Before API call
logger.info("Making API request", extra={"operation": "api.request", "endpoint": "agent/run", "org_id": org_id})

# After successful API call
logger.info("API request successful", extra={"operation": "api.request", "endpoint": "agent/run", "response_id": response.get("id"), "status_code": response.status_code})
```

## 🎯 What to Log (Priority Order)

### 🔥 High Priority (Add These First)

- **Operation start/end**: When commands begin/complete
- **API calls**: Requests to your backend
- **Authentication events**: Login/logout/token issues
- **Errors**: Any exception or failure
- **User actions**: Commands run, options selected

### ⭐ Medium Priority

- **Performance**: Duration of operations
- **State changes**: Status updates, configuration changes
- **External tools**: Claude CLI detection, git operations

### 💡 Low Priority (Nice to Have)

- **Debug info**: Internal state, validation steps
- **User behavior**: Which features are used most

## 🔧 Minimal Changes to Existing Commands

### Example: Enhance agent/main.py

```python
# Just add these 3 lines to your existing create() function:

from codegen.shared.logging.get_logger import get_logger
logger = get_logger(__name__)

def create(prompt: str, org_id: int | None = None, ...):
    """Create a new agent run with the given prompt."""

    # ADD: Log start
    logger.info("Agent creation started", extra={
        "operation": "agent.create",
        "org_id": org_id,
        "prompt_length": len(prompt)
    })

    # Your existing code...
    try:
        response = requests.post(url, headers=headers, json=payload)
        agent_run_data = response.json()

        # ADD: Log success
        logger.info("Agent created successfully", extra={
            "operation": "agent.create",
            "agent_run_id": agent_run_data.get("id"),
            "status": agent_run_data.get("status")
        })

    except requests.RequestException as e:
        # ADD: Log error
        logger.error("Agent creation failed", extra={
            "operation": "agent.create",
            "error_type": "api_error",
            "error": str(e)
        })
        # Your existing error handling...
```

### Example: Enhance claude/main.py

```python
# Add to your _run_claude_interactive function:

logger = get_logger(__name__)


def _run_claude_interactive(resolved_org_id: int, no_mcp: bool | None) -> None:
    session_id = generate_session_id()

    # ADD: Log session start
    logger.info(
        "Claude session started",
        extra={
            "operation": "claude.session_start",
            "session_id": session_id[:8],  # Short version for privacy
            "org_id": resolved_org_id,
        },
    )

    # Your existing code...

    try:
        process = subprocess.Popen([claude_path, "--session-id", session_id])
        returncode = process.wait()

        # ADD: Log session end
        logger.info(
            "Claude session completed", extra={"operation": "claude.session_complete", "session_id": session_id[:8], "exit_code": returncode, "status": "COMPLETE" if returncode == 0 else "ERROR"}
        )

    except Exception as e:
        # ADD: Log session error
        logger.error("Claude session failed", extra={"operation": "claude.session_error", "session_id": session_id[:8], "error": str(e)})
```

## 🧪 Verification

After making changes:

1. **Run the command**: Execute your enhanced CLI command
1. **Check telemetry status**: `codegen config telemetry status`
1. **Look for logs in Grafana Cloud**: Search for your operation names
1. **Test with telemetry disabled**: `codegen config telemetry disable` - should still work normally

## 🚀 Progressive Enhancement

**Week 1**: Add basic operation logging to 2-3 commands
**Week 2**: Add error logging to all commands
**Week 3**: Add performance metrics and detailed context
**Week 4**: Create Grafana dashboards using the collected data

## 🎉 Benefits You'll See Immediately

- **Real usage data**: Which commands are used most?
- **Error tracking**: What breaks and how often?
- **Performance insights**: Which operations are slow?
- **User behavior**: How do users actually use your CLI?
- **Debugging**: Rich context when things go wrong

Start with just **one command** and **one log line** - you'll see the value immediately! 🎯
