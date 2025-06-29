"""Example usage of the enhanced Codegen SDK.

This example demonstrates how to use the new SDK components:
- CodegenSDK: Unified entry point for all API functionality
- Organizations: Managing organizations
- Users: Managing users within organizations
- Enhanced Agent: Improved agent functionality with better error handling
"""

import os

from codegen.agents import Agent, CodegenSDK, Organizations, Users


# Example 1: Using the unified SDK
def example_unified_sdk():
    """Example using the unified CodegenSDK."""
    print("=== Unified SDK Example ===")

    # Initialize the SDK with your API token
    sdk = CodegenSDK(token=os.getenv("CODEGEN_API_TOKEN"))

    # Use agents
    print("Running an agent task...")
    task = sdk.agents.run("Analyze the codebase and suggest improvements")
    print(f"Task created: {task.id}")
    print(f"Status: {task.status}")
    print(f"Web URL: {task.web_url}")

    # List organizations
    print("\nListing organizations...")
    orgs = sdk.organizations.list()
    for org in orgs:
        print(f"- {org.name} (ID: {org.id})")

    # Get users in the first organization
    if orgs:
        print(f"\nListing users in organization '{orgs[0].name}'...")
        users = sdk.users(org_id=orgs[0].id).list()
        for user in users:
            print(f"- {user.github_username} ({user.email})")


# Example 2: Using individual SDK components
def example_individual_components():
    """Example using individual SDK components."""
    print("\n=== Individual Components Example ===")

    token = os.getenv("CODEGEN_API_TOKEN")

    # Enhanced Agent with better error handling
    print("Using enhanced Agent...")
    agent = Agent(token=token)

    try:
        task = agent.run("Create a simple Python function")
        print(f"Agent task: {task.id}")

        # Check task status with new helper methods
        if task.is_running():
            print("Task is currently running...")
        elif task.is_completed():
            print("Task completed!")
            if task.is_successful():
                print("Task was successful!")
            elif task.is_failed():
                print("Task failed.")

        # Get task by ID
        retrieved_task = agent.get_task(task.id)
        print(f"Retrieved task: {retrieved_task.id}")

    except Exception as e:
        print(f"Error: {e}")

    # Organizations management
    print("\nUsing Organizations...")
    orgs_client = Organizations(token=token)

    try:
        # List with pagination
        page_result = orgs_client.get_page(page=1, page_size=10)
        print(f"Organizations page: {page_result['page']}/{page_result['pages']}")
        print(f"Total organizations: {page_result['total']}")

        # Iterate through all organizations
        print("All organizations:")
        for org in orgs_client.list_all():
            print(f"- {org.name} (ID: {org.id})")
            print(f"  Settings: {org.settings}")

    except Exception as e:
        print(f"Error: {e}")

    # Users management
    print("\nUsing Users...")
    if orgs:
        users_client = Users(token=token, org_id=orgs[0].id)

        try:
            # List users with pagination
            page_result = users_client.get_page(page=1, page_size=5)
            print(f"Users page: {page_result['page']}/{page_result['pages']}")
            print(f"Total users: {page_result['total']}")

            # Find specific users
            user = users_client.find_by_github_username("example-user")
            if user:
                print(f"Found user: {user.github_username}")

            # Get user by ID
            if page_result["items"]:
                first_user = page_result["items"][0]
                retrieved_user = users_client.get(first_user.id)
                print(f"Retrieved user: {retrieved_user.github_username}")

        except Exception as e:
            print(f"Error: {e}")


# Example 3: Error handling
def example_error_handling():
    """Example demonstrating error handling."""
    print("\n=== Error Handling Example ===")

    from codegen.exceptions import AuthenticationError, CodegenError, NotFoundError

    # Invalid token example
    try:
        sdk = CodegenSDK(token="invalid-token")
        orgs = sdk.organizations.list()
    except AuthenticationError as e:
        print(f"Authentication failed: {e.message}")
        print(f"Status code: {e.status_code}")
    except CodegenError as e:
        print(f"API error: {e.message}")

    # Not found example
    try:
        sdk = CodegenSDK(token=os.getenv("CODEGEN_API_TOKEN"))
        user = sdk.users().get(user_id=99999)  # Non-existent user
    except NotFoundError as e:
        print(f"User not found: {e.message}")
    except CodegenError as e:
        print(f"API error: {e.message}")


if __name__ == "__main__":
    # Make sure to set your API token
    if not os.getenv("CODEGEN_API_TOKEN"):
        print("Please set the CODEGEN_API_TOKEN environment variable")
        exit(1)

    example_unified_sdk()
    example_individual_components()
    example_error_handling()
