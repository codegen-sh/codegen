"""
Settings API module for the unified agent application.
This module provides API endpoints for retrieving and updating application settings.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from .database import db
from .models import Settings
from .config import config, SlackConfig, GitHubConfig, AIConfig, AppConfig, WorkflowConfig

router = APIRouter(prefix="/settings", tags=["settings"])

class SettingsResponse(BaseModel):
    """Response model for settings."""
    slack: Dict[str, Any]
    github: Dict[str, Any]
    ai: Dict[str, Any]
    app: Dict[str, Any]
    workflow: Dict[str, Any]

class SlackConfigUpdate(BaseModel):
    """Update model for Slack configuration."""
    bot_token: Optional[str] = None
    app_token: Optional[str] = None
    channel_id: Optional[str] = None
    user_id: Optional[str] = None

class GitHubConfigUpdate(BaseModel):
    """Update model for GitHub configuration."""
    token: Optional[str] = None
    repo: Optional[str] = None
    webhook_secret: Optional[str] = None
    ngrok_auth_token: Optional[str] = None
    ngrok_domain: Optional[str] = None

class AIConfigUpdate(BaseModel):
    """Update model for AI configuration."""
    provider: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

class AppConfigUpdate(BaseModel):
    """Update model for application configuration."""
    data_dir: Optional[str] = None
    docs_path: Optional[str] = None
    output_dir: Optional[str] = None
    port: Optional[int] = None
    interval: Optional[int] = None

class WorkflowConfigUpdate(BaseModel):
    """Update model for workflow configuration."""
    auto_start_requirements: Optional[bool] = None
    auto_review_prs: Optional[bool] = None
    auto_update_status: Optional[bool] = None

class SettingsUpdate(BaseModel):
    """Update model for settings."""
    slack: Optional[SlackConfigUpdate] = None
    github: Optional[GitHubConfigUpdate] = None
    ai: Optional[AIConfigUpdate] = None
    app: Optional[AppConfigUpdate] = None
    workflow: Optional[WorkflowConfigUpdate] = None

@router.get("/", response_model=SettingsResponse)
async def get_settings():
    """Get the application settings."""
    return {
        "slack": config.slack.dict(),
        "github": config.github.dict(),
        "ai": config.ai.dict(),
        "app": config.app.dict(),
        "workflow": config.workflow.dict()
    }

@router.put("/", response_model=SettingsResponse)
async def update_settings(settings_update: SettingsUpdate):
    """Update the application settings."""
    # Update Slack configuration
    if settings_update.slack:
        for key, value in settings_update.slack.dict(exclude_unset=True).items():
            setattr(config.slack, key, value)
    
    # Update GitHub configuration
    if settings_update.github:
        for key, value in settings_update.github.dict(exclude_unset=True).items():
            setattr(config.github, key, value)
    
    # Update AI configuration
    if settings_update.ai:
        for key, value in settings_update.ai.dict(exclude_unset=True).items():
            setattr(config.ai, key, value)
    
    # Update App configuration
    if settings_update.app:
        for key, value in settings_update.app.dict(exclude_unset=True).items():
            setattr(config.app, key, value)
    
    # Update Workflow configuration
    if settings_update.workflow:
        for key, value in settings_update.workflow.dict(exclude_unset=True).items():
            setattr(config.workflow, key, value)
    
    # Apply configuration to environment variables
    config.apply_to_env()
    
    # Save settings to database
    db_settings = Settings(
        slack_bot_token=config.slack.bot_token,
        slack_app_token=config.slack.app_token,
        slack_channel_id=config.slack.channel_id,
        codegen_user_id=config.slack.user_id,
        github_token=config.github.token,
        github_repo=config.github.repo,
        webhook_secret=config.github.webhook_secret,
        ngrok_auth_token=config.github.ngrok_auth_token,
        ngrok_domain=config.github.ngrok_domain,
        ai_provider=config.ai.provider,
        anthropic_api_key=config.ai.anthropic_api_key,
        openai_api_key=config.ai.openai_api_key,
        data_dir=config.app.data_dir,
        docs_path=config.app.docs_path,
        output_dir=config.app.output_dir,
        port=config.app.port,
        interval=config.app.interval,
        auto_start_requirements=config.workflow.auto_start_requirements,
        auto_review_prs=config.workflow.auto_review_prs,
        auto_update_status=config.workflow.auto_update_status
    )
    db.update_settings(db_settings)
    
    return {
        "slack": config.slack.dict(),
        "github": config.github.dict(),
        "ai": config.ai.dict(),
        "app": config.app.dict(),
        "workflow": config.workflow.dict()
    }

@router.get("/slack", response_model=SlackConfig)
async def get_slack_settings():
    """Get the Slack settings."""
    return config.slack

@router.put("/slack", response_model=SlackConfig)
async def update_slack_settings(slack_update: SlackConfigUpdate):
    """Update the Slack settings."""
    for key, value in slack_update.dict(exclude_unset=True).items():
        setattr(config.slack, key, value)
    
    config.apply_to_env()
    
    # Save settings to database
    db_settings = db.get_settings()
    db_settings.slack_bot_token = config.slack.bot_token
    db_settings.slack_app_token = config.slack.app_token
    db_settings.slack_channel_id = config.slack.channel_id
    db_settings.codegen_user_id = config.slack.user_id
    db.update_settings(db_settings)
    
    return config.slack

@router.get("/github", response_model=GitHubConfig)
async def get_github_settings():
    """Get the GitHub settings."""
    return config.github

@router.put("/github", response_model=GitHubConfig)
async def update_github_settings(github_update: GitHubConfigUpdate):
    """Update the GitHub settings."""
    for key, value in github_update.dict(exclude_unset=True).items():
        setattr(config.github, key, value)
    
    config.apply_to_env()
    
    # Save settings to database
    db_settings = db.get_settings()
    db_settings.github_token = config.github.token
    db_settings.github_repo = config.github.repo
    db_settings.webhook_secret = config.github.webhook_secret
    db_settings.ngrok_auth_token = config.github.ngrok_auth_token
    db_settings.ngrok_domain = config.github.ngrok_domain
    db.update_settings(db_settings)
    
    return config.github

@router.get("/ai", response_model=AIConfig)
async def get_ai_settings():
    """Get the AI settings."""
    return config.ai

@router.put("/ai", response_model=AIConfig)
async def update_ai_settings(ai_update: AIConfigUpdate):
    """Update the AI settings."""
    for key, value in ai_update.dict(exclude_unset=True).items():
        setattr(config.ai, key, value)
    
    config.apply_to_env()
    
    # Save settings to database
    db_settings = db.get_settings()
    db_settings.ai_provider = config.ai.provider
    db_settings.anthropic_api_key = config.ai.anthropic_api_key
    db_settings.openai_api_key = config.ai.openai_api_key
    db.update_settings(db_settings)
    
    return config.ai

@router.get("/app", response_model=AppConfig)
async def get_app_settings():
    """Get the application settings."""
    return config.app

@router.put("/app", response_model=AppConfig)
async def update_app_settings(app_update: AppConfigUpdate):
    """Update the application settings."""
    for key, value in app_update.dict(exclude_unset=True).items():
        setattr(config.app, key, value)
    
    config.apply_to_env()
    
    # Save settings to database
    db_settings = db.get_settings()
    db_settings.data_dir = config.app.data_dir
    db_settings.docs_path = config.app.docs_path
    db_settings.output_dir = config.app.output_dir
    db_settings.port = config.app.port
    db_settings.interval = config.app.interval
    db.update_settings(db_settings)
    
    return config.app

@router.get("/workflow", response_model=WorkflowConfig)
async def get_workflow_settings():
    """Get the workflow settings."""
    return config.workflow

@router.put("/workflow", response_model=WorkflowConfig)
async def update_workflow_settings(workflow_update: WorkflowConfigUpdate):
    """Update the workflow settings."""
    for key, value in workflow_update.dict(exclude_unset=True).items():
        setattr(config.workflow, key, value)
    
    config.apply_to_env()
    
    # Save settings to database
    db_settings = db.get_settings()
    db_settings.auto_start_requirements = config.workflow.auto_start_requirements
    db_settings.auto_review_prs = config.workflow.auto_review_prs
    db_settings.auto_update_status = config.workflow.auto_update_status
    db.update_settings(db_settings)
    
    return config.workflow

@router.post("/test-slack-connection", response_model=Dict[str, bool])
async def test_slack_connection():
    """Test the Slack connection."""
    # This would be implemented with actual Slack API calls
    # For now, just return success if the token is set
    success = bool(config.slack.bot_token and config.slack.app_token)
    return {"success": success}