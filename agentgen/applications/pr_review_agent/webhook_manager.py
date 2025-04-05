import logging
import requests
from typing import List, Dict, Optional, Tuple
from logging import getLogger
from github import Github
from github.Repository import Repository
from github.GithubException import GithubException

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

class WebhookManager:
    """
    Manages GitHub webhooks for repositories.
    Ensures all repositories have webhooks configured and keeps them updated.
    """
    
    def __init__(self, github_client: Github, webhook_url: str):
        """
        Initialize the webhook manager.
        
        Args:
            github_client: GitHub client instance
            webhook_url: URL for the webhook (e.g., https://example.com/webhook)
        """
        self.github_client = github_client
        self.webhook_url = webhook_url
        logger.info(f"WebhookManager initialized with webhook URL: {webhook_url}")
    
    def get_all_repositories(self) -> List[Repository]:
        """
        Get all repositories accessible by the GitHub token.
        
        Returns:
            List of Repository objects
        """
        logger.info("Fetching all accessible repositories")
        try:
            repos = list(self.github_client.get_user().get_repos())
            logger.info(f"Found {len(repos)} repositories")
            for repo in repos:
                logger.info(f"  - {repo.full_name} (private: {repo.private})")
            return repos
        except Exception as e:
            logger.error(f"Error fetching repositories: {e}", exc_info=True)
            return []
    
    def list_webhooks(self, repo: Repository) -> List[Dict]:
        """
        List all webhooks for a repository.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            List of webhook dictionaries
        """
        logger.info(f"Listing webhooks for {repo.full_name}")
        try:
            hooks = list(repo.get_hooks())
            logger.info(f"Found {len(hooks)} webhooks for {repo.full_name}")
            for hook in hooks:
                logger.info(f"  - Hook ID: {hook.id}, URL: {hook.config.get('url', 'N/A')}, Events: {hook.events}")
            return hooks
        except GithubException as e:
            logger.error(f"Error listing webhooks for {repo.full_name}: {e.status} - {e.data.get('message', '')}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Error listing webhooks for {repo.full_name}: {e}", exc_info=True)
            return []
    
    def find_pr_review_webhook(self, repo: Repository) -> Optional[Dict]:
        """
        Find an existing PR review webhook in the repository.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            Webhook dictionary if found, None otherwise
        """
        webhooks = self.list_webhooks(repo)
        for hook in webhooks:
            hook_url = hook.config.get("url", "")
            if hook_url and "/webhook" in hook_url:
                logger.info(f"Found existing webhook in {repo.full_name}: {hook_url}")
                return hook
        logger.info(f"No existing webhook found in {repo.full_name}")
        return None
    
    def create_webhook(self, repo: Repository) -> Optional[Dict]:
        """
        Create a new webhook for PR reviews in the repository.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            Created webhook dictionary if successful, None otherwise
        """
        logger.info(f"Creating webhook for {repo.full_name} with URL: {self.webhook_url}")
        try:
            # Check if we have admin permissions
            permissions = repo.permissions
            if not permissions.admin:
                logger.warning(f"No admin permissions for {repo.full_name}. Cannot create webhook.")
                print(f"Repository {repo.full_name}: No admin permissions. Cannot create webhook.")
                return None
            
            config = {
                "url": self.webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"
            }
            
            # Add secret if available
            import os
            webhook_secret = os.environ.get("WEBHOOK_SECRET", "")
            if webhook_secret:
                logger.info(f"Adding webhook secret to configuration for {repo.full_name}")
                config["secret"] = webhook_secret
            
            logger.info(f"Creating webhook with events: pull_request, repository")
            hook = repo.create_hook(
                name="web",
                config=config,
                events=["pull_request", "repository"],
                active=True
            )
            logger.info(f"Webhook created successfully for {repo.full_name} with ID: {hook.id}")
            return hook
        except GithubException as e:
            error_message = f"Error creating webhook for {repo.full_name}: {e.status} - {e.data.get('message', '')}"
            logger.error(error_message, exc_info=True)
            print(error_message)
            if e.status == 404:
                print(f"Repository {repo.full_name}: Permission denied. Make sure your token has 'admin:repo_hook' scope.")
            elif e.status == 422:
                print(f"Repository {repo.full_name}: Invalid webhook URL or configuration. Make sure your webhook URL is publicly accessible.")
            return None
        except Exception as e:
            logger.error(f"Error creating webhook for {repo.full_name}: {e}", exc_info=True)
            print(f"Error creating webhook for {repo.full_name}: {e}")
            return None
    
    def update_webhook_url(self, repo: Repository, hook_id: int, new_url: str) -> bool:
        """
        Update a webhook URL.
        
        Args:
            repo: GitHub Repository object
            hook_id: Webhook ID
            new_url: New webhook URL
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Updating webhook URL for {repo.full_name} (Hook ID: {hook_id}) to: {new_url}")
        try:
            hook = repo.get_hook(hook_id)
            
            # Create a new config dictionary instead of modifying the existing one
            new_config = {
                "url": new_url,
                "content_type": "json",
                "insecure_ssl": "0",
                "secret": hook.config.get("secret", "")
            }
            
            # Log the current events
            logger.info(f"Current webhook events for {repo.full_name}: {hook.events}")
            
            # Update the webhook with the new config
            hook.edit(
                name="web",  # Required parameter
                config=new_config,
                events=hook.events,
                active=True
            )
            
            logger.info(f"Webhook URL updated successfully for {repo.full_name}")
            return True
        except GithubException as e:
            logger.error(f"Error updating webhook URL for {repo.full_name}: {e.status} - {e.data.get('message', '')}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error updating webhook URL for {repo.full_name}: {e}", exc_info=True)
            return False
    
    def ensure_webhook_exists(self, repo: Repository) -> Tuple[bool, str]:
        """
        Ensure a webhook exists for the repository.
        Creates one if it doesn't exist, updates if URL doesn't match.
        
        Args:
            repo: GitHub Repository object
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if webhook already exists
            existing_hook = self.find_pr_review_webhook(repo)
            
            if existing_hook:
                # Check if URL needs updating
                existing_url = existing_hook.config.get("url", "")
                if existing_url != self.webhook_url:
                    logger.info(f"Webhook URL mismatch for {repo.full_name}. Current: {existing_url}, New: {self.webhook_url}")
                    success = self.update_webhook_url(repo, existing_hook.id, self.webhook_url)
                    if success:
                        return True, f"Updated webhook URL for {repo.full_name}"
                    else:
                        return False, f"Failed to update webhook URL for {repo.full_name}"
                else:
                    logger.info(f"Webhook already exists with correct URL for {repo.full_name}")
                    return True, f"Webhook already exists with correct URL for {repo.full_name}"
            else:
                # Create new webhook
                new_hook = self.create_webhook(repo)
                if new_hook:
                    return True, f"Created new webhook for {repo.full_name}"
                else:
                    return False, f"Failed to create webhook for {repo.full_name}"
        except Exception as e:
            logger.error(f"Error ensuring webhook for {repo.full_name}: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def setup_webhooks_for_all_repos(self) -> Dict[str, str]:
        """
        Set up webhooks for all accessible repositories.
        
        Returns:
            Dictionary mapping repository names to status messages
        """
        logger.info("Setting up webhooks for all repositories")
        results = {}
        
        repos = self.get_all_repositories()
        logger.info(f"Found {len(repos)} repositories")
        
        for repo in repos:
            success, message = self.ensure_webhook_exists(repo)
            results[repo.full_name] = message
            print(f"Repository {repo.full_name}: {message}")
            
        return results
    
    def handle_repository_created(self, repo_name: str) -> Tuple[bool, str]:
        """
        Handle repository creation event.
        Sets up webhook for the newly created repository.
        
        Args:
            repo_name: Repository name in format "owner/repo"
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Handling repository creation for {repo_name}")
        try:
            repo = self.github_client.get_repo(repo_name)
            success, message = self.ensure_webhook_exists(repo)
            print(f"New repository {repo_name}: {message}")
            return success, message
        except Exception as e:
            logger.error(f"Error handling repository creation for {repo_name}: {e}", exc_info=True)
            return False, f"Error: {str(e)}"