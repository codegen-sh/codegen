"""Test top-level imports from the codegen package."""

import pytest


class TestTopLevelImports:
    """Test that key classes can be imported at the top level of the codegen package."""

    def test_can_import_agent_from_top_level(self):
        """Test that Agent class can be imported from the top level."""
        # This should work: from codegen import Agent
        from codegen import Agent
        
        # Verify Agent class is available
        assert Agent is not None
        assert callable(Agent)
        
        # Verify it's the same class as importing from the submodule
        from codegen.agents.agent import Agent as DirectAgent
        assert Agent is DirectAgent

    def test_agent_in_all_exports(self):
        """Test that Agent is listed in __all__ exports."""
        import codegen
        
        # Agent should be in the __all__ list
        assert hasattr(codegen, '__all__')
        assert 'Agent' in codegen.__all__
        
        # Agent should be accessible as an attribute
        assert hasattr(codegen, 'Agent')
        assert codegen.Agent is not None

    def test_agent_functionality_works_from_top_level(self):
        """Test that Agent imported from top level is fully functional."""
        from codegen import Agent
        
        # Test that the class has expected methods
        assert hasattr(Agent, 'run')
        assert hasattr(Agent, 'get_status')
        assert callable(getattr(Agent, 'run'))
        assert callable(getattr(Agent, 'get_status'))
        
        # Test that we can create an Agent instance with None token (it should work)
        agent = Agent(token=None)
        assert agent is not None
        assert hasattr(agent, 'token')
        assert agent.token is None

    def test_version_still_available(self):
        """Test that version information is still available alongside Agent."""
        import codegen
        
        # Version attributes should still be available
        assert hasattr(codegen, '__version__')
        assert hasattr(codegen, 'version')
        assert hasattr(codegen, '__version_tuple__')
        assert hasattr(codegen, 'version_tuple')
        
        # They should be in __all__
        assert '__version__' in codegen.__all__
        assert 'version' in codegen.__all__
        assert '__version_tuple__' in codegen.__all__
        assert 'version_tuple' in codegen.__all__
