"""Tests for MCP resources functionality."""

import json
from unittest.mock import patch

import pytest


class TestMCPResources:
    """Test MCP resources functionality."""

    def test_system_agent_prompt_resource(self):
        """Test the system://agent_prompt resource."""
        from codegen.cli.mcp.server import mcp

        # Get the agent_prompt resource function
        resources = mcp._resource_manager._resources
        assert "system://agent_prompt" in resources

        agent_prompt_resource = resources["system://agent_prompt"]

        # Test the resource function
        result = agent_prompt_resource.fn()

        # Should return a string with system prompt content
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain information about Codegen SDK
        assert "codegen" in result.lower() or "sdk" in result.lower()

    def test_system_setup_instructions_resource(self):
        """Test the system://setup_instructions resource."""
        from codegen.cli.mcp.server import mcp

        # Get the setup_instructions resource function
        resources = mcp._resource_manager._resources
        assert "system://setup_instructions" in resources

        setup_instructions_resource = resources["system://setup_instructions"]

        # Test the resource function
        result = setup_instructions_resource.fn()

        # Should return a string with setup instructions
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain setup-related content
        assert any(keyword in result.lower() for keyword in ["setup", "install", "environment", "configure"])

    def test_system_manifest_resource(self):
        """Test the system://manifest resource."""
        from codegen.cli.mcp.server import mcp

        # Get the manifest resource function
        resources = mcp._resource_manager._resources
        assert "system://manifest" in resources

        manifest_resource = resources["system://manifest"]

        # Test the resource function
        result = manifest_resource.fn()

        # Should return a dictionary with manifest information
        assert isinstance(result, dict)
        assert "name" in result
        assert "version" in result
        assert "description" in result

        # Check specific values
        assert result["name"] == "mcp-codegen"
        assert result["version"] == "0.1.0"
        assert "codegen" in result["description"].lower()

    def test_resource_mime_types(self):
        """Test that resources have correct MIME types."""
        from codegen.cli.mcp.server import mcp

        resources = mcp._resource_manager._resources
        resource_mime_types = {uri: resource.mime_type for uri, resource in resources.items()}

        # Check expected MIME types
        assert resource_mime_types["system://agent_prompt"] == "text/plain"
        assert resource_mime_types["system://setup_instructions"] == "text/plain"
        assert resource_mime_types["system://manifest"] == "application/json"

    def test_resource_descriptions(self):
        """Test that resources have appropriate descriptions."""
        from codegen.cli.mcp.server import mcp

        resources = mcp._resource_manager._resources
        resource_descriptions = {uri: resource.description for uri, resource in resources.items()}

        # Check that descriptions exist and are meaningful
        assert "agent" in resource_descriptions["system://agent_prompt"].lower()
        assert "codegen" in resource_descriptions["system://agent_prompt"].lower()

        assert "setup" in resource_descriptions["system://setup_instructions"].lower()
        assert "instructions" in resource_descriptions["system://setup_instructions"].lower()

        # Manifest resource might not have a description, but if it does, it should be meaningful
        if resource_descriptions.get("system://manifest"):
            assert len(resource_descriptions["system://manifest"]) > 0

    def test_all_resources_callable(self):
        """Test that all resource functions are callable."""
        from codegen.cli.mcp.server import mcp

        resources = mcp._resource_manager._resources
        for uri, resource in resources.items():
            assert callable(resource.fn), f"Resource {uri} function is not callable"

            # Try calling the function
            try:
                result = resource.fn()
                assert result is not None, f"Resource {uri} returned None"
            except Exception as e:
                pytest.fail(f"Resource {uri} raised exception: {e}")

    def test_resource_content_consistency(self):
        """Test that resource content is consistent across calls."""
        from codegen.cli.mcp.server import mcp

        resources = mcp._resource_manager._resources
        for uri, resource in resources.items():
            # Call the resource function multiple times
            result1 = resource.fn()
            result2 = resource.fn()

            # Results should be identical (resources should be deterministic)
            assert result1 == result2, f"Resource {uri} returned different results on multiple calls"

    def test_system_prompt_content_structure(self):
        """Test that the system prompt has expected structure."""
        from codegen.cli.mcp.resources.system_prompt import SYSTEM_PROMPT

        # Should be a non-empty string
        assert isinstance(SYSTEM_PROMPT, str)
        assert len(SYSTEM_PROMPT) > 100  # Should be substantial

        # Should contain key information about Codegen
        assert "codegen" in SYSTEM_PROMPT.lower()

    def test_setup_instructions_content_structure(self):
        """Test that setup instructions have expected structure."""
        from codegen.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS

        # Should be a non-empty string
        assert isinstance(SETUP_INSTRUCTIONS, str)
        assert len(SETUP_INSTRUCTIONS) > 50  # Should be substantial

        # Should contain setup-related keywords
        setup_keywords = ["install", "setup", "configure", "environment", "python", "pip", "uv"]
        assert any(keyword in SETUP_INSTRUCTIONS.lower() for keyword in setup_keywords)

    @patch("codegen.cli.mcp.server.mcp")
    def test_resource_registration_process(self, mock_mcp):
        """Test that resources are properly registered with the MCP server."""
        # Import the server module to trigger resource registration

        # Check that the resource decorator was called
        assert mock_mcp.resource.called, "MCP resource decorator should have been called"

        # Check that it was called the expected number of times
        expected_resource_count = 3  # agent_prompt, setup_instructions, manifest
        assert mock_mcp.resource.call_count >= expected_resource_count

    def test_resource_error_handling(self):
        """Test resource error handling."""
        from codegen.cli.mcp.server import mcp

        # All current resources should not raise exceptions
        resources = mcp._resource_manager._resources
        for uri, resource in resources.items():
            try:
                result = resource.fn()
                # Basic validation that result is not empty
                if isinstance(result, str):
                    assert len(result) > 0
                elif isinstance(result, dict):
                    assert len(result) > 0
                else:
                    pytest.fail(f"Resource {uri} returned unexpected type: {type(result)}")
            except Exception as e:
                pytest.fail(f"Resource {uri} should not raise exceptions, but raised: {e}")

    def test_json_serializable_manifest(self):
        """Test that the manifest resource returns JSON-serializable data."""
        from codegen.cli.mcp.server import mcp

        # Get the manifest resource
        manifest_resources = mcp._resource_manager._resources
        assert "system://manifest" in manifest_resources

        manifest_resource = manifest_resources["system://manifest"]
        result = manifest_resource.fn()

        # Should be JSON serializable
        try:
            json_str = json.dumps(result)
            # Should be able to parse it back
            parsed = json.loads(json_str)
            assert parsed == result
        except (TypeError, ValueError) as e:
            pytest.fail(f"Manifest resource result is not JSON serializable: {e}")
