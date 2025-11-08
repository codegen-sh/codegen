/**
 * Codegen Meeting Bot - Zoom SDK Proof of Concept
 *
 * This script demonstrates how to use the Zoom Meeting SDK to create a meeting bot that can:
 * 1. Join a Zoom meeting
 * 2. Listen to meeting events
 * 3. Interact with the meeting
 *
 * Requirements:
 * - Node.js
 * - Zoom Meeting SDK credentials
 * - Puppeteer for headless browser automation
 *
 * Note: This is a proof-of-concept and not production-ready code.
 */

const puppeteer = require("puppeteer");
const express = require("express");
const bodyParser = require("body-parser");
const crypto = require("crypto");
const cors = require("cors");
const path = require("path");
const fs = require("fs");

// Configuration
const PORT = process.env.PORT || 3000;
const ZOOM_SDK_KEY = process.env.ZOOM_SDK_KEY || "your_sdk_key_here";
const ZOOM_SDK_SECRET = process.env.ZOOM_SDK_SECRET || "your_sdk_secret_here";

// Express app setup
const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(express.static("public"));

// Generate a Zoom Meeting SDK JWT token
function generateZoomToken(sdkKey, sdkSecret, meetingNumber, role) {
	const iat = Math.round(new Date().getTime() / 1000) - 30;
	const exp = iat + 60 * 60 * 2; // Token expires in 2 hours
	const oHeader = { alg: "HS256", typ: "JWT" };

	const oPayload = {
		sdkKey: sdkKey,
		mn: meetingNumber,
		role: role,
		iat: iat,
		exp: exp,
		tokenExp: exp,
	};

	const sHeader = JSON.stringify(oHeader);
	const sPayload = JSON.stringify(oPayload);
	const signature = crypto
		.createHmac("sha256", sdkSecret)
		.update(Buffer.from(sHeader + "." + sPayload).toString("base64"))
		.digest("base64");

	return (
		Buffer.from(sHeader).toString("base64") +
		"." +
		Buffer.from(sPayload).toString("base64") +
		"." +
		signature
	);
}

// API endpoint to generate a token
app.post("/api/token", (req, res) => {
	const { meetingNumber, role } = req.body;

	if (!meetingNumber) {
		return res.status(400).json({ error: "Meeting number is required" });
	}

	const token = generateZoomToken(
		ZOOM_SDK_KEY,
		ZOOM_SDK_SECRET,
		meetingNumber,
		role || 0,
	);
	res.json({ token });
});

// HTML template for the Zoom client
const zoomClientHtml = `
<!DOCTYPE html>
<html>
<head>
  <title>Codegen Zoom Bot</title>
  <meta charset="utf-8" />
  <link type="text/css" rel="stylesheet" href="https://source.zoom.us/2.13.0/css/bootstrap.css" />
  <link type="text/css" rel="stylesheet" href="https://source.zoom.us/2.13.0/css/react-select.css" />
  <meta name="format-detection" content="telephone=no">
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
  <style>
    body {
      padding-top: 50px;
    }
    #zmmtg-root {
      display: block;
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 1000;
    }
  </style>
</head>
<body>
  <div id="zmmtg-root"></div>
  <script src="https://source.zoom.us/2.13.0/lib/vendor/react.min.js"></script>
  <script src="https://source.zoom.us/2.13.0/lib/vendor/react-dom.min.js"></script>
  <script src="https://source.zoom.us/2.13.0/lib/vendor/redux.min.js"></script>
  <script src="https://source.zoom.us/2.13.0/lib/vendor/redux-thunk.min.js"></script>
  <script src="https://source.zoom.us/2.13.0/lib/vendor/lodash.min.js"></script>
  <script src="https://source.zoom.us/2.13.0/zoom-meeting-2.13.0.min.js"></script>
  <script>
    // Zoom Meeting SDK initialization
    const client = ZoomMtgEmbedded.createClient();

    // Setup Zoom client
    client.init({
      debug: true,
      zoomAppRoot: document.getElementById('zmmtg-root'),
      language: 'en-US',
      customize: {
        meetingInfo: ['topic', 'host', 'mn', 'pwd', 'telPwd', 'invite', 'participant', 'dc', 'enctype'],
        toolbar: {
          buttons: [
            {
              text: 'Custom Button',
              className: 'CustomButton',
              onClick: () => {
                console.log('Custom button clicked');
                // Send a message to the parent process
                window.parent.postMessage({ type: 'CUSTOM_BUTTON_CLICKED' }, '*');
              }
            }
          ]
        }
      }
    });

    // Join the meeting
    function joinMeeting(meetingNumber, token, userName, password) {
      client.join({
        sdkKey: '${ZOOM_SDK_KEY}',
        signature: token,
        meetingNumber: meetingNumber,
        password: password,
        userName: userName,
        success: (success) => {
          console.log('Join meeting success:', success);
          window.parent.postMessage({ type: 'JOIN_SUCCESS', data: success }, '*');
        },
        error: (error) => {
          console.log('Join meeting error:', error);
          window.parent.postMessage({ type: 'JOIN_ERROR', data: error }, '*');
        }
      });
    }

    // Listen for messages from the parent process
    window.addEventListener('message', (event) => {
      const { type, data } = event.data;

      if (type === 'JOIN_MEETING') {
        const { meetingNumber, token, userName, password } = data;
        joinMeeting(meetingNumber, token, userName, password);
      } else if (type === 'LEAVE_MEETING') {
        client.leave();
      }
    });

    // Listen for Zoom events
    client.on('connection-change', (payload) => {
      window.parent.postMessage({ type: 'CONNECTION_CHANGE', data: payload }, '*');
    });

    client.on('current-audio-change', (payload) => {
      window.parent.postMessage({ type: 'AUDIO_CHANGE', data: payload }, '*');
    });

    client.on('chat-received', (payload) => {
      window.parent.postMessage({ type: 'CHAT_RECEIVED', data: payload }, '*');
    });

    // Notify parent that the client is ready
    window.parent.postMessage({ type: 'CLIENT_READY' }, '*');
  </script>
</body>
</html>
`;

// Serve the Zoom client HTML
app.get("/zoom-client", (req, res) => {
	res.send(zoomClientHtml);
});

// Start the server
app.listen(PORT, () => {
	console.log(`Server running on port ${PORT}`);
});

/**
 * CodegenZoomBot class for controlling a Zoom meeting bot
 */
class CodegenZoomBot {
	constructor() {
		this.browser = null;
		this.page = null;
		this.serverUrl = `http://localhost:${PORT}`;
		this.isConnected = false;
		this.meetingData = {
			meetingNumber: "",
			password: "",
			userName: "Codegen Assistant",
		};
	}

	/**
	 * Initialize the bot
	 */
	async initialize() {
		// Launch a headless browser
		this.browser = await puppeteer.launch({
			headless: true,
			args: [
				"--no-sandbox",
				"--disable-setuid-sandbox",
				"--disable-web-security",
				"--allow-running-insecure-content",
				"--use-fake-ui-for-media-stream",
				"--use-fake-device-for-media-stream",
			],
		});

		// Create a new page
		this.page = await this.browser.newPage();

		// Set up event listeners for messages from the Zoom client
		await this.page.exposeFunction("onClientMessage", (message) => {
			const { type, data } = message;

			switch (type) {
				case "CLIENT_READY":
					console.log("Zoom client is ready");
					break;
				case "JOIN_SUCCESS":
					console.log("Successfully joined the meeting");
					this.isConnected = true;
					break;
				case "JOIN_ERROR":
					console.error("Failed to join the meeting:", data);
					break;
				case "CONNECTION_CHANGE":
					console.log("Connection changed:", data);
					break;
				case "AUDIO_CHANGE":
					console.log("Audio changed:", data);
					break;
				case "CHAT_RECEIVED":
					console.log("Chat received:", data);
					this.processChat(data);
					break;
				default:
					console.log("Unknown message type:", type);
			}
		});

		// Set up message listener
		await this.page.evaluateOnNewDocument(() => {
			window.addEventListener("message", (event) => {
				window.onClientMessage(event.data);
			});
		});

		// Navigate to the Zoom client page
		await this.page.goto(`${this.serverUrl}/zoom-client`);

		console.log("Bot initialized");
	}

