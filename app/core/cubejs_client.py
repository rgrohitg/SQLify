#cubejs_client.py
import requests
import os
from app.utils.logger import logger

CUBEJS_API_URL = os.getenv("CUBEJS_API_URL")
CUBEJS_API_TOKEN = os.getenv("CUBEJS_API_TOKEN")


def load_cube_models_and_views():
    headers = {
        "Content-Type": "application/json",
        "Authorization": CUBEJS_API_TOKEN
    }
    try:
        response = requests.get(f"{CUBEJS_API_URL}/meta", headers=headers)
        response.raise_for_status()

        cubejs_meta = response.json()
        models = {}
        views = {}
        #TODO Just load VIEWS dont load CUBES
        for cube in cubejs_meta['cubes']:
            cube_name = cube['name']
            details = {
                "measures": [{"name": measure['name'], "type": measure['type']} for measure in cube['measures']],
                "dimensions": [{"name": dimension['name'], "type": dimension['type']} for dimension in
                               cube['dimensions']],
                "timeDimensions": [dimension['name'] for dimension in cube['dimensions'] if dimension['type'] == 'time']
            }
            if cube_name.endswith("_view"):
                views[cube_name] = details
            else:
                models[cube_name] = details

        logger.info("Cube.js models and views loaded successfully.")
        return models, views
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to load Cube.js models and views: {str(e)}")
        return None, None

def get_sql_from_cubejs(query):
    headers = {
        "Content-Type": "application/json",
        "Authorization": CUBEJS_API_TOKEN
    }
    response = requests.post(f"{CUBEJS_API_URL}/sql", json={"query": query}, headers=headers)
    if response.status_code == 200:
        sql_response = response.json()
        sql_query = sql_response.get('sql', {}).get('sql', [])[0]
        if sql_query:
            return sql_query.replace("\n", " ").strip()
        else:
            return None
    else:
        return None


def get_data_from_cubejs(query):
    headers = {
        "Content-Type": "application/json",
        "Authorization": CUBEJS_API_TOKEN
    }

    try:
        response = requests.post(f"{CUBEJS_API_URL}/load", json={"query": query}, headers=headers)

        # Return status code and response message
        if response.status_code == 200:
            data = response.json()
            return response.status_code, data if data else "No data returned from Cube.js."

        # Handle specific Cube.js API errors
        elif response.status_code == 400:
            return response.status_code, "Bad request. The query format might be incorrect."
        elif response.status_code == 422:
            return response.status_code, "Invalid dimensions or measures."

        # Generic error message for other non-200 responses
        return response.status_code, f"Cube.js API returned status code {response.status_code}."

    except requests.exceptions.RequestException as e:
        # Handle network-related errors or request failures
        return None, f"An error occurred while connecting to Cube.js API. Error: {str(e)}"

    except Exception as e:
        # Handle any other unexpected errors
        return None, f"An unexpected error occurred. Error: {str(e)}"