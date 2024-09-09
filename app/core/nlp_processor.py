# nlp_processor.py

from app.core.cubejs_client import load_cube_models_and_views, get_sql_from_cubejs, get_data_from_cubejs
from app.utils.helpers import generate_cube_query, format_data_with_openai
from app.utils.logger import logger
from app.vector_store.store_manager import search_similar_queries, add_query_to_vector_store
from datetime import datetime
import json
def process_nlp_query(user_query: str) -> tuple:
    cube_models, cube_views = load_cube_models_and_views()
    if not cube_models or not cube_views:
        raise ValueError("Could not load Cube.js models or views")

    # **Step 1: Retrieval - Search for similar queries in the vector store**
    similar_queries = search_similar_queries(user_query, k=5)
    previous_queries_info = []

    # Collect similar queries, feedback, and ratings
    if similar_queries:
        for similar_query in similar_queries:
            # Ensure that similar_query is a dictionary and has expected keys
            response_metadata = similar_query.get('metadata', {})
            feedback = response_metadata.get('feedback', None)
            rating = feedback.get('rating') if feedback else None
            cubejs_query = response_metadata.get('cubejs_query', None)
            data = response_metadata.get('data', None)
            error_message = response_metadata.get('error_message', None)

            previous_queries_info.append({
                'query': similar_query.get('query', None),
                'rating': rating,
                'feedback': feedback,
                'cubejs_query': cubejs_query,
                'data': data,
                'error_message': error_message
            })

    # **Step 2: Augmentation - Enhance the user query if relevant previous queries are found**
    augmented_query = augment_user_query(user_query, previous_queries_info)

    # **Step 3: Generation - Generate a new Cube.js query based on the augmented query**
    cubejs_query, request_id = generate_cube_query(augmented_query, cube_models, cube_views)
    logger.info("Generated request ID: %s", request_id)

    if cubejs_query:
        # **Step 4: Get data from Cube.js using the generated query**
        status_code, data = get_data_from_cubejs(cubejs_query)
        logger.info("Data from Cube load API : %s", data)

        # Extract the relevant data from the response
        if status_code == 200 and data and 'data' in data:
            extracted_data = data['data']
            # Format the extracted data as a string
            formatted_data = format_data_with_openai(user_query, data)  # Convert list of dicts to a JSON string
            status = "pass"
            error_message = None
        else:
            extracted_data = None
            formatted_data = "No data available"
            status = "fail"
            error_message = data if status_code else "Unable to generate data from Cube.js query."

        # Store both the Cube.js query and the data in the vector store with enhanced metadata
        add_query_to_vector_store(
            user_query,
            cubejs_query,
            metadata={
                "status": status,                # 'pass' or 'fail'
                "error_message": error_message,  # Error message if failed
                "cubejs_query": cubejs_query,    # Cube.js query
                "data": extracted_data,          # Actual data or None if failure
                "feedback": None,                # Initial feedback is None
                "similar_queries_info": previous_queries_info,  # Include info on similar queries
                "request_id": request_id,        # Unique request ID
                "timestamp": str(datetime.utcnow()),  # Timestamp of when the query was processed
            }
        )

        # Return the formatted data and request ID
        return formatted_data, request_id

    else:
        error_message = "Unable to generate Cube.js query."
        add_query_to_vector_store(
            user_query,
            cubejs_query,
            metadata={
                "status": "fail",                # Status: fail
                "error_message": error_message,  # Error message if query generation fails
                "cubejs_query": None,            # No valid Cube.js query
                "data": None,                    # No data
                "feedback": None,                # Initial feedback is None
                "similar_queries_info": previous_queries_info,  # Include info on similar queries
                "request_id": request_id,        # Unique request ID
                "timestamp": str(datetime.utcnow()),  # Timestamp
            }
        )
        # Return the error message and request ID
        return error_message, request_id



def augment_user_query(user_query: str, previous_queries_info: list) -> str:
    """
    Modify or enhance the user query based on previous similar queries and their feedback.
    For example, if a highly rated previous query is found, it can be used to refine the current query.
    """
    if previous_queries_info:
        # If previous queries with good feedback exist, use them to augment the current query.
        # This is a simple example, you can modify the logic to fit your use case.
        top_query_info = max(previous_queries_info, key=lambda x: x['rating'] if x['rating'] else 0)
        if top_query_info['rating'] and top_query_info['rating'] >= 4:
            augmented_query = f"{user_query} (Consider previous feedback: {top_query_info['query']})"
            logger.info(f"Augmented user query: {augmented_query}")
            return augmented_query

    return user_query  # If no relevant queries found, return the original query unchanged.