import subprocess
import json
import logging

logger = logging.getLogger(__name__)

def team_db_execute(sql: str):
    """
    Executes a SQL statement via the team-db CLI.
    Returns the JSON output as a list of dicts.
    """
    try:
        # One SQL statement per call, passed as a single argument
        result = subprocess.run(["team-db", sql], capture_output=True, text=True, check=True)
        if result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except subprocess.CalledProcessError as e:
        logger.error(f"team-db error: {e.stderr}")
        raise Exception(f"Database error: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {result.stdout}")
        return []

def init_db():
    # Tables are already created in the previous step
    pass

def get_db():
    # This is a dummy for FastAPI dependency injection if needed
    # but we'll use team_db_execute directly in CRUD
    yield None
