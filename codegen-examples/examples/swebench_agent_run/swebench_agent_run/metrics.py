import json
import os
from importlib.metadata import version
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


def write_report_to_db(report_file: str):
    path = Path(__file__).parent.parent / ".env.db"
    if not path.exists():
        raise FileNotFoundError(f"DB credentials not found: {path}")
    load_dotenv(str(path.resolve()))

    postgres_host = os.getenv("POSTGRESQL_HOST")
    postgres_database = os.getenv("POSTGRESQL_DATABASE")
    postgres_user = os.getenv("POSTGRESQL_USER")
    postgres_password = os.getenv("POSTGRESQL_PASSWORD")
    postgres_port = os.getenv("POSTGRESQL_PORT")

    try:
        codegen_version = version("codegen")
    except Exception:
        codegen_version = "dev"

    with open(report_file) as f:
        report = json.load(f)

    # Establish connection

    conn = psycopg2.connect(
        host=postgres_host,
        database=postgres_database,
        user=postgres_user,
        password=postgres_password,
        port=postgres_port,
    )

    # Create a cursor
    cur = conn.cursor()

    try:
        # Single row insert
        cur.execute(
            "INSERT INTO swebench_output (codegen_version, submitted, completed_instances, resolved_instances, unresolved_instances, empty_patches, error_instances) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                codegen_version,
                report["submitted_instances"],
                report["completed_instances"],
                report["resolved_instances"],
                report["unresolved_instances"],
                report["empty_patch_instances"],
                report["error_instances"],
            ),
        )

        # Commit the transaction
        conn.commit()

    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error: {e}")

    finally:
        # Close cursor and connection
        cur.close()
        conn.close()
