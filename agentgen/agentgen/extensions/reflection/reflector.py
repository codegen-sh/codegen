"""
Reflector module for agentgen.

This module provides a Reflector class that can evaluate agent outputs
and provide feedback for improvement.
"""

import os
import json
import logging
import traceback
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass

from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReflectionResult:
    """Result of a reflection evaluation."""
    
    is_valid: bool
    """Whether the output is valid."""
    
    score: float
    """Score between 0 and 1 indicating the quality of the output."""
    
    feedback: str
    """Feedback on the output."""
    
    improved_output: Optional[str] = None
    """Improved version of the output, if available."""


class Reflector:
    """Class for reflecting on agent outputs and providing feedback."""
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        model_provider: str = "anthropic",
        model_name: str = "claude-3-7-sonnet-latest",
        judge_model_provider: str = "openai",
        judge_model_name: str = "gpt-4o",
    ):
        """Initialize the reflector.
        
        Args:
            output_dir: Directory to store outputs.
            anthropic_api_key: Anthropic API key.
            openai_api_key: OpenAI API key.
            model_provider: Model provider to use for generation.
            model_name: Model name to use for generation.
            judge_model_provider: Model provider to use for evaluation.
            judge_model_name: Model name to use for evaluation.
        """
        self.output_dir = output_dir or os.environ.get("OUTPUT_DIR", "output")
        
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        
        self.model_provider = model_provider
        self.model_name = model_name
        
        self.judge_model_provider = judge_model_provider
        self.judge_model_name = judge_model_name
        
        # Initialize models
        if self.model_provider == "anthropic":
            self.model = ChatAnthropic(
                model=self.model_name,
                anthropic_api_key=self.anthropic_api_key,
                temperature=0.2,
            )
        else:
            self.model = ChatOpenAI(
                model=self.model_name,
                openai_api_key=self.openai_api_key,
                temperature=0.2,
            )
        
        if self.judge_model_provider == "anthropic":
            self.judge_model = ChatAnthropic(
                model=self.judge_model_name,
                anthropic_api_key=self.anthropic_api_key,
                temperature=0.0,
            )
        else:
            self.judge_model = ChatOpenAI(
                model=self.judge_model_name,
                openai_api_key=self.openai_api_key,
                temperature=0.0,
            )
    
    def evaluate_pr_review(
        self,
        pr_review: Dict[str, Any],
        requirements: List[Dict[str, Any]],
        codebase_patterns: List[Dict[str, Any]],
    ) -> ReflectionResult:
        """Evaluate a PR review against requirements and codebase patterns.
        
        Args:
            pr_review: PR review to evaluate.
            requirements: List of requirements to check against.
            codebase_patterns: List of codebase patterns to check against.
            
        Returns:
            ReflectionResult: Result of the evaluation.
        """
        # Create evaluation prompt
        evaluation_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert code reviewer tasked with evaluating a PR review.
Your job is to determine if the PR review correctly assessed whether the PR meets all requirements and follows codebase patterns.

Evaluate the PR review based on these criteria:
1. Completeness - Does it address all requirements?
2. Accuracy - Does it correctly identify issues?
3. Actionability - Does it provide clear suggestions for improvement?
4. Consistency - Does it align with codebase patterns?

Provide a score between 0 and 1, where:
- 0.0-0.3: Poor review that misses critical issues
- 0.4-0.6: Adequate review but with significant gaps
- 0.7-0.8: Good review with minor issues
- 0.9-1.0: Excellent review that thoroughly addresses all aspects

Format your response as a JSON object with these fields:
{
  "is_valid": true/false,
  "score": 0.0-1.0,
  "feedback": "Detailed feedback on the PR review",
  "improved_output": "Improved version of the PR review (if needed)"
}"""),
            HumanMessage(content=f"""
# PR Review to Evaluate
```json
{json.dumps(pr_review, indent=2)}
```

# Requirements
```json
{json.dumps(requirements, indent=2)}
```

# Codebase Patterns
```json
{json.dumps(codebase_patterns, indent=2)}
```

Evaluate this PR review and provide your assessment.
"""),
        ])
        
        # Run evaluation
        try:
            evaluation_result = self.judge_model.invoke(evaluation_prompt.format_messages())
            
            # Parse result
            result_text = evaluation_result.content
            result_json = json.loads(result_text)
            
            return ReflectionResult(
                is_valid=result_json.get("is_valid", False),
                score=result_json.get("score", 0.0),
                feedback=result_json.get("feedback", ""),
                improved_output=result_json.get("improved_output"),
            )
        except Exception as e:
            logger.error(f"Error evaluating PR review: {e}")
            return ReflectionResult(
                is_valid=False,
                score=0.0,
                feedback=f"Error evaluating PR review: {e}",
                improved_output=None,
            )
    
    def improve_pr_review(
        self,
        pr_review: Dict[str, Any],
        reflection_result: ReflectionResult,
        requirements: List[Dict[str, Any]],
        codebase_patterns: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Improve a PR review based on reflection feedback.
        
        Args:
            pr_review: PR review to improve.
            reflection_result: Result of the reflection evaluation.
            requirements: List of requirements to check against.
            codebase_patterns: List of codebase patterns to check against.
            
        Returns:
            Dict[str, Any]: Improved PR review.
        """
        if reflection_result.is_valid and reflection_result.score >= 0.8:
            # No need to improve
            return pr_review
        
        # Create improvement prompt
        improvement_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert code reviewer tasked with improving a PR review.
Your job is to enhance the PR review based on feedback to ensure it correctly assesses whether the PR meets all requirements and follows codebase patterns.

Create an improved PR review that:
1. Addresses all requirements thoroughly
2. Correctly identifies issues
3. Provides clear and actionable suggestions
4. Aligns with codebase patterns

Format your response as a JSON object with the same structure as the original PR review."""),
            HumanMessage(content=f"""
# Original PR Review
```json
{json.dumps(pr_review, indent=2)}
```

# Feedback on the PR Review
{reflection_result.feedback}

# Requirements
```json
{json.dumps(requirements, indent=2)}
```

# Codebase Patterns
```json
{json.dumps(codebase_patterns, indent=2)}
```

Provide an improved version of the PR review that addresses the feedback.
"""),
        ])
        
        # Run improvement
        try:
            improvement_result = self.model.invoke(improvement_prompt.format_messages())
            
            # Parse result
            result_text = improvement_result.content
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_match = re.search(r'({.*})', result_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    logger.error("Could not extract JSON from improvement result")
                    return pr_review
            
            improved_review = json.loads(json_str)
            return improved_review
        except Exception as e:
            logger.error(f"Error improving PR review: {e}")
            return pr_review