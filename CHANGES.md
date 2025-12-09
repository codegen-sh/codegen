# Changes

This PR adds support for handling repositories that don't support draft PRs. When attempting to create a draft PR in a repository that doesn't support this feature, the code will now gracefully fall back to creating a regular PR instead of failing.

## Implementation Details

1. Modified the `create_pull` method in the `GitRepoClient` class to:
   - First attempt to create a draft PR when requested
   - Catch GitHub exceptions with status code 422 that mention "draft" in the error message
   - Fall back to creating a regular PR when draft PRs aren't supported
   - Log appropriate warning messages

This change ensures that the PR creation process is more robust and works across all GitHub repositories, including older GitHub Enterprise Server instances that may not support draft PRs.
