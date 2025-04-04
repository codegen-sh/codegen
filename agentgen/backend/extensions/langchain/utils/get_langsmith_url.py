import datetime
from typing import Optional

from langsmith import Client


def get_langsmith_url(client: Client, run_id: str, project_name: Optional[str] = None) -> str:
    """Get the URL for a run in LangSmith.

    Args:
        client: The LangSmith client
        run_id: The ID of the run
        project_name: Optional name of the project

    Returns:
        The URL for the run in LangSmith
    """
    # Construct the URL directly using the host URL and run ID
    # This avoids the issue with the client's get_run_url method expecting a run object
    host_url = client._host_url
    tenant_id = client._get_tenant_id()

    try:
        # Get the project ID from the project name
        if project_name is not None:
            project_id = client.read_project(project_name=project_name).id
            # Construct the URL
            return f"{host_url}/o/{tenant_id}/projects/p/{project_id}/r/{run_id}?poll=true"
        else:
            # If project_name is not provided, construct a URL without it
            return f"{host_url}/o/{tenant_id}/r/{run_id}?poll=true"
    except Exception as e:
        # If we can't get the project ID, construct a URL without it
        print(f"Could not get project ID for {project_name}: {e}")
        return f"{host_url}/o/{tenant_id}/r/{run_id}?poll=true"


def find_and_print_langsmith_run_url(client: Client, project_name: Optional[str] = None) -> Optional[str]:
    """Find the most recent LangSmith run and print its URL.

    Args:
        client: The LangSmith client
        project_name: Optional name of the project

    Returns:
        The URL for the run in LangSmith if found, None otherwise
    """
    separator = "=" * 60

    try:
        # Get the most recent runs with proper filter parameters
        # We need to provide at least one filter parameter as required by the API
        recent_runs = list(
            client.list_runs(
                # Use the project name from environment variable
                project_name=project_name,
                # Limit to just the most recent run
                limit=1,
            )
        )

        if recent_runs and len(recent_runs) > 0:
            # Make sure we have a valid run object with an id attribute
            if hasattr(recent_runs[0], "id"):
                # Convert the ID to string to ensure it's in the right format
                run_id = str(recent_runs[0].id)

                # Get the run URL using the run_id parameter
                run_url = get_langsmith_url(client, run_id=run_id, project_name=project_name)

                print(f"\n{separator}\n🔍 LangSmith Run URL: {run_url}\n{separator}")
                return run_url
            else:
                print(f"\n{separator}\nRun object has no 'id' attribute: {recent_runs[0]}\n{separator}")
                return None
        else:
            # If no runs found with project name, try a more general approach
            # Use a timestamp filter to get recent runs (last 10 minutes)
            ten_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=10)

            recent_runs = list(client.list_runs(start_time=ten_minutes_ago.isoformat(), limit=1))

            if recent_runs and len(recent_runs) > 0 and hasattr(recent_runs[0], "id"):
                # Convert the ID to string to ensure it's in the right format
                run_id = str(recent_runs[0].id)

                # Get the run URL using the run_id parameter
                run_url = get_langsmith_url(client, run_id=run_id, project_name=project_name)

                print(f"\n{separator}\n🔍 LangSmith Run URL: {run_url}\n{separator}")
                return run_url
            else:
                print(f"\n{separator}\nNo valid runs found\n{separator}")
                return None
    except Exception as e:
        print(f"\n{separator}\nCould not retrieve LangSmith URL: {e}")
        import traceback

        print(traceback.format_exc())
        print(separator)
        return None
