"""Tests for top-level imports in the codegen package."""


class TestTopLevelImports:
    """Test that we can properly import classes from the top level."""

    def test_can_import_agent_from_top_level(self):
        """Test that we can import Agent directly from codegen."""
        from codegen import Agent

        assert Agent is not None
        
        # Verify it's the same class as the one in codegen.agents.agent
        from codegen.agents.agent import Agent as AgentFromModule
        assert Agent is AgentFromModule

