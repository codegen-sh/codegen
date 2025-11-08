# Codegen Meeting Bot Examples

This directory contains proof-of-concept examples for implementing a Codegen bot that can join Google Meet and Zoom meetings.

## Overview

The Codegen Meeting Bot is designed to:

1. Join video meetings on platforms like Google Meet and Zoom
1. Record and transcribe meetings
1. Answer questions about Codegen during meetings
1. Generate meeting summaries and action items

## Implementation Options

### 1. Recall.ai Integration (recall_ai_poc.py)

This example demonstrates how to use the [Recall.ai](https://www.recall.ai/) API to create a meeting bot that works across multiple platforms.

**Features:**

- Platform-agnostic implementation (works with Google Meet, Zoom, MS Teams, etc.)
- Real-time transcription streaming
- Meeting recording and processing
- Customizable bot name and appearance

**Requirements:**

- Python 3.8+
- Recall.ai API key
- Required packages: `requests`, `asyncio`, `websockets`

**Usage:**

```python
# Set your Recall.ai API key
export RECALL_API_KEY="your_api_key_here"

# Run the example
python recall_ai_poc.py
```

### 2. Zoom SDK Integration (zoom_sdk_poc.js)

This example demonstrates how to use the Zoom Meeting SDK to create a bot specifically for Zoom meetings.

**Features:**

- Join Zoom meetings programmatically
- Listen to meeting events (chat messages, participant changes, etc.)
- Respond to questions in the chat
- Customizable bot behavior

**Requirements:**

- Node.js
- Zoom Meeting SDK credentials
- Required packages: `puppeteer`, `express`, `body-parser`, `crypto`, `cors`

**Usage:**

```javascript
// Set your Zoom SDK credentials
export ZOOM_SDK_KEY="your_sdk_key_here"
export ZOOM_SDK_SECRET="your_sdk_secret_here"

// Install dependencies
npm install puppeteer express body-parser crypto cors

// Run the example
node zoom_sdk_poc.js
```

## Integration with Codegen

To fully integrate these examples with Codegen, you would need to:

1. Connect to the Codegen API to process questions and generate responses
1. Implement a calendar integration to automatically schedule bots for meetings
1. Create a user interface for managing bot settings and viewing meeting summaries
1. Set up secure storage for meeting recordings and transcripts

## Next Steps

These examples are proof-of-concept implementations and not production-ready. For a production implementation, consider:

1. Error handling and retry logic
1. Authentication and security
1. Scalability for multiple concurrent meetings
1. Proper logging and monitoring
1. User management and permissions

## Resources

- [Recall.ai Documentation](https://docs.recall.ai/docs/getting-started)
- [Zoom Meeting SDK Documentation](https://marketplace.zoom.us/docs/sdk/native-sdks/web/)
- [Google Meet Bot Examples](https://github.com/Ritika-Das/Google-Meet-Bot)
