"""
Code research and analysis module for PR Code Review agent.
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

import markdown
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CodeInsight(BaseModel):
    """An insight about a code pattern or structure."""
    
    id: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    category: str
    importance: str = "medium"  # low, medium, high
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ResearchResult(BaseModel):
    """Results from a code research operation."""
    
    query: str
    insights: List[CodeInsight] = Field(default_factory=list)
    summary: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Researcher:
    """Code research and analysis tool."""
    
    def __init__(
        self,
        output_dir: str,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """Initialize the researcher."""
        self.output_dir = Path(output_dir) / "research"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        
        # Initialize state files
        self.research_results_file = self.output_dir / "research_results.json"
        self.insights_file = self.output_dir / "insights.json"
    
    def research_codebase(self, codebase, query: str, file_patterns: Optional[List[str]] = None) -> ResearchResult:
        """Research a codebase for patterns and insights based on a query."""
        logger.info(f"Researching codebase with query: {query}")
        
        # Search the codebase
        search_results = self._search_codebase(codebase, query, file_patterns)
        
        # Analyze the search results
        insights = self._analyze_search_results(search_results, query)
        
        # Generate a summary
        summary = self._generate_summary(insights, query)
        
        # Create the research result
        result = ResearchResult(
            query=query,
            insights=insights,
            summary=summary,
        )
        
        # Save the result
        self._save_research_result(result)
        
        return result
    
    def _search_codebase(self, codebase, query: str, file_patterns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search the codebase for files matching the query."""
        search_results = []
        
        try:
            # Use the codebase's search functionality
            results = codebase.search(query, file_patterns=file_patterns)
            
            for result in results:
                file_path = result.get("file_path", "")
                line_number = result.get("line_number")
                code_snippet = result.get("code_snippet", "")
                
                search_results.append({
                    "file_path": file_path,
                    "line_number": line_number,
                    "code_snippet": code_snippet,
                })
        
        except Exception as e:
            logger.error(f"Error searching codebase: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return search_results
    
    def _analyze_search_results(self, search_results: List[Dict[str, Any]], query: str) -> List[CodeInsight]:
        """Analyze search results to extract insights."""
        insights = []
        
        # Process each search result
        for i, result in enumerate(search_results):
            file_path = result.get("file_path", "")
            line_number = result.get("line_number")
            code_snippet = result.get("code_snippet", "")
            
            # Determine the category based on file extension and content
            category = self._determine_category(file_path, code_snippet)
            
            # Create an insight
            insight = CodeInsight(
                id=f"insight-{i+1}",
                description=f"Found code related to '{query}' in {file_path}",
                file_path=file_path,
                line_number=line_number,
                code_snippet=code_snippet,
                category=category,
            )
            
            insights.append(insight)
        
        return insights
    
    def _determine_category(self, file_path: str, code_snippet: str) -> str:
        """Determine the category of an insight based on file path and code snippet."""
        # Check file extension
        if file_path.endswith(".py"):
            if "class" in code_snippet:
                return "python-class"
            elif "def" in code_snippet:
                return "python-function"
            else:
                return "python"
        elif file_path.endswith(".js") or file_path.endswith(".ts"):
            if "class" in code_snippet:
                return "javascript-class"
            elif "function" in code_snippet or "=>" in code_snippet:
                return "javascript-function"
            else:
                return "javascript"
        elif file_path.endswith(".html"):
            return "html"
        elif file_path.endswith(".css"):
            return "css"
        elif file_path.endswith(".md"):
            return "markdown"
        elif file_path.endswith(".json"):
            return "json"
        elif file_path.endswith(".yml") or file_path.endswith(".yaml"):
            return "yaml"
        else:
            return "other"
    
    def _generate_summary(self, insights: List[CodeInsight], query: str) -> str:
        """Generate a summary of the research results."""
        if not insights:
            return f"No insights found for query: {query}"
        
        # Count insights by category
        categories = {}
        for insight in insights:
            category = insight.category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        # Generate the summary
        summary = f"Found {len(insights)} insights for query: {query}\n\n"
        
        summary += "Insights by category:\n"
        for category, count in categories.items():
            summary += f"- {category}: {count}\n"
        
        return summary
    
    def _save_research_result(self, result: ResearchResult) -> None:
        """Save a research result to disk."""
        # Save to research results file
        if self.research_results_file.exists():
            with open(self.research_results_file, "r", encoding="utf-8") as f:
                results = json.load(f)
        else:
            results = []
        
        # Add the new result
        results.append(json.loads(result.model_dump_json()))
        
        # Save the results
        with open(self.research_results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        # Save insights to insights file
        if self.insights_file.exists():
            with open(self.insights_file, "r", encoding="utf-8") as f:
                insights = json.load(f)
        else:
            insights = []
        
        # Add the new insights
        for insight in result.insights:
            insights.append(json.loads(insight.model_dump_json()))
        
        # Save the insights
        with open(self.insights_file, "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2)
    
    def get_insights_by_query(self, query: str) -> List[CodeInsight]:
        """Get insights by query."""
        if not self.research_results_file.exists():
            return []
        
        with open(self.research_results_file, "r", encoding="utf-8") as f:
            results = json.load(f)
        
        for result in results:
            if result.get("query") == query:
                insights = []
                for insight_data in result.get("insights", []):
                    insights.append(CodeInsight.model_validate(insight_data))
                return insights
        
        return []
    
    def get_all_insights(self) -> List[CodeInsight]:
        """Get all insights."""
        if not self.insights_file.exists():
            return []
        
        with open(self.insights_file, "r", encoding="utf-8") as f:
            insights_data = json.load(f)
        
        insights = []
        for insight_data in insights_data:
            insights.append(CodeInsight.model_validate(insight_data))
        
        return insights
    
    def generate_research_report(self, query: Optional[str] = None) -> str:
        """Generate a research report."""
        if query:
            insights = self.get_insights_by_query(query)
            title = f"Research Report for Query: {query}"
        else:
            insights = self.get_all_insights()
            title = "Comprehensive Research Report"
        
        if not insights:
            return f"No insights found for {title}"
        
        # Generate the report
        report = f"# {title}\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Add summary
        report += "## Summary\n\n"
        report += f"- **Total Insights:** {len(insights)}\n"
        
        # Count insights by category
        categories = {}
        for insight in insights:
            category = insight.category
            if category not in categories:
                categories[category] = 0
            categories[category] += 1
        
        report += "- **Categories:**\n"
        for category, count in categories.items():
            report += f"  - {category}: {count}\n"
        
        # Add insights
        report += "\n## Insights\n\n"
        
        for insight in insights:
            report += f"### {insight.id}: {insight.description}\n\n"
            report += f"- **File:** {insight.file_path}\n"
            if insight.line_number:
                report += f"- **Line:** {insight.line_number}\n"
            report += f"- **Category:** {insight.category}\n"
            report += f"- **Importance:** {insight.importance}\n"
            
            if insight.code_snippet:
                report += "\n```\n"
                report += insight.code_snippet
                report += "\n```\n\n"
        
        # Save the report
        report_file = self.output_dir / f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        return report
