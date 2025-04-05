"""
Unified configuration module for the integrated agent application.
This module provides a centralized configuration system that handles all environment variables
from the different agent applications (integrated_agent, pr_review_agent, integrated_pr_agent, requirements_tracker).
"""

import os
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, validator

class SlackConfig(BaseModel):
    """Slack integration configuration."""
    bot_token: Optional[str] = Field(None, description="Slack bot token (SLACK_BOT_TOKEN)")
    app_token: Optional[str] = Field(None, description="Slack app token (SLACK_APP_TOKEN)")
    channel_id: Optional[str] = Field(None, description="Slack channel ID (SLACK_CHANNEL_ID)")
    user_id: Optional[str] = Field(None, description="Codegen user ID (CODEGEN_USER_ID)")

    @validator('bot_token', 'app_token', 'channel_id', 'user_id', pre=True)
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

class GitHubConfig(BaseModel):
    """GitHub integration configuration."""
    token: Optional[str] = Field(None, description="GitHub token (GITHUB_TOKEN)")
    repo: Optional[str] = Field(None, description="GitHub repository (GITHUB_REPO)")
    webhook_secret: Optional[str] = Field(None, description="GitHub webhook secret (WEBHOOK_SECRET)")
    ngrok_auth_token: Optional[str] = Field(None, description="Ngrok auth token (NGROK_AUTH_TOKEN)")
    ngrok_domain: Optional[str] = Field(None, description="Ngrok domain (NGROK_DOMAIN)")

    @validator('token', 'repo', 'webhook_secret', 'ngrok_auth_token', 'ngrok_domain', pre=True)
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

class AIConfig(BaseModel):
    """AI provider configuration."""
    provider: str = Field("anthropic", description="AI provider (anthropic, openai)")
    model_name: str = Field("claude-3-opus-20240229", description="Model name to use")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key (ANTHROPIC_API_KEY)")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (OPENAI_API_KEY)")
    
    @validator('anthropic_api_key', 'openai_api_key', pre=True)
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v

class AppConfig(BaseModel):
    """Application configuration."""
    data_dir: str = Field("./data", description="Data directory (DATA_DIR)")
    docs_path: str = Field("./docs", description="Documentation path (DOCS_PATH)")
    output_dir: str = Field("./output", description="Output directory (OUTPUT_DIR)")
    port: int = Field(8000, description="Application port (PORT)")
    interval: int = Field(3600, description="Check interval in seconds (INTERVAL)")

class WorkflowConfig(BaseModel):
    """Workflow configuration."""
    auto_start_requirements: bool = Field(False, description="Auto-start requirements tracking")
    auto_review_prs: bool = Field(False, description="Auto-review PRs")
    auto_merge_prs: bool = Field(False, description="Auto-merge PRs that pass review")
    auto_update_status: bool = Field(True, description="Auto-update workflow status")

class Config(BaseModel):
    """Unified configuration for the integrated agent application."""
    slack: SlackConfig = Field(default_factory=SlackConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    app: AppConfig = Field(default_factory=AppConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)

    def to_env(self) -> Dict[str, str]:
        """Convert configuration to environment variables."""
        env = {}
        
        # Slack
        if self.slack.bot_token:
            env["SLACK_BOT_TOKEN"] = self.slack.bot_token
        if self.slack.app_token:
            env["SLACK_APP_TOKEN"] = self.slack.app_token
        if self.slack.channel_id:
            env["SLACK_CHANNEL_ID"] = self.slack.channel_id
            env["SLACK_CHANNEL"] = self.slack.channel_id  # For compatibility
        if self.slack.user_id:
            env["CODEGEN_USER_ID"] = self.slack.user_id
        
        # GitHub
        if self.github.token:
            env["GITHUB_TOKEN"] = self.github.token
        if self.github.repo:
            env["GITHUB_REPO"] = self.github.repo
        if self.github.webhook_secret:
            env["WEBHOOK_SECRET"] = self.github.webhook_secret
        if self.github.ngrok_auth_token:
            env["NGROK_AUTH_TOKEN"] = self.github.ngrok_auth_token
        if self.github.ngrok_domain:
            env["NGROK_DOMAIN"] = self.github.ngrok_domain
        
        # AI
        env["AI_PROVIDER"] = self.ai.provider
        env["AI_MODEL_NAME"] = self.ai.model_name
        if self.ai.anthropic_api_key:
            env["ANTHROPIC_API_KEY"] = self.ai.anthropic_api_key
        if self.ai.openai_api_key:
            env["OPENAI_API_KEY"] = self.ai.openai_api_key
        
        # App
        env["DATA_DIR"] = self.app.data_dir
        env["DOCS_PATH"] = self.app.docs_path
        env["OUTPUT_DIR"] = self.app.output_dir
        env["PORT"] = str(self.app.port)
        env["INTERVAL"] = str(self.app.interval)
        
        # Workflow
        env["AUTO_START_REQUIREMENTS"] = str(int(self.workflow.auto_start_requirements))
        env["AUTO_REVIEW_PRS"] = str(int(self.workflow.auto_review_prs))
        env["AUTO_MERGE_PRS"] = str(int(self.workflow.auto_merge_prs))
        env["AUTO_UPDATE_STATUS"] = str(int(self.workflow.auto_update_status))
        
        return env

    def update_from_env(self) -> None:
        """Update configuration from environment variables."""
        # Slack
        if os.environ.get("SLACK_BOT_TOKEN"):
            self.slack.bot_token = os.environ["SLACK_BOT_TOKEN"]
        if os.environ.get("SLACK_APP_TOKEN"):
            self.slack.app_token = os.environ["SLACK_APP_TOKEN"]
        if os.environ.get("SLACK_CHANNEL_ID"):
            self.slack.channel_id = os.environ["SLACK_CHANNEL_ID"]
        elif os.environ.get("SLACK_CHANNEL"):
            self.slack.channel_id = os.environ["SLACK_CHANNEL"]
        if os.environ.get("CODEGEN_USER_ID"):
            self.slack.user_id = os.environ["CODEGEN_USER_ID"]
        
        # GitHub
        if os.environ.get("GITHUB_TOKEN"):
            self.github.token = os.environ["GITHUB_TOKEN"]
        if os.environ.get("GITHUB_REPO"):
            self.github.repo = os.environ["GITHUB_REPO"]
        if os.environ.get("WEBHOOK_SECRET"):
            self.github.webhook_secret = os.environ["WEBHOOK_SECRET"]
        if os.environ.get("NGROK_AUTH_TOKEN"):
            self.github.ngrok_auth_token = os.environ["NGROK_AUTH_TOKEN"]
        if os.environ.get("NGROK_DOMAIN"):
            self.github.ngrok_domain = os.environ["NGROK_DOMAIN"]
        
        # AI
        if os.environ.get("AI_PROVIDER"):
            self.ai.provider = os.environ["AI_PROVIDER"]
        if os.environ.get("AI_MODEL_NAME"):
            self.ai.model_name = os.environ["AI_MODEL_NAME"]
        if os.environ.get("ANTHROPIC_API_KEY"):
            self.ai.anthropic_api_key = os.environ["ANTHROPIC_API_KEY"]
        if os.environ.get("OPENAI_API_KEY"):
            self.ai.openai_api_key = os.environ["OPENAI_API_KEY"]
        
        # App
        if os.environ.get("DATA_DIR"):
            self.app.data_dir = os.environ["DATA_DIR"]
        if os.environ.get("DOCS_PATH"):
            self.app.docs_path = os.environ["DOCS_PATH"]
        if os.environ.get("OUTPUT_DIR"):
            self.app.output_dir = os.environ["OUTPUT_DIR"]
        if os.environ.get("PORT"):
            try:
                self.app.port = int(os.environ["PORT"])
            except ValueError:
                pass
        if os.environ.get("INTERVAL"):
            try:
                self.app.interval = int(os.environ["INTERVAL"])
            except ValueError:
                pass
        
        # Workflow
        if os.environ.get("AUTO_START_REQUIREMENTS"):
            try:
                self.workflow.auto_start_requirements = bool(int(os.environ["AUTO_START_REQUIREMENTS"]))
            except ValueError:
                pass
        if os.environ.get("AUTO_REVIEW_PRS"):
            try:
                self.workflow.auto_review_prs = bool(int(os.environ["AUTO_REVIEW_PRS"]))
            except ValueError:
                pass
        if os.environ.get("AUTO_MERGE_PRS"):
            try:
                self.workflow.auto_merge_prs = bool(int(os.environ["AUTO_MERGE_PRS"]))
            except ValueError:
                pass
        if os.environ.get("AUTO_UPDATE_STATUS"):
            try:
                self.workflow.auto_update_status = bool(int(os.environ["AUTO_UPDATE_STATUS"]))
            except ValueError:
                pass

    def apply_to_env(self) -> None:
        """Apply configuration to environment variables."""
        env_vars = self.to_env()
        for key, value in env_vars.items():
            os.environ[key] = value

# Global configuration instance
config = Config()
config.update_from_env()