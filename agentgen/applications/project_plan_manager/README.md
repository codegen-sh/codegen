# Unified Agent Application

This application integrates multiple agent functionalities into a single unified interface, including:

- PR review agent
- Requirements tracking
- Project planning
- Slack integration
- Workflow visualization

## Features

- **Unified Configuration**: All environment variables can be configured through the UI settings dialog
- **Workflow Visualization**: Track the progress of workflows with a visual interface
- **PR Review**: Automatically review PRs based on requirements and codebase context
- **Requirements Tracking**: Track requirements and their implementation status
- **Project Planning**: Create and manage project plans
- **Slack Integration**: Communicate with the agent through Slack

## Installation

1. Clone the repository
2. Install the backend dependencies:

```bash
pip install -r requirements.txt
```

3. Install the frontend dependencies:

```bash
cd frontend
npm install
```

4. Create a `.env` file with the required environment variables (or configure them through the UI)

## Usage

### Development Mode

1. Start the backend:

```bash
python main.py --reload
```

2. Start the frontend development server:

```bash
cd frontend
npm start
```

3. Open the UI in your browser at `http://localhost:3000`

### Production Mode

1. Build the frontend:

```bash
cd frontend
npm run build
```

2. Start the application:

```bash
python main.py
```

3. Open the UI in your browser at `http://localhost:8000`
4. Configure the settings through the UI
5. Start using the agent!

## Environment Variables

All environment variables can be configured through the UI settings dialog. Here are the available settings:

### Slack Configuration

- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_APP_TOKEN`: Slack app token
- `SLACK_CHANNEL_ID`: Slack channel ID
- `CODEGEN_USER_ID`: Codegen user ID

### GitHub Configuration

- `GITHUB_TOKEN`: GitHub token
- `GITHUB_REPO`: GitHub repository
- `WEBHOOK_SECRET`: GitHub webhook secret
- `NGROK_AUTH_TOKEN`: Ngrok auth token
- `NGROK_DOMAIN`: Ngrok domain

### AI Provider Configuration

- `ANTHROPIC_API_KEY`: Anthropic API key
- `OPENAI_API_KEY`: OpenAI API key

### Application Configuration

- `DATA_DIR`: Data directory
- `DOCS_PATH`: Documentation path
- `OUTPUT_DIR`: Output directory
- `PORT`: Application port
- `INTERVAL`: Check interval in seconds

## API Endpoints

The application provides a RESTful API for interacting with the agent. Here are the available endpoints:

### Settings

- `GET /settings`: Get all settings
- `PUT /settings`: Update all settings
- `GET /settings/slack`: Get Slack settings
- `PUT /settings/slack`: Update Slack settings
- `GET /settings/github`: Get GitHub settings
- `PUT /settings/github`: Update GitHub settings
- `GET /settings/ai`: Get AI settings
- `PUT /settings/ai`: Update AI settings
- `GET /settings/app`: Get application settings
- `PUT /settings/app`: Update application settings
- `GET /settings/workflow`: Get workflow settings
- `PUT /settings/workflow`: Update workflow settings
- `POST /settings/test-slack-connection`: Test Slack connection

### Workflows

- `POST /workflows`: Create a new workflow
- `GET /workflows`: Get all workflows
- `GET /workflows/{workflow_id}`: Get a workflow by ID
- `PUT /workflows/{workflow_id}`: Update a workflow
- `DELETE /workflows/{workflow_id}`: Delete a workflow
- `POST /workflows/{workflow_id}/start`: Start a workflow
- `POST /workflows/{workflow_id}/complete`: Complete a workflow
- `POST /workflows/{workflow_id}/fail`: Fail a workflow
- `POST /workflows/{workflow_id}/cancel`: Cancel a workflow
- `PUT /workflows/{workflow_id}/steps/{step_id}`: Update a workflow step
- `POST /workflows/{workflow_id}/steps/{step_id}/complete`: Complete a workflow step
- `POST /workflows/{workflow_id}/steps/{step_id}/fail`: Fail a workflow step
- `POST /workflows/{workflow_id}/steps/{step_id}/skip`: Skip a workflow step

### PR Reviews

- `POST /pr-reviews`: Create a new PR review
- `GET /pr-reviews`: Get all PR reviews
- `GET /pr-reviews/{pr_review_id}`: Get a PR review by ID
- `PUT /pr-reviews/{pr_review_id}`: Update a PR review
- `DELETE /pr-reviews/{pr_review_id}`: Delete a PR review

### Requirements

- `POST /requirements`: Create a new requirement
- `GET /requirements`: Get all requirements
- `GET /requirements/{requirement_id}`: Get a requirement by ID
- `PUT /requirements/{requirement_id}`: Update a requirement
- `DELETE /requirements/{requirement_id}`: Delete a requirement

### Project Plans

- `POST /project-plans`: Create a new project plan
- `GET /project-plans`: Get all project plans
- `GET /project-plans/{project_plan_id}`: Get a project plan by ID
- `PUT /project-plans/{project_plan_id}`: Update a project plan
- `DELETE /project-plans/{project_plan_id}`: Delete a project plan
![Screenshot 2025-04-05 072913](https://github.com/user-attachments/assets/46243c05-0ab2-420e-a9d6-19f94cb17a1b)

!!!!!!!!!!!! BELOW - Analyze project's full featured functionality - Mark each completed step [X] Task 1 and not completed [ ] Task 2 -- Create implementation plan for not completed steps !!!!!!

1. System Overview
The Slack Agent Bridge system serves as an intelligent intermediary between a user and Slack application, specifically focused on creating and managing PR code upgrades. The system shall:

Function as an autonomous agent that analyzes user requirements
Communicate with a Slack application through its API
Support parallel conversations across multiple projects and features
Generate, monitor, and advance PR (Pull Request) implementations
Maintain context and state across all conversations

2. Core Functionality Requirements
2.1 Multi-Project Management

[X] Requirement 2.1.1: The system shall support activation of multiple projects simultaneously
[X] Requirement 2.1.2: Each project shall maintain its own isolated context and state
[X] Requirement 2.1.3: The system shall track progress independently for each active project
[X] Requirement 2.1.4: Resources shall be allocated fairly across all active projects
[X] Requirement 2.1.5: The system shall support at least 5 concurrent active projects

2.2 Requirements Analysis

[X] Requirement 2.2.1: The system shall parse structured requirement documents (Markdown format)
[X] Requirement 2.2.2: The system shall extract project features and components from requirements
[X] Requirement 2.2.3: The system shall generate detailed implementation plans for each feature
[X] Requirement 2.2.4: The system shall estimate implementation complexity and effort
[X] Requirement 2.2.5: The system shall identify dependencies between features

2.3 Slack Thread Management

[X] Requirement 2.3.1: The system shall create a main thread for each active project
[X] Requirement 2.3.2: The system shall create sub-threads for individual features
[X] Requirement 2.3.3: The system shall route messages to appropriate threads based on context
[X] Requirement 2.3.4: The system shall monitor all threads simultaneously for updates
[X] Requirement 2.3.5: The system shall maintain a mapping of all active threads and their purposes

2.4 PR Generation and Management

[X] Requirement 2.4.1: The system shall generate structured PR requests with clear implementation steps
[X] Requirement 2.4.2: The system shall monitor for PR implementation notifications
[X] Requirement 2.4.3: The system shall analyze PR implementations for completeness
[X] Requirement 2.4.4: The system shall provide feedback on implementation quality and completeness
[X] Requirement 2.4.5: The system shall generate follow-up tasks for incomplete implementations

2.5 Context Maintenance

[X] Requirement 2.5.1: The system shall maintain conversation context across multiple sessions
[X] Requirement 2.5.2: The system shall associate incoming messages with the correct context
[X] Requirement 2.5.3: The system shall track the state of each feature implementation
[X] Requirement 2.5.4: The system shall persist context information to survive restarts
[X] Requirement 2.5.5: The system shall handle context switching between projects seamlessly

3. Technical Requirements
3.1 Slack Integration

[X] Requirement 3.1.1: The system shall authenticate with Slack using OAuth
[X] Requirement 3.1.2: The system shall use Slack's Web API for message posting
[X] Requirement 3.1.3: The system shall use Slack's Events API for message monitoring
[X] Requirement 3.1.4: The system shall support rich text formatting in messages
[X] Requirement 3.1.5: The system shall handle rate limiting according to Slack's guidelines

3.2 Storage and Persistence

[X] Requirement 3.2.1: The system shall persist project state to a database
[X] Requirement 3.2.2: The system shall store thread mappings for long-running conversations
[X] Requirement 3.2.3: The system shall backup critical state information regularly
[X] Requirement 3.2.4: The system shall implement transaction safety for state changes
[X] Requirement 3.2.5: The system shall support data migration for version upgrades

3.3 Natural Language Processing

[X] Requirement 3.3.1: The system shall parse user requirements written in natural language
[X] Requirement 3.3.2: The system shall extract actionable items from unstructured text
[X] Requirement 3.3.3: The system shall identify feature requirements from general descriptions
[X] Requirement 3.3.4: The system shall detect implementation status from PR descriptions
[X] Requirement 3.3.5: The system shall generate natural language responses and requests

3.4 Security

[X] Requirement 3.4.1: The system shall securely store API credentials
[X] Requirement 3.4.3: The system shall validate all incoming data
[X] Requirement 3.4.5: The system shall log security-relevant events

4. User Interface Requirements
4.1 Command Interface

[X] Requirement 4.1.2: The system shall support configuration via environment variables
[X] Requirement 4.1.3: The system shall provide clear error messages for configuration issues
[X] Requirement 4.1.4: The system shall validate configuration before startup

# Codebase Planner Implementation Requirements

## Project Overview

The Codebase Planner is a comprehensive web application for project planning and visualization with an AI-powered chat interface. The project requirements below detail the implementation plan for the Slack Agent Bridge that will connect users with this application for creating and managing PR code upgrades. This system includes a web UI for configuration and visualization of project status.

## 1. System Architecture Requirements

### 1.1 Slack Agent Bridge Core
[X] - **Requirement 1.1.1:** Develop a TypeScript/Node.js-based agent bridge application that connects to Slack API
[X] - **Requirement 1.1.2:** Implement a project context management system to handle multiple active projects
[X] - **Requirement 1.1.3:** Create a thread orchestration system for parallel conversations in Slack
[X] - **Requirement 1.1.4:** Build a PR generation and tracking system to manage code upgrades
[X] - **Requirement 1.1.5:** Develop persistence mechanisms for maintaining state across sessions

### 1.2 Integration with Codebase Planner
[X] - **Requirement 1.2.1:** Integrate with Codebase Planner's API endpoints for project data
[X] - **Requirement 1.2.2:** Implement synchronization between Slack conversations and Codebase Planner diagrams
[X] - **Requirement 1.2.3:** Develop mechanisms to translate diagram updates to PR requirements
[X] - **Requirement 1.2.4:** Create interfaces for the agent to retrieve tree structure data
[X] - **Requirement 1.2.5:** Build functionality to trigger diagram generation based on Slack conversations

### 1.3 Web Interface
[X] - **Requirement 1.3.1:** Create a Next.js web application with TypeScript for system configuration and monitoring
[X] - **Requirement 1.3.2:** Implement responsive UI using TailwindCSS for desktop and mobile access
[X] - **Requirement 1.3.3:** Develop authentication and authorization for the web interface
[ ] - **Requirement 1.3.4:** Create real-time dashboard for project status and thread activity monitoring
[X] - **Requirement 1.3.5:** Implement system configuration panels for environment variables and integration settings

## 2. Feature Requirements

### 2.1 Multi-Project Management
[X] - **Requirement 2.1.1:** Support simultaneous management of at least 5 different projects
[X] - **Requirement 2.1.2:** Implement project activation/deactivation functionality
[X] - **Requirement 2.1.3:** Develop project context isolation to prevent cross-contamination
[X] - **Requirement 2.1.4:** Create project status tracking and visualization
[X] - **Requirement 2.1.5:** Build project archiving and retrieval mechanisms
[X] - **Requirement 2.1.6:** Implement GitHub repository URL configuration for each project
[X] - **Requirement 2.1.7:** Develop functionality to add and manage reference images per project

### 2.2 Slack Thread Management
[X] - **Requirement 2.2.1:** Develop a system for creating and tracking main project threads
[X] - **Requirement 2.2.2:** Implement feature-specific thread creation and management
[X] - **Requirement 2.2.3:** Build message routing logic for directing communications to appropriate threads
[X] - **Requirement 2.2.4:** Create thread monitoring and event handling for all active threads
[X] - **Requirement 2.2.5:** Develop thread reference management for cross-thread communication
[X] - **Requirement 2.2.6:** Implement image sharing capabilities for reference images in Slack threads

### 2.3 Requirements Analysis
[X] - **Requirement 2.3.1:** Create a parser for Markdown-formatted project requirements
[X] - **Requirement 2.3.2:** Implement feature extraction from requirements documents
[X] - **Requirement 2.3.3:** Develop component relationship analysis
[X] - **Requirement 2.3.4:** Build a system for incremental document parsing when additional documentation is provided
[X] - **Requirement 2.3.5:** Create visualizations of the extracted requirements and generated implementation steps

### 2.4 Chat Interface
[ ] - **Requirement 2.4.1:** Implement an AI-powered chat interface in the web UI for user interaction
[ ] - **Requirement 2.4.2:** Develop capabilities for adjusting processing parameters through chat commands
[ ] - **Requirement 2.4.3:** Create functionality for modifying project plans via chat interactions
[ ] - **Requirement 2.4.4:** Build context-aware conversation capabilities that understand project state
[ ] - **Requirement 2.4.5:** Implement request step list generation and visualization based on documentation

### 2.5 Configuration Management
[X] - **Requirement 2.5.1:** Create a settings dialog for managing all environment variables
[X] - **Requirement 2.5.2:** Implement secure storage for sensitive configuration data
[X] - **Requirement 2.5.3:** Develop validation for all configuration parameters
[X] - **Requirement 2.5.4:** Build real-time configuration updates without service restart
[X] - **Requirement 2.5.5:** Create backup and restore functionality for system configuration

## 3. Technical Implementation Requirements

### 3.1 Frontend Implementation
[X] - **Requirement 3.1.1:** Develop the web UI using Next.js 14+ with TypeScript
[X] - **Requirement 3.1.2:** Implement responsive design with TailwindCSS
[X] - **Requirement 3.1.3:** Create reusable React components for all major UI elements
[ ] - **Requirement 3.1.4:** Build real-time updates using WebSockets
[X] - **Requirement 3.1.5:** Implement client-side state management using React Context or Redux
[X] - **Requirement 3.1.6:** Create accessible UI components following WCAG guidelines

### 3.2 Backend Implementation
[X] - **Requirement 3.2.1:** Develop backend services using Node.js with TypeScript
[X] - **Requirement 3.2.2:** Implement REST API endpoints for frontend communication
[ ] - **Requirement 3.2.3:** Create WebSocket server for real-time updates
[X] - **Requirement 3.2.4:** Build database integration for persistent storage
[X] - **Requirement 3.2.5:** Implement background workers for long-running tasks
[X] - **Requirement 3.2.6:** Develop secure API authentication and authorization

### 3.3 Slack Integration
[X] - **Requirement 3.3.1:** Implement Slack Bot API integration using Bolt.js framework
[X] - **Requirement 3.3.2:** Develop event subscription handling for real-time Slack messages
[X] - **Requirement 3.3.3:** Create message formatting for rich text and image content
[X] - **Requirement 3.3.4:** Build thread management and conversation tracking
[X] - **Requirement 3.3.5:** Implement rate limiting and backoff strategies for API calls
[X] - **Requirement 3.3.6:** Develop error handling and reconnection logic

### 3.4 GitHub Integration
[X] - **Requirement 3.4.1:** Implement GitHub API integration for repository access
[X] - **Requirement 3.4.2:** Develop PR review and tracking functionality
[ ] - **Requirement 3.4.3:** Build webhook handling for PR status updates
[X] - **Requirement 3.4.4:** Create code diff analysis for implementation verification
[X] - **Requirement 3.4.5:** Implement repository structure analysis
[X] - **Requirement 3.4.6:** Develop detailed PR review comment generation

## 4. Implementation Phases

### 4.1 Phase 1: Core System Architecture 
[X] - **Requirement 4.1.1:** Set up Next.js project with TypeScript and TailwindCSS
[X] - **Requirement 4.1.2:** Implement basic backend API server with database integration
[X] - **Requirement 4.1.3:** Create initial Slack API integration
[X] - **Requirement 4.1.4:** Develop authentication and basic web UI layout
[X] - **Requirement 4.1.5:** Implement project management data structures
[X] - **Deliverable:** Functional prototype with basic Slack communication and project configuration

### 4.2 Phase 2: Chat Interface and Thread Management
[X] - **Requirement 4.2.1:** Implement AI-powered chat interface in web UI
[X] - **Requirement 4.2.2:** Develop thread orchestration system
[X] - **Requirement 4.2.3:** Create requirements analysis parser
[X] - **Requirement 4.2.4:** Implement feature extraction logic
[X] - **Requirement 4.2.5:** Build documentation management system
[X] - **Deliverable:** Functioning chat interface with requirements parsing and thread management

### 4.3 Phase 3: PR Review and GitHub Integration 
[X] - **Requirement 4.3.1:** Implement GitHub API integration
[X] - **Requirement 4.3.2:** Develop PR review and tracking
[X] - **Requirement 4.3.3:** Build implementation analysis capabilities
[ ] - **Requirement 4.3.4:** Create step list visualization in web UI
[ ] - **Requirement 4.3.5:** Implement webhook handlers for status updates
[X] - **Deliverable:** End-to-end PR review system with GitHub integration

### 4.4 Phase 4: Multi-Project Support and Production Readiness 
[X] - **Requirement 4.4.1:** Implement parallel project management
[X] - **Requirement 4.4.2:** Develop configuration management system
[X] - **Requirement 4.4.3:** Create deployment pipeline for production
[X] - **Requirement 4.4.4:** Implement monitoring and error handling
[X] - **Requirement 4.4.5:** Optimize performance and security
[X] - **Deliverable:** Production-ready system with full multi-project support

## Implementation Plan for Incomplete Tasks

### 1. Real-time Dashboard and WebSocket Integration
- **Tasks:**
  - Implement WebSocket server in the backend for real-time updates
  - Create WebSocket client connection in the frontend
  - Develop real-time notification system for PR review status changes
  - Build dashboard components for visualizing project status and thread activity
  - Implement real-time updates for workflow progress

### 2. Chat Interface Implementation
- **Tasks:**
  - Develop AI-powered chat interface component for the web UI
  - Implement context-aware conversation capabilities
  - Create command parser for chat-based configuration adjustments
  - Build project plan modification functionality through chat
  - Implement step list generation and visualization based on documentation

### 3. GitHub Webhook Integration
- **Tasks:**
  - Create webhook endpoint for GitHub PR events
  - Implement webhook payload validation and security
  - Develop handler for automatically triggering PR reviews on PR creation/update
  - Build notification system for webhook events
  - Implement automatic PR status updates based on webhook events

### 4. Frontend PR Review Interface
- **Tasks:**
  - Create PR Review list component to display all PR reviews
  - Develop PR Review detail component to show review results
  - Implement PR review form for submitting new reviews
  - Build code diff visualization with review comments
  - Create step list visualization for PR implementation progress
