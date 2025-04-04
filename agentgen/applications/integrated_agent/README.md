# Integrated Agent

A unified application that combines PR Review Agent and Requirements Tracker to provide a seamless workflow for tracking requirements, reviewing PRs, and coordinating with Codegen.

## Features

- **Document Management**: Upload and manage requirement documents
- **Requirements Tracking**: Extract and track requirements from documents
- **Repository Integration**: Configure GitHub repositories for tracking
- **PR Review**: Automatically review PRs against requirements
- **Project Planning**: Generate AI-assisted project plans
- **Slack Integration**: Communicate with Codegen via Slack

## Architecture

The application consists of two main components:

1. **Backend**: A FastAPI application that provides RESTful APIs for all functionality
2. **Frontend**: A React application with Material UI for the user interface

## Installation

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn
- GitHub token with repo and webhook permissions
- Anthropic API key or OpenAI API key
- Slack bot token and app token

### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export GITHUB_TOKEN=your_github_token
   export ANTHROPIC_API_KEY=your_anthropic_key
   export OPENAI_API_KEY=your_openai_key
   export SLACK_BOT_TOKEN=your_slack_bot_token
   export SLACK_APP_TOKEN=your_slack_app_token
   export CODEGEN_USER_ID=codegen_slack_user_id
   ```

4. Run the backend:
   ```bash
   python main.py
   ```

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Run the frontend:
   ```bash
   npm start
   ```

## Usage

1. Open your browser and navigate to http://localhost:3000
2. Upload requirement documents
3. Configure GitHub repositories
4. Extract requirements from documents
5. Generate project plans
6. Start the process to send requirements to Codegen

## Development

### Project Structure

- `backend/`: FastAPI backend application
  - `api.py`: API endpoints
  - `models.py`: Data models
  - `database.py`: Database operations
- `frontend/`: React frontend application
  - `src/`: Source code
    - `components/`: Reusable components
    - `pages/`: Page components
    - `utils/`: Utility functions
- `main.py`: Main entry point for the application

### Adding New Features

1. Define data models in `backend/models.py`
2. Add database operations in `backend/database.py`
3. Add API endpoints in `backend/api.py`
4. Add frontend components in `frontend/src/components/`
5. Add pages in `frontend/src/pages/`

## License

This project is licensed under the MIT License - see the LICENSE file for details.