"""
PR review service for analyzing pull requests against requirements.
"""

import json
import logging
import os
import re
import traceback
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from ..models import PullRequest, PRStatus, PRReviewStatus, PRSuggestion, Requirement, RequirementList

logger = logging.getLogger("integrated_pr_agent")


class PRReviewService:
    """Service for reviewing pull requests against requirements."""
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """Initialize the PR review service."""
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        
        # Initialize LLM
        if self.anthropic_api_key:
            self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
        elif self.openai_api_key:
            self.llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
        else:
            raise ValueError("Either Anthropic or OpenAI API key is required")
    
    def analyze_pr_against_requirements(
        self, pr: PullRequest, requirements: RequirementList, pr_diff: str
    ) -> Dict[str, Any]:
        """Analyze a pull request against requirements."""
        # Find the associated requirement if any
        requirement = None
        if pr.requirement_id:
            requirement = requirements.get_requirement_by_id(pr.requirement_id)
        
        # Prepare the prompt
        prompt = self._prepare_analysis_prompt(pr, requirement, requirements, pr_diff)
        
        # Run the LLM
        try:
            chain = ChatPromptTemplate.from_template(prompt) | self.llm | StrOutputParser()
            response = chain.invoke({})
            
            # Parse the response
            return self._parse_llm_response(response)
        except Exception as e:
            logger.error(f"Error analyzing PR: {e}")
            logger.error(traceback.format_exc())
            return {
                "compliant": False,
                "issues": [f"Error during automated review: {str(e)}"],
                "suggestions": [],
                "approval_recommendation": "request_changes",
                "review_comment": f"An error occurred during the automated review: {str(e)}\n\nPlease review this PR manually.",
            }
    
    def _prepare_analysis_prompt(
        self, pr: PullRequest, requirement: Optional[Requirement], requirements: RequirementList, pr_diff: str
    ) -> str:
        """Prepare the prompt for PR analysis."""
        prompt = f"""
        You are a PR review bot that checks if pull requests comply with project requirements.

        Please analyze this pull request:
        PR #{pr.number}: {pr.title}

        PR Description:
        {pr.body or "No description provided"}

        PR Diff:
        ```diff
        {pr_diff}
        ```

        """
        
        if requirement:
            prompt += f"""
            This PR is associated with the following requirement:
            
            Requirement ID: {requirement.id}
            Description: {requirement.description}
            Section: {requirement.section}
            Source: {requirement.source}
            
            """
        else:
            # If no specific requirement is associated, include all requirements
            prompt += "The PR should comply with the following requirements:\n\n"
            
            for req in requirements.requirements:
                prompt += f"- {req.description} (Section: {req.section}, Source: {req.source})\n"
        
        prompt += """
        Your task:
        1. Analyze if the PR complies with the requirement(s)
        2. Identify any issues or non-compliance
        3. Provide specific suggestions for improvement if needed
        4. Determine if the PR should be approved or needs changes

        Format your final response as a JSON object with the following structure:
        {
            "compliant": true/false,
            "issues": ["issue1", "issue2", ...],
            "suggestions": [
                {
                    "description": "suggestion1",
                    "file_path": "path/to/file.py",
                    "line_number": 42
                },
                ...
            ],
            "approval_recommendation": "approve" or "request_changes",
            "review_comment": "Your detailed review comment here"
        }
        """
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response to extract the JSON."""
        try:
            # Find JSON in the response
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON without code blocks
                json_match = re.search(r'({.*})', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.error("Could not extract JSON from LLM response")
                    return {
                        "compliant": False,
                        "issues": ["Failed to analyze PR properly"],
                        "suggestions": [],
                        "approval_recommendation": "request_changes",
                        "review_comment": "Failed to analyze PR properly. Please review manually.",
                    }

            result = json.loads(json_str)
            
            # Convert suggestions to PRSuggestion objects
            if "suggestions" in result and isinstance(result["suggestions"], list):
                suggestions = []
                for suggestion in result["suggestions"]:
                    if isinstance(suggestion, dict):
                        suggestions.append(
                            {
                                "id": str(uuid.uuid4()),
                                "description": suggestion.get("description", ""),
                                "file_path": suggestion.get("file_path"),
                                "line_number": suggestion.get("line_number"),
                                "created_at": datetime.now(),
                                "implemented": False,
                            }
                        )
                    elif isinstance(suggestion, str):
                        suggestions.append(
                            {
                                "id": str(uuid.uuid4()),
                                "description": suggestion,
                                "file_path": None,
                                "line_number": None,
                                "created_at": datetime.now(),
                                "implemented": False,
                            }
                        )
                result["suggestions"] = suggestions
            
            return result
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(traceback.format_exc())
            return {
                "compliant": False,
                "issues": ["Failed to analyze PR properly"],
                "suggestions": [],
                "approval_recommendation": "request_changes",
                "review_comment": "Failed to analyze PR properly. Please review manually.",
            }
    
    def format_review_comment(self, review_result: Dict[str, Any]) -> str:
        """Format the review comment for GitHub."""
        comment = f"# PR Review Bot Analysis\n\n"

        if review_result["compliant"]:
            comment += ":white_check_mark: **This PR complies with project requirements.**\n\n"
        else:
            comment += ":x: **This PR does not fully comply with project requirements.**\n\n"

        # Add issues if any
        if review_result.get("issues") and len(review_result["issues"]) > 0:
            comment += "## Issues\n\n"
            for issue in review_result["issues"]:
                comment += f"- {issue}\n"
            comment += "\n"

        # Add suggestions if any
        if review_result.get("suggestions") and len(review_result["suggestions"]) > 0:
            comment += "## Suggestions\n\n"
            for suggestion in review_result["suggestions"]:
                if isinstance(suggestion, dict):
                    desc = suggestion.get("description", "")
                    file_path = suggestion.get("file_path")
                    line_number = suggestion.get("line_number")
                    
                    if file_path and line_number:
                        comment += f"- {desc} (in `{file_path}` at line {line_number})\n"
                    elif file_path:
                        comment += f"- {desc} (in `{file_path}`)\n"
                    else:
                        comment += f"- {desc}\n"
                else:
                    comment += f"- {suggestion}\n"
            comment += "\n"

        # Add detailed review
        comment += "## Detailed Review\n\n"
        comment += review_result.get("review_comment", "No detailed review provided.")

        return comment
    
    def get_review_event(self, review_result: Dict[str, Any]) -> str:
        """Get the GitHub review event based on the review result."""
        if review_result.get("approval_recommendation") == "approve":
            return "APPROVE"
        else:
            return "REQUEST_CHANGES"