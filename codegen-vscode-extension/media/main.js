(() => {
	// Get VS Code API
	const vscode = acquireVsCodeApi();

	// DOM elements
	const messagesContainer = document.getElementById("messages");
	const messageInput = document.getElementById("message-input");
	const sendButton = document.getElementById("send-button");
	const loadingElement = document.getElementById("loading");

	// Store messages
	let messages = [];

	// Initialize
	window.addEventListener("message", (event) => {
		const message = event.data;

		switch (message.command) {
			case "updateMessages":
				messages = message.messages;
				renderMessages();
				break;
			case "showLoading":
				toggleLoading(message.value);
				break;
		}
	});

	// Send message when button is clicked
	sendButton.addEventListener("click", () => {
		sendMessage();
	});

	// Send message when Enter is pressed (without Shift)
	messageInput.addEventListener("keydown", (e) => {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	});

	// Send message to extension
	function sendMessage() {
		const text = messageInput.value.trim();
		if (text) {
			vscode.postMessage({
				command: "sendMessage",
				text: text,
			});
			messageInput.value = "";
		}
	}

	// Check if content needs to be collapsed
	function shouldCollapseContent(contentElement) {
		// Get the computed max-height value from CSS variable
		const maxHeight = Number.parseInt(
			getComputedStyle(document.documentElement).getPropertyValue(
				"--message-max-height",
			),
		);

		// If the content is taller than the max height, it should be collapsed
		return contentElement.scrollHeight > maxHeight;
	}

	// Toggle message expansion
	function toggleMessageExpansion(contentElement, indicatorElement) {
		if (contentElement.classList.contains("collapsed")) {
			// Expand
			contentElement.classList.remove("collapsed");
			indicatorElement.textContent = "Click to collapse";
		} else {
			// Collapse
			contentElement.classList.add("collapsed");
			indicatorElement.textContent = "Click to expand";
		}
	}

	// Render all messages
	function renderMessages() {
		messagesContainer.innerHTML = "";

		messages.forEach((message) => {
			const messageElement = document.createElement("div");
			messageElement.className = `message ${message.role}-message`;

			// Message content
			const contentElement = document.createElement("div");
			contentElement.className = "message-content markdown";
			contentElement.innerHTML = formatMarkdown(message.content);
			messageElement.appendChild(contentElement);

			// Add expand indicator element
			const expandIndicator = document.createElement("div");
			expandIndicator.className = "expand-indicator";
			messageElement.appendChild(expandIndicator);

			// Check if content should be collapsed (after adding to DOM to get accurate height)
			setTimeout(() => {
				if (shouldCollapseContent(contentElement)) {
					contentElement.classList.add("collapsed");
					expandIndicator.textContent = "Click to expand";
				} else {
					expandIndicator.style.display = "none"; // Hide indicator if not needed
				}
			}, 0);

			// Add click event to toggle expansion
			messageElement.addEventListener("click", (e) => {
				// Don't toggle if clicking on code action buttons
				if (e.target.closest(".code-action-button")) {
					return;
				}

				// Toggle expansion
				if (shouldCollapseContent(contentElement)) {
					toggleMessageExpansion(contentElement, expandIndicator);
				}
			});

			// Code block (if any)
			if (message.code) {
				const codeElement = document.createElement("div");
				codeElement.className = "code-block";
				codeElement.textContent = message.code;
				messageElement.appendChild(codeElement);

				// Code actions
				const actionsElement = document.createElement("div");
				actionsElement.className = "code-actions";

				// Insert code button
				const insertButton = document.createElement("button");
				insertButton.className = "code-action-button";
				insertButton.textContent = "Insert Code";
				insertButton.addEventListener("click", () => {
					vscode.postMessage({
						command: "insertCode",
						code: message.code,
					});
				});
				actionsElement.appendChild(insertButton);

				// Copy code button
				const copyButton = document.createElement("button");
				copyButton.className = "code-action-button";
				copyButton.textContent = "Copy";
				copyButton.addEventListener("click", () => {
					navigator.clipboard.writeText(message.code);
					copyButton.textContent = "Copied!";
					setTimeout(() => {
						copyButton.textContent = "Copy";
					}, 2000);
				});
				actionsElement.appendChild(copyButton);

				messageElement.appendChild(actionsElement);
			}

			// Timestamp
			const timestampElement = document.createElement("div");
			timestampElement.className = "timestamp";
			timestampElement.textContent = formatTimestamp(message.timestamp);
			messageElement.appendChild(timestampElement);

			messagesContainer.appendChild(messageElement);
		});

		// Scroll to bottom
		messagesContainer.scrollTop = messagesContainer.scrollHeight;
	}

	// Format timestamp
	function formatTimestamp(timestamp) {
		const date = new Date(timestamp);
		return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
	}

	// Toggle loading indicator
	function toggleLoading(show) {
		if (show) {
			loadingElement.classList.remove("hidden");
		} else {
			loadingElement.classList.add("hidden");
		}
	}

	// Format markdown to HTML
	function formatMarkdown(text) {
		// This is a very simple markdown parser
		// In a real extension, you might want to use a library like marked.js

		// Code blocks
		text = text.replace(
			/```(\w*)\n([\s\S]*?)\n```/g,
			"<pre><code>$2</code></pre>",
		);

		// Inline code
		text = text.replace(/`([^`]+)`/g, "<code>$1</code>");

		// Headers
		text = text.replace(/^### (.*$)/gm, "<h3>$1</h3>");
		text = text.replace(/^## (.*$)/gm, "<h2>$1</h2>");
		text = text.replace(/^# (.*$)/gm, "<h1>$1</h1>");

		// Bold
		text = text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

		// Italic
		text = text.replace(/\*(.*?)\*/g, "<em>$1</em>");

		// Lists
		text = text.replace(/^\s*\*\s(.*$)/gm, "<li>$1</li>");
		text = text.replace(/(<li>.*<\/li>)/g, "<ul>$1</ul>");

		// Links
		text = text.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');

		// Paragraphs
		text = text.replace(/\n\n/g, "</p><p>");
		text = "<p>" + text + "</p>";

		return text;
	}
})();
