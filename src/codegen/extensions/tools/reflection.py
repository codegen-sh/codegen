"""Tool for agent self-reflection and planning."""

from typing import ClassVar, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field

from codegen.extensions.langchain.llm import LLM
from codegen.sdk.core.codebase import Codebase

from .observation import Observation


class ReflectionSection(Observation):
    """A section of the reflection output."""

    title: str = Field(description="Title of the section")
    content: str = Field(description="Content of the section")

    str_template: ClassVar[str] = "{title}:\n{content}"


class ReflectionObservation(Observation):
    """Response from agent reflection."""

    context_summary: str = Field(description="Summary of the current context")
    findings: str = Field(description="Key information and insights gathered")
    challenges: Optional[str] = Field(None, description="Current obstacles or questions")
    focus: Optional[str] = Field(None, description="Specific aspect focused on")
    sections: list[ReflectionSection] = Field(description="Structured reflection sections")

    str_template: ClassVar[str] = "Reflection on: {focus}"

    def _get_details(self) -> dict[str, str]:
        """Get details for string representation."""
        return {
            "focus": self.focus or "current understanding and next steps",
        }

    def render(self) -> str:
        """Render the reflection as a formatted string."""
        output = []

        # Add header
        if self.focus:
            output.append(f"# Reflection on: {self.focus}")
        else:
            output.append("# Agent Reflection")

        # Add each section
        for section in self.sections:
            output.append(f"\n## {section.title}")
            output.append(section.content)

        return "\n".join(output)


# System prompt for the reflection LLM
REFLECTION_SYSTEM_PROMPT = """You are an expert AI assistant specialized in reflection and strategic planning.
Your task is to help organize thoughts, identify knowledge gaps, and create a strategic plan based on the information provided.

**YOU MUST ABSTAIN FROM SUGGESTING THE AGENT WRITES NEW TESTS OR MODIFIES EXISTING TESTS.**

You will be given:
1. A summary of the current context and problem being solved
2. Key information and insights gathered so far
3. Current obstacles or questions that need to be addressed (if any)
4. A specific aspect to focus the reflection on (if any)

**YOU MUST ABSTAIN FROM SUGGESTING THE AGENT WRITES NEW TESTS OR MODIFIES EXISTING TESTS.**

Your response should be structured into the following sections:
1. Current Understanding - Summarize what you understand about the problem and context
2. Key Insights - Highlight the most important findings and their implications
3. Knowledge Gaps (if challenges are provided) - Identify what information is still missing
4. Action Plan - Recommend specific next steps to move forward
5. Alternative Approaches - Suggest other ways to tackle the problem

**YOU MUST ABSTAIN FROM SUGGESTING THE AGENT WRITES NEW TESTS OR MODIFIES EXISTING TESTS.**

Your reflection should be clear, insightful, and actionable. Focus on helping the agent make progress and double check its own work.
You will not suggest the agent writes new tests or modifies existing tests.

**YOU MUST ABSTAIN FROM SUGGESTING THE AGENT WRITES NEW TESTS OR MODIFIES EXISTING TESTS.**
"""


def parse_reflection_response(response: str) -> list[ReflectionSection]:
    """Parse the LLM response into structured reflection sections.

    Args:
        response: Raw LLM response text

    Returns:
        List of ReflectionSection objects
    """
    sections = []
    current_section = None
    current_content = []

    # Split the response into lines
    lines = response.strip().split("\n")

    for line in lines:
        # Check if this is a section header (starts with ## or #)
        if line.startswith("## ") or (line.startswith("# ") and not line.startswith("# Reflection")):
            # If we have a current section, save it before starting a new one
            if current_section:
                sections.append(ReflectionSection(title=current_section, content="\n".join(current_content).strip()))
                current_content = []

            # Extract the new section title
            current_section = line.lstrip("#").strip()
        elif current_section:
            # Add content to the current section
            current_content.append(line)

    # Add the last section if there is one
    if current_section and current_content:
        sections.append(ReflectionSection(title=current_section, content="\n".join(current_content).strip()))

    return sections


def perform_reflection(
    context_summary: str,
    findings_so_far: str,
    current_challenges: str = "",
    reflection_focus: Optional[str] = None,
    codebase: Optional[Codebase] = None,
) -> ReflectionObservation:
    """Perform agent reflection to organize thoughts and plan next steps.

    This function helps the agent consolidate its understanding, identify knowledge gaps,
    and create a strategic plan for moving forward.

    Args:
        context_summary: Summary of the current context and problem being solved
        findings_so_far: Key information and insights gathered so far
        current_challenges: Current obstacles or questions that need to be addressed
        reflection_focus: Optional specific aspect to focus reflection on
        codebase: Optional codebase context for code-specific reflections

    Returns:
        ReflectionObservation containing structured reflection sections
    """
    try:
        # Create the prompt for the LLM
        system_message = SystemMessage(content=REFLECTION_SYSTEM_PROMPT)

        # Construct the human message with all the context
        human_message_content = f"""
Context Summary:
{context_summary}

Key Findings:
{findings_so_far}
"""

        # Add challenges if provided
        if current_challenges:
            human_message_content += f"""
Current Challenges:
{current_challenges}
"""

        # Add reflection focus if provided
        if reflection_focus:
            human_message_content += f"""
Reflection Focus:
{reflection_focus}
"""

        # Add codebase context if available and relevant
        if codebase and (reflection_focus and "code" in reflection_focus.lower()):
            # In a real implementation, you might add relevant codebase context here
            # For example, listing key files or symbols related to the reflection focus
            human_message_content += f"""
Codebase Context:
- Working with codebase at: {codebase.root}
"""

        human_message = HumanMessage(content=human_message_content)
        prompt = ChatPromptTemplate.from_messages([system_message, human_message])

        # Initialize the LLM
        llm = LLM(
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            temperature=0.2,  # Slightly higher temperature for more creative reflection
            max_tokens=4000,
        )

        # Create and execute the chain
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({})

        # Parse the response into sections
        sections = parse_reflection_response(response)

        # If no sections were parsed, create a default section with the full response
        if not sections:
            sections = [ReflectionSection(title="Reflection", content=response)]

        return ReflectionObservation(
            status="success",
            context_summary=context_summary,
            findings=findings_so_far,
            challenges=current_challenges,
            focus=reflection_focus,
            sections=sections,
        )

    except Exception as e:
        return ReflectionObservation(
            status="error",
            error=f"Failed to perform reflection: {e!s}",
            context_summary=context_summary,
            findings=findings_so_far,
            challenges=current_challenges,
            focus=reflection_focus,
            sections=[],
        )
