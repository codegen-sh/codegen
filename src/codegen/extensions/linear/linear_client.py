import mimetypes
import os
from pathlib import Path
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from codegen.extensions.linear.types import LinearAttachment, LinearComment, LinearIssue, LinearTeam, LinearUploadResponse, LinearUser
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class LinearClient:
    api_headers: dict
    api_endpoint = "https://api.linear.app/graphql"

    def __init__(self, access_token: Optional[str] = None, team_id: Optional[str] = None, max_retries: int = 3, backoff_factor: float = 0.5):
        if not access_token:
            access_token = os.getenv("LINEAR_ACCESS_TOKEN")
            if not access_token:
                msg = "access_token is required"
                raise ValueError(msg)
        self.access_token = access_token

        if not team_id:
            team_id = os.getenv("LINEAR_TEAM_ID")
        self.team_id = team_id

        self.api_headers = {
            "Content-Type": "application/json",
            "Authorization": self.access_token,
        }

        # Set up a session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],  # POST is important for GraphQL
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_issue(self, issue_id: str) -> LinearIssue:
        query = """
            query getIssue($issueId: String!) {
                issue(id: $issueId) {
                    id
                    title
                    description
                }
            }
        """
        variables = {"issueId": issue_id}
        response = self.session.post(self.api_endpoint, headers=self.api_headers, json={"query": query, "variables": variables})
        data = response.json()
        issue_data = data["data"]["issue"]
        return LinearIssue(id=issue_data["id"], title=issue_data["title"], description=issue_data["description"])

    def get_issue_comments(self, issue_id: str) -> list[LinearComment]:
        query = """
            query getIssueComments($issueId: String!) {
                issue(id: $issueId) {
                    comments {
                    nodes {
                        id
                        body
                        user {
                            id
                            name
                        }
                    }

                    }
                }
            }
        """
        variables = {"issueId": issue_id}
        response = self.session.post(self.api_endpoint, headers=self.api_headers, json={"query": query, "variables": variables})
        data = response.json()
        comments = data["data"]["issue"]["comments"]["nodes"]

        # Parse comments into list of LinearComment objects
        parsed_comments = []
        for comment in comments:
            user = comment.get("user", None)
            parsed_comment = LinearComment(id=comment["id"], body=comment["body"], user=LinearUser(id=user.get("id"), name=user.get("name")) if user else None)
            parsed_comments.append(parsed_comment)

        # Convert raw comments to LinearComment objects
        return parsed_comments

    def comment_on_issue(self, issue_id: str, body: str) -> LinearComment:
        """Add a comment to an issue."""
        query = """mutation makeComment($issueId: String!, $body: String!) {
          commentCreate(input: {issueId: $issueId, body: $body}) {
            comment {
              id
              body
              url
              user {
                id
                name
              }
            }
          }
        }
        """
        variables = {"issueId": issue_id, "body": body}
        response = self.session.post(
            self.api_endpoint,
            headers=self.api_headers,
            json={"query": query, "variables": variables},
        )
        data = response.json()
        try:
            comment_data = data["data"]["commentCreate"]["comment"]
            user_data = comment_data.get("user", None)
            user = LinearUser(id=user_data["id"], name=user_data["name"]) if user_data else None

            return LinearComment(id=comment_data["id"], body=comment_data["body"], user=user)
        except Exception as e:
            msg = f"Error creating comment\n{data}\n{e}"
            raise ValueError(msg)

    def register_webhook(self, webhook_url: str, team_id: str, secret: str, enabled: bool, resource_types: list[str]):
        mutation = """
            mutation createWebhook($input: WebhookCreateInput!) {
                webhookCreate(input: $input) {
                    success
                    webhook {
                    id
                    enabled
                    }
                }
            }
        """

        variables = {
            "input": {
                "url": webhook_url,
                "teamId": team_id,
                "resourceTypes": resource_types,
                "enabled": enabled,
                "secret": secret,
            }
        }

        response = self.session.post(self.api_endpoint, headers=self.api_headers, json={"query": mutation, "variables": variables})
        body = response.json()
        return body

    def search_issues(self, query: str, limit: int = 10) -> list[LinearIssue]:
        """Search for issues using a query string.

        Args:
            query: Search query string
            limit: Maximum number of issues to return (default: 10)

        Returns:
            List of LinearIssue objects matching the search query
        """
        graphql_query = """
            query searchIssues($query: String!, $limit: Int!) {
                issueSearch(query: $query, first: $limit) {
                    nodes {
                        id
                        title
                        description
                    }
                }
            }
        """
        variables = {"query": query, "limit": limit}
        response = self.session.post(
            self.api_endpoint,
            headers=self.api_headers,
            json={"query": graphql_query, "variables": variables},
        )
        data = response.json()

        try:
            issues_data = data["data"]["issueSearch"]["nodes"]
            return [
                LinearIssue(
                    id=issue["id"],
                    title=issue["title"],
                    description=issue["description"],
                )
                for issue in issues_data
            ]
        except Exception as e:
            msg = f"Error searching issues\n{data}\n{e}"
            raise Exception(msg)

    def create_issue(self, title: str, description: str | None = None, team_id: str | None = None) -> LinearIssue:
        """Create a new issue.

        Args:
            title: Title of the issue
            description: Optional description of the issue
            team_id: Optional team ID. If not provided, uses the client's configured team_id

        Returns:
            The created LinearIssue object

        Raises:
            ValueError: If no team_id is provided or configured
        """
        if not team_id:
            team_id = self.team_id
            if not team_id:
                msg = "team_id must be provided either during client initialization or in the create_issue call"
                raise ValueError(msg)

        mutation = """
            mutation createIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    success
                    issue {
                        id
                        title
                        description
                    }
                }
            }
        """

        variables = {
            "input": {
                "teamId": team_id,
                "title": title,
                "description": description,
            }
        }

        response = self.session.post(
            self.api_endpoint,
            headers=self.api_headers,
            json={"query": mutation, "variables": variables},
        )
        data = response.json()

        try:
            issue_data = data["data"]["issueCreate"]["issue"]
            return LinearIssue(
                id=issue_data["id"],
                title=issue_data["title"],
                description=issue_data["description"],
            )
        except Exception as e:
            msg = f"Error creating issue\n{data}\n{e}"
            raise Exception(msg)

    def get_teams(self) -> list[LinearTeam]:
        """Get all teams the authenticated user has access to.

        Returns:
            List of LinearTeam objects
        """
        query = """
            query {
                teams {
                    nodes {
                        id
                        name
                        key
                    }
                }
            }
        """

        response = self.session.post(
            self.api_endpoint,
            headers=self.api_headers,
            json={"query": query},
        )
        data = response.json()

        try:
            teams_data = data["data"]["teams"]["nodes"]
            return [
                LinearTeam(
                    id=team["id"],
                    name=team["name"],
                    key=team["key"],
                )
                for team in teams_data
            ]
        except Exception as e:
            msg = f"Error getting teams\n{data}\n{e}"
            raise Exception(msg)

    def get_issue_attachments(self, issue_id: str) -> list[LinearAttachment]:
        """Get all attachments for an issue.

        Args:
            issue_id: ID of the issue to get attachments for

        Returns:
            List of LinearAttachment objects
        """
        query = """
            query getIssueAttachments($issueId: String!) {
                issue(id: $issueId) {
                    attachments {
                        nodes {
                            id
                            url
                            title
                            subtitle
                            size
                            contentType
                            source
                        }
                    }
                }
            }
        """

        variables = {"issueId": issue_id}
        response = self.session.post(
            self.api_endpoint,
            headers=self.api_headers,
            json={"query": query, "variables": variables},
        )
        data = response.json()

        try:
            attachments_data = data["data"]["issue"]["attachments"]["nodes"]
            return [
                LinearAttachment(
                    id=attachment["id"],
                    url=attachment["url"],
                    title=attachment["title"],
                    subtitle=attachment.get("subtitle"),
                    size=attachment.get("size"),
                    content_type=attachment.get("contentType"),
                    source=attachment.get("source"),
                    issue_id=issue_id,
                )
                for attachment in attachments_data
            ]
        except Exception as e:
            logger.exception(f"Error getting issue attachments: {e}")
            return []

    def download_attachment(self, attachment_url: str) -> bytes:
        """Download a file attachment from Linear.

        Args:
            attachment_url: URL of the attachment to download

        Returns:
            Binary content of the attachment
        """
        # Linear files are stored at uploads.linear.app
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = self.session.get(attachment_url, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.exception(f"Error downloading attachment: {e}")
            msg = f"Failed to download attachment: {e}"
            raise Exception(msg)

    def request_upload_url(self, content_type: str, filename: str, size: int) -> LinearUploadResponse:
        """Request a pre-signed URL for file upload.

        Args:
            content_type: MIME type of the file
            filename: Name of the file
            size: Size of the file in bytes

        Returns:
            LinearUploadResponse with upload URL and headers
        """
        mutation = """
            mutation FileUpload($contentType: String!, $filename: String!, $size: Int!) {
                fileUpload(contentType: $contentType, filename: $filename, size: $size) {
                    success
                    uploadFile {
                        assetUrl
                        uploadUrl
                        headers {
                            key
                            value
                        }
                    }
                }
            }
        """

        variables = {
            "contentType": content_type,
            "filename": filename,
            "size": size,
        }

        response = self.session.post(
            self.api_endpoint,
            headers=self.api_headers,
            json={"query": mutation, "variables": variables},
        )
        data = response.json()

        try:
            return LinearUploadResponse.model_validate(data["data"])
        except Exception as e:
            logger.exception(f"Error requesting upload URL: {e}")
            msg = f"Failed to request upload URL: {e}"
            raise Exception(msg)

    def upload_file(self, file_path: str) -> str:
        """Upload a file to Linear.

        Args:
            file_path: Path to the file to upload

        Returns:
            URL of the uploaded file
        """
        path = Path(file_path)
        if not path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        # Get file info
        file_size = path.stat().st_size
        file_name = path.name
        content_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        # Request upload URL
        upload_response = self.request_upload_url(content_type, file_name, file_size)

        if not upload_response.success or not upload_response.uploadFile:
            msg = "Failed to request upload URL"
            raise Exception(msg)

        upload_url = upload_response.uploadFile.uploadUrl
        asset_url = upload_response.uploadFile.assetUrl

        # Prepare headers for the PUT request
        headers = {
            "Content-Type": content_type,
            "Cache-Control": "public, max-age=31536000",
        }

        # Add headers from the upload response
        for header in upload_response.uploadFile.headers:
            headers[header.key] = header.value

        # Upload the file
        with open(file_path, "rb") as file:
            response = self.session.put(upload_url, headers=headers, data=file)
            response.raise_for_status()

        return asset_url
