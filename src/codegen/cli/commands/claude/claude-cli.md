# Claude Code CLI Integration Documentation

## Overview

The `codegen claude` command integrates Claude Code with our remote telemetry system, allowing us to monitor and analyze Claude Code usage patterns, tool executions, and API interactions. This integration uses Claude Code's built-in OpenTelemetry (OTEL) support to send telemetry data to our backend API.

## Architecture

```
Claude Code Process
        ↓ (OTLP/HTTP)
Local CLI Command (codegen claude)
        ↓ (Environment Variables)
Remote Telemetry API (/v1/organizations/{org_id}/telemetry)
        ↓ (Processing)
AgentRun & AgentRunLog Database Models
        ↓ (Display)
Frontend Agent Trace Components
```

## File Structure

- `main.py` - Main CLI command implementation
- `claude-cli.md` (this file) - Documentation
- Backend files (in `cloud/codegen-backend/`):
  - `app/modal_app/dev_api/v1/telemetry.py` - OTLP endpoint handlers
  - `app/modal_app/dev_api/v1/claude_types.py` - Pydantic models for OTLP data
  - `app/modal_app/dev_api/v1/claude_session_utils.py` - AgentRun/AgentRunLog utilities

## Command Usage

### Basic Usage

```bash
codegen claude                          # Normal mode with telemetry
codegen claude --normal-mode            # No telemetry (normal Claude Code)
```

### Debug Modes

```bash
codegen claude --debug-mode             # Show debug info
codegen claude --debug-otel             # Show ALL OTLP events (verbose)
codegen claude --debug-otel-actions-only # Show ONLY action events (clean)
codegen claude --verbose-telemetry      # Enable backend verbose logging
```

### Security & Logging Options

```bash
codegen claude --log-prompts            # Log user prompt content (security risk)
codegen claude --console-output         # Show telemetry in local console
```

### Advanced Options

```bash
codegen claude --org-id 123             # Custom organization ID
codegen claude --export-interval 30     # Custom export interval (seconds)
```

## How It Works

### 1. Environment Variable Configuration

The CLI sets up Claude Code's OpenTelemetry configuration via environment variables:

```bash
# Core telemetry
CLAUDE_CODE_ENABLE_TELEMETRY=1
OTEL_EXPORTER_OTLP_ENDPOINT=https://api.codegen.com/v1/organizations/11/telemetry
OTEL_EXPORTER_OTLP_PROTOCOL=http/json
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <token>,X-Verbose-Telemetry=true

# Export configuration
OTEL_METRICS_EXPORTER=otlp,console
OTEL_LOGS_EXPORTER=otlp,console
OTEL_METRIC_EXPORT_INTERVAL=60000    # 60 seconds in milliseconds
OTEL_LOGS_EXPORT_INTERVAL=60000

# Resource identification
OTEL_RESOURCE_ATTRIBUTES=service.name=claude-code,organization.id=11,user.id=<token>

# Feature flags
OTEL_METRICS_INCLUDE_SESSION_ID=true
OTEL_LOG_USER_PROMPTS=1              # Enable/disable prompt content logging
```

### 2. Telemetry Data Flow

Claude Code automatically sends two types of telemetry:

#### Metrics (Counters/Gauges)

- `claude_code.session.count` - Active session tracking
- `claude_code.token.usage` - Token consumption by model/type
- `claude_code.cost.usage` - Estimated API costs
- `claude_code.active_time.total` - User activity time
- `claude_code.tool_decision.count` - Tool accept/reject counts

#### Events (Logs)

- `claude_code.user_prompt` - User interactions
- `claude_code.tool_result` - Tool executions with parameters
- `claude_code.tool_decision` - Tool permission decisions
- `claude_code.api_request` - LLM API calls with tokens/cost
- `claude_code.api_error` - API failures

### 3. Backend Processing

#### OTLP Endpoints

- `POST /v1/organizations/{org_id}/telemetry/v1/metrics` - Receives metrics
- `POST /v1/organizations/{org_id}/telemetry/v1/logs` - Receives events

#### Data Transformation Pipeline

1. **Raw OTLP Parsing** (`telemetry.py`) - Handles camelCase/snake_case variations
1. **Type Validation** (`claude_types.py`) - Pydantic models for safe parsing
1. **Session Management** (`claude_session_utils.py`) - Maps sessions to AgentRuns
1. **Database Storage** - Creates AgentRun and AgentRunLog entries

#### Key Database Models

- `AgentRunModel` - Represents a Claude Code session
  - `meta.claude_code_session_id` - Links to Claude session
  - `agent_type = AgentType.CLAUDE_CODE`
  - `source_type = AgentRunSourceType.API`
- `AgentRunLogModel` - Individual events within a session
  - `type = AgentLogType.USER_MESSAGE | ACTION`
  - `tool_input` - Parsed tool parameters as JSON
  - `tool_data` - Additional metadata

## Debug Modes Explained

### `--debug-otel` (Full Debug)

Shows ALL OpenTelemetry events in console, including:

- Metrics (counters, timers, gauges)
- Events (tool usage, API calls, prompts)
- Raw OTLP JSON structures

**Use when**: Deep debugging telemetry issues

### `--debug-otel-actions-only` (Clean Mode - No Console Telemetry)

Disables console telemetry output entirely for a clean Claude Code experience:

- **No raw JSON output** cluttering the terminal
- **Telemetry still captured** and sent to backend for processing
- **Clean interactive experience** with Claude Code
- **Backend processing** of all telemetry events continues normally

**Use when**: You want to use Claude Code without telemetry noise but still capture data remotely

**Note**: This mode prioritizes user experience over real-time telemetry visibility. Use `--debug-otel` if you need to see telemetry events in real-time.

### `--verbose-telemetry` (Backend Debug)

Controls backend logging verbosity via `X-Verbose-Telemetry` header.

- `false` (default): Clean logs, essential events only
- `true`: Detailed event-by-event logging with emojis

**Use when**: Debugging backend processing issues

## Tool Parameter Extraction

One of the key features is extracting tool parameters from Claude Code events:

### Flow

1. Claude Code sends `tool_result` event with `tool_parameters` as JSON string
1. `ClaudeCodeEventAttributes.tool_parameters_json` property parses it
1. `claude_session_utils.py` stores parsed JSON in `AgentRunLog.tool_input`
1. Frontend components receive structured tool input data

### Example

Claude Code sends:

```json
{
  "tool_parameters": "{\"bash_command\":\"find\",\"full_command\":\"find . -name '*.js'\",\"description\":\"Find JS files\"}"
}
```

We store in database:

```json
{
  "bash_command": "find",
  "full_command": "find . -name '*.js'",
  "description": "Find JS files"
}
```

## Frontend Integration

The telemetry data flows to our frontend agent trace system:

### Components

- `AgentTrace/Cards/ToolRenderers/ClaudeCode/` - Tool-specific renderers
- `ClaudeCodeTodoWriteConfig.tsx` - TodoWrite tool renderer
- `ClaudeCodeLsConfig.tsx` - File listing tool renderer

### Schema Handling

Frontend components use flexible Zod schemas (`z.any()`) to handle varying tool input structures from Claude Code.

## Authentication & Security

### API Authentication

- Uses existing `codegen login` token system
- Token passed via `Authorization: Bearer <token>` header
- Organization membership verified on backend

### Prompt Logging Security

- **Default**: Prompt content redacted, only length tracked
- **`--log-prompts`**: Full prompt content logged (security risk)
- **Debug modes**: Auto-enable for troubleshooting

## Error Handling

### CLI Level

- Tests Claude Code accessibility before starting
- Graceful Ctrl+C handling
- Clear error messages for missing authentication

### Backend Level

- Handles both camelCase and snake_case OTLP formats
- Fallback parsing for malformed JSON
- Transaction rollback on database errors

### Frontend Level

- Defensive parsing with optional chaining
- Debug sections for troubleshooting malformed data
- Flexible schemas to handle unexpected structures

## Performance Considerations

### Export Intervals

- **Production**: 60 seconds (default)
- **Debug**: 5 seconds for faster feedback
- Configurable via `--export-interval`

### Logging Verbosity

- **Default**: Essential events only for clean logs
- **Verbose**: Full event details only when needed
- **Actions-only**: Filters noisy metrics in debug mode

### Database Impact

- Batched processing of events by session
- Efficient session lookup via meta field indexing
- Minimal AgentRun updates (only timestamp changes)

## Common Issues & Solutions

### "Input must be provided" Error

- **Cause**: CLI capturing stdout/stderr preventing interactive mode
- **Solution**: Fixed by not capturing output in normal mode

### Empty tool_input (`{}`) in Database

- **Cause**: tool_parameters not being parsed as JSON
- **Solution**: Added `tool_parameters_json` property and improved parsing

### Frontend Rendering Errors

- **Cause**: Rigid Zod schemas expecting specific structures
- **Solution**: Made schemas flexible with `z.any()` and defensive parsing

### CamelCase/Snake_Case Mismatches

- **Cause**: OTLP data can come in either format
- **Solution**: Added fallback parsing for both formats

## Extending the System

### Adding New Tool Renderers

1. Create new component in `ClaudeCode/tool/configs/`
1. Use flexible schema: `z.any()` or `z.union([...])`
1. Add defensive parsing with optional chaining
1. Include debug sections for troubleshooting

### Adding New Event Types

1. Update `ClaudeCodeEventAttributes` in `claude_types.py`
1. Add new `is_*` property to `ClaudeCodeEvent`
1. Handle in `log_claude_event_as_agent_run_log()`
1. Update frontend if needed

### Debugging New Issues

1. Start with `--debug-otel-actions-only` for clean action view
1. Use `--verbose-telemetry` for backend detail
1. Check raw OTLP data with `--debug-otel` if needed
1. Verify database entries in AgentRun/AgentRunLog tables

## Future Improvements

### Potential Enhancements

- Real-time telemetry dashboard
- Cost tracking and budgeting
- Tool usage analytics
- Session replay functionality
- Claude Code version-specific optimizations

### Architecture Considerations

- Separate metrics and events processing
- Real-time vs batch processing modes
- Telemetry data retention policies
- Performance monitoring for high-volume usage

## Related Documentation

- [Claude Code OpenTelemetry Docs](https://docs.anthropic.com/en/docs/claude-code/monitoring-usage)
- [OpenTelemetry Protocol Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Typer CLI Framework](https://typer.tiangolo.com/) \[[memory:5707685]\]
- [AgentRun Database Schema](../../../cloud/codegen-backend/app/db/models/agent/agent_run.py)

______________________________________________________________________

_This documentation is maintained alongside the code. Update when making significant changes to the telemetry integration._
