"""Codegen Meeting Bot - Recall.ai Proof of Concept

This script demonstrates how to use Recall.ai to create a meeting bot that can:
1. Join a Google Meet or Zoom meeting
2. Record the meeting
3. Generate a transcript
4. Process the transcript with Codegen

Requirements:
- Recall.ai API key
- Python 3.8+
- Required packages: requests, asyncio, websockets

Note: This is a proof-of-concept and not production-ready code.
"""

import asyncio
import json
import os
import time
from typing import Any, Optional

import requests

# Configuration
RECALL_API_KEY = os.environ.get("RECALL_API_KEY", "your_api_key_here")
RECALL_API_BASE_URL = "https://api.recall.ai/api/v1"


class CodegenMeetingBot:
    """A meeting bot that uses Recall.ai to join meetings and process transcripts with Codegen."""

    def __init__(self, api_key: str):
        """Initialize the meeting bot with the Recall.ai API key."""
        self.api_key = api_key
        self.headers = {"Authorization": f"Token {self.api_key}", "Content-Type": "application/json"}

    def create_bot(self, platform: str, meeting_url: str, bot_name: str = "Codegen Assistant", join_at: Optional[str] = None) -> dict[str, Any]:
        """Create a bot to join a meeting.

        Args:
            platform: The meeting platform ("zoom", "google_meet", "ms_teams", etc.)
            meeting_url: The URL of the meeting to join
            bot_name: The display name for the bot
            join_at: ISO 8601 timestamp for when the bot should join (None for immediate)

        Returns:
            The bot data from the Recall.ai API
        """
        endpoint = f"{RECALL_API_BASE_URL}/bot/"

        payload = {"meeting_url": meeting_url, "platform": platform, "bot_name": bot_name}

        if join_at:
            payload["join_at"] = join_at

        response = requests.post(endpoint, headers=self.headers, json=payload)
        response.raise_for_status()

        return response.json()

    def get_bot(self, bot_id: str) -> dict[str, Any]:
        """Get information about a bot.

        Args:
            bot_id: The ID of the bot

        Returns:
            The bot data from the Recall.ai API
        """
        endpoint = f"{RECALL_API_BASE_URL}/bot/{bot_id}/"

        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def list_bots(self, limit: int = 10) -> list[dict[str, Any]]:
        """List all bots.

        Args:
            limit: Maximum number of bots to return

        Returns:
            List of bot data from the Recall.ai API
        """
        endpoint = f"{RECALL_API_BASE_URL}/bot/?limit={limit}"

        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()

        return response.json().get("results", [])

    async def stream_transcription(self, bot_id: str):
        """Stream real-time transcription from a bot.

        Args:
            bot_id: The ID of the bot
        """
        import websockets

        # Get the bot data to check if it's active
        bot = self.get_bot(bot_id)

        if bot.get("status") != "joined":
            print(f"Bot is not active in the meeting. Current status: {bot.get('status')}")
            return

        # Connect to the transcription websocket
        ws_url = f"wss://api.recall.ai/ws/bot/{bot_id}/transcription/"

        async with websockets.connect(ws_url, extra_headers={"Authorization": f"Token {self.api_key}"}) as websocket:
            print("Connected to transcription stream. Waiting for transcription...")

            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)

                    if data.get("event") == "transcript_part":
                        speaker = data.get("speaker", "Unknown")
                        text = data.get("text", "")
                        print(f"{speaker}: {text}")

                        # Here you would process the transcript with Codegen
                        # For example, detect if someone is asking a question about Codegen
                        if "codegen" in text.lower() and "?" in text:
                            print("Detected question about Codegen!")
                            # In a real implementation, you would:
                            # 1. Process the question with Codegen
                            # 2. Generate a response
                            # 3. Send the response back to the meeting (via chat or audio)

                except Exception as e:
                    print(f"Error in transcription stream: {e}")
                    break

    def process_meeting_recording(self, bot_id: str) -> dict[str, Any]:
        """Process a completed meeting recording.

        Args:
            bot_id: The ID of the bot

        Returns:
            Processed meeting data
        """
        # Get the bot data
        bot = self.get_bot(bot_id)

        if bot.get("status") not in ["left", "ended"]:
            print(f"Meeting is not completed yet. Current status: {bot.get('status')}")
            return {}

        # Get the recording URL
        recording_url = bot.get("video_url")

        if not recording_url:
            print("No recording available for this meeting.")
            return {}

        print(f"Recording available at: {recording_url}")

        # In a real implementation, you would:
        # 1. Download the recording
        # 2. Process the full transcript
        # 3. Generate a meeting summary with Codegen
        # 4. Extract action items
        # 5. Store the results

        return {
            "meeting_id": bot.get("id"),
            "duration": bot.get("duration"),
            "recording_url": recording_url,
            "platform": bot.get("platform"),
            "summary": "This is where the meeting summary would go.",
            "action_items": ["Action item 1", "Action item 2"],
        }


async def main():
    """Main function to demonstrate the Codegen Meeting Bot."""
    # Initialize the bot
    bot = CodegenMeetingBot(RECALL_API_KEY)

    # Example: Create a bot to join a Google Meet meeting
    meeting_url = "https://meet.google.com/abc-defg-hij"

    try:
        # Create a bot to join the meeting
        print(f"Creating bot to join meeting: {meeting_url}")
        bot_data = bot.create_bot(platform="google_meet", meeting_url=meeting_url, bot_name="Codegen Assistant")

        bot_id = bot_data.get("id")
        print(f"Bot created with ID: {bot_id}")
        print(f"Bot status: {bot_data.get('status')}")

        # Wait for the bot to join the meeting
        print("Waiting for bot to join the meeting...")
        for _ in range(30):  # Wait up to 30 seconds
            bot_data = bot.get_bot(bot_id)
            if bot_data.get("status") == "joined":
                print("Bot has joined the meeting!")
                break
            time.sleep(1)

        # Stream transcription in real-time
        print("Starting transcription stream...")
        await bot.stream_transcription(bot_id)

        # In a real implementation, you would wait for the meeting to end
        # For this example, we'll just wait a few seconds
        print("Simulating meeting duration (10 seconds)...")
        time.sleep(10)

        # Process the meeting recording
        print("Processing meeting recording...")
        meeting_data = bot.process_meeting_recording(bot_id)
        print(f"Meeting data: {json.dumps(meeting_data, indent=2)}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