	/**
	 * Join a Zoom meeting
	 * @param {string} meetingNumber - The Zoom meeting number
	 * @param {string} password - The Zoom meeting password
	 */
	async joinMeeting(meetingNumber, password) {
		this.meetingData.meetingNumber = meetingNumber;
		this.meetingData.password = password;

		// Get a token for the meeting
		const response = await fetch(`${this.serverUrl}/api/token`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				meetingNumber,
				role: 0, // 0 for attendee, 1 for host
			}),
		});

		const { token } = await response.json();

		// Send a message to the Zoom client to join the meeting
		await this.page.evaluate(
			(data) => {
				window.postMessage(
					{
						type: "JOIN_MEETING",
						data: {
							meetingNumber: data.meetingNumber,
							token: data.token,
							userName: data.userName,
							password: data.password,
						},
					},
					"*",
				);
			},
			{
				meetingNumber,
				token,
				userName: this.meetingData.userName,
				password,
			},
		);

		console.log(`Joining meeting: ${meetingNumber}`);
	}

	/**
	 * Leave the current Zoom meeting
	 */
	async leaveMeeting() {
		if (!this.isConnected) {
			console.log("Not connected to a meeting");
			return;
		}

		// Send a message to the Zoom client to leave the meeting
		await this.page.evaluate(() => {
			window.postMessage(
				{
					type: "LEAVE_MEETING",
				},
				"*",
			);
		});

		this.isConnected = false;
		console.log("Left the meeting");
	}

	/**
	 * Process a chat message from the meeting
	 * @param {Object} chatData - The chat message data
	 */
	async processChat(chatData) {
		const { message, sender } = chatData;

		// Check if the message is directed to Codegen
		if (message.toLowerCase().includes("codegen") && message.includes("?")) {
			console.log(`Processing question from ${sender}: ${message}`);

			// In a real implementation, you would:
			// 1. Process the question with Codegen
			// 2. Generate a response
			// 3. Send the response back to the chat

			// For this example, we'll just send a hardcoded response
			await this.sendChatMessage(
				`Hello ${sender}, I'm the Codegen Assistant. I'm here to help with your Codegen questions!`,
			);
		}
	}

	/**
	 * Send a chat message to the meeting
	 * @param {string} message - The message to send
	 */
	async sendChatMessage(message) {
		if (!this.isConnected) {
			console.log("Not connected to a meeting");
			return;
		}

		// In a real implementation, you would use the Zoom SDK to send a chat message
		// For this example, we'll just log the message
		console.log(`Sending chat message: ${message}`);
	}

	/**
	 * Close the bot
	 */
	async close() {
		if (this.isConnected) {
			await this.leaveMeeting();
		}

		if (this.browser) {
			await this.browser.close();
		}

		console.log("Bot closed");
	}
}

/**
 * Example usage
 */
async function main() {
	const bot = new CodegenZoomBot();

	try {
		// Initialize the bot
		await bot.initialize();

		// Join a meeting
		const meetingNumber = "123456789";
		const password = "password";
		await bot.joinMeeting(meetingNumber, password);

		// Keep the bot running for a while
		console.log("Bot is running. Press Ctrl+C to exit.");

		// Handle process termination
		process.on("SIGINT", async () => {
			console.log("Shutting down...");
			await bot.close();
			process.exit(0);
		});
	} catch (error) {
		console.error("Error:", error);
		await bot.close();
	}
}

// Run the example if this script is executed directly
if (require.main === module) {
	main();
}

module.exports = CodegenZoomBot;
