# Test data
SAMPLE_TOML = """
[secrets]
github_token = "gh_token123"
openai_api_key = "sk-123456"

[repository]
full_name = "test-org/test-repo"
repo_name = "test-repo"

[feature_flags.codebase]
debug = true
verify_graph = true
track_graph = false
method_usages = true
sync_enabled = true
full_range_index = false
ignore_process_errors = true
disable_graph = false
generics = true

[feature_flags.codebase.typescript]
ts_dependency_manager = true
ts_language_engine = false
v8_ts_engine = true

[feature_flags.codebase.import_resolution_overrides]
"@org/pkg" = "./local/path"
"""

SAMPLE_CONFIG_DICT = {
    "secrets": {
        "github_token": "gh_token123",
        "openai_api_key": "sk-123456",
    },
    "repository": {
        "organization_name": "test-org",
        "repo_name": "test-repo",
    },
    "feature_flags": {
        "codebase": {
            "debug": True,
            "verify_graph": True,
            "track_graph": False,
            "method_usages": True,
            "sync_enabled": True,
            "full_range_index": False,
            "ignore_process_errors": True,
            "disable_graph": False,
            "generics": True,
            "typescript": {
                "ts_dependency_manager": True,
                "ts_language_engine": False,
                "v8_ts_engine": True,
            },
            "import_resolution_overrides": {"@org/pkg": "./local/path"},
        }
    },
}
