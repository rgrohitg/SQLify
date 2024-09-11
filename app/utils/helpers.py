import json
import os
import uuid
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_openai import OpenAI
from app.vector_store.store_manager import add_query_to_vector_store, search_similar_queries, filter_complex_metadata

from app.utils.logger import logger

llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0)

def generate_cube_query(query: str, cube_models: dict, cube_views: dict) -> tuple:
    logger.info(f"Generating Cube.js query for user query: {query}")

    # Search for similar queries in the vector store
    previous_responses = search_similar_queries(query, k=15)
    logger.info("Previous Response: %s ", previous_responses)

    # Collect previous responses for inclusion in the prompt
    previous_responses_text = ""
    if previous_responses:
        for resp in previous_responses:
            response_metadata = resp.get('metadata', {})
            feedback = response_metadata.get('feedback', None)
            rating = feedback.get('rating') if feedback else None
            data = response_metadata.get('data', None)
            cubejs_query = response_metadata.get('cubejs_query', None)
            status = response_metadata.get('status', 'unknown')  # Add status retrieval

            # Format the previous response data
            if data:
                formatted_data = format_data_with_openai(query, data)
                previous_responses_text += (
                    f"\nPrevious Query: {resp.get('query')}\n"
                    f"Status: {status}\n"
                    f"Rating: {rating}\n"
                    f"Cube.js Query: {cubejs_query}\n"
                    f"Data: {formatted_data}\n"
                )
            else:
                previous_responses_text += (
                    f"\nPrevious Query: {resp.get('query')}\n"
                    f"Status: {status}\n"
                    f"Rating: {rating}\n"
                    f"Cube.js Query: {cubejs_query}\n"
                    f"Data: No data available\n"
                )

    # Prepare the Cube.js query generation prompt
    prompt = PromptTemplate(
        input_variables=["cube_views", "previous_responses", "query"],
        template="""
            You are an expert in generating Cube.js queries. Based on the following Cube.js views:

            Views:
            {cube_views}
            
            Previous Responses:
            {previous_responses}
            
            Instructions:
            - Ensure that all measures and dimensions used in the query match those defined in the models and views.
            - Use the correct cube name for the dimensions and measures (e.g., 'ecom_view.orderCount' or 'customers_view.orderStatus').
            - Always include the 'order' key in the query, if the query involves any measure that can be sorted (e.g., orderCount, totalOrderAmount).
            - Based on the query context, select the most relevant view from the provided views.
            - If the query involves orders or users, use a view related to 'orders', 'users', or 'ecommerce'.
            - If the query involves products or inventory, use views related to 'products', 'inventory', or 'catalog'.
            - Prioritize selecting views based on the field names and dimensions related to the query, such as 'orderCount', 'userId', 'productName', etc.
            - Avoid including empty filters unless the query explicitly requires them. Ensure that any filters applied match the fields available in the views.
            - If a dimension has possible values or synonyms, always use the closest match from the list of possible values when constructing the query. If user input doesn't exactly match any value, select the closest possible match from the list. Do not introduce any non-listed values.
            - For example, if the user requests 'Camera' and the `productCategory` dimension has possible values ['Cameras', 'Smartphones'], use 'Cameras' as the filter value.
            - Use the following format for filters:
              {{
                  "filters": [
                      {{
                          "member": "<Dimension_Name>",
                          "operator": "<Comparison_Operator>",
                          "values": ["<Value_List>"]
                      }}
                  ]
              }}
              Example:
              {{
                  "filters": [
                      {{
                          "member": "customers_view.orderStatus",
                          "operator": "equals",
                          "values": ["completed"]
                      }}
                  ]
              }}
            
            - If the query involves time-based measures or dimensions, include 'timeDimensions' in the query and use only one time dimension value (e.g., 'ecom_view.orderCreatedAt').
            - Consider the relationships and joins between different cubes and views when constructing the query. Include joins if necessary.
            - Use appropriate aggregations (sum, count, average, etc.) as dictated by the query, and validate that they are supported for the selected measures.
            - Include 'limit' and 'offset' for pagination if the query is expected to return multiple results.
            - Ensure that the generated query is syntactically correct according to Cube.js's query format.
            - Always use dimension names as defined in the views when generating the query.
            
            Example Query:
            - Natural language request: "How many users have placed orders?"
              Correct Cube.js Query: {{
                  "order": {{
                      "customers_view.orderCount": "desc"
                  }},
                  "measures": ["customers_view.orderCount"],
                  "dimensions": ["customers_view.user_id"],
                  "timeDimensions": [],
                  "filters": [
                      {{
                          "member": "customers_view.orderStatus",
                          "operator": "equals",
                          "values": ["completed"]
                      }}
                  ],
                  "limit": 100
              }}
            
            Generate a Cube.js query for the following natural language request:
            '{query}'
            """
    )

    # Generate the prompt and process the response
    sequence = prompt | llm
    inputs = {
        "query": query,
        "cube_views": json.dumps(cube_views, indent=4),
        "previous_responses": previous_responses_text
    }

    logger.info(f"Generated prompt inputs: {inputs}")
    response = sequence.invoke(inputs)
    logger.info(f"Raw response from OpenAI: {response}")

    try:
        cubejs_query = json.loads(response)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}. Response was: {response}")
        return None, None

    # Remove empty filters
    if "filters" in cubejs_query and not cubejs_query["filters"]:
        del cubejs_query["filters"]

    # Ensure an order field exists
    if "order" not in cubejs_query:
        cubejs_query["order"] = {"Orders.orderCount": "desc"}

    logger.info(f"Generated Cube.js query: {cubejs_query}")

    # Serialize the Cube.js query
    serialized_query = json.dumps(cubejs_query)
    if serialized_query is None:
        logger.error("Failed to serialize cubejs_query")
        return None, None

    # Store the query and its metadata in the vector store
    request_id = str(uuid.uuid4())
    metadata = {
        "response": serialized_query,  # Store the serialized Cube.js query
        "request_id": request_id,
        "success": True,
        "feedback": None,
        "cubejs_query": serialized_query  # Store the Cube.js query
    }

    # Add the query and its response to the vector store
    add_query_to_vector_store(query, serialized_query, metadata)

    return cubejs_query, request_id

def chunk_data(data, chunk_size=10):
    # Split the data into smaller chunks
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def format_data_with_openai(user_query: str, cubejs_data: dict) -> str:
    try:
        # Extract relevant data from the Cube.js response
        if 'data' in cubejs_data and cubejs_data['data']:
            data_points = cubejs_data['data']
            formatted_data_points = [f"{key}: {value}" for item in data_points for key, value in item.items()]
            formatted_data = "\n".join(formatted_data_points)
        else:
            formatted_data = "No data available"

        # Prepare the prompt for OpenAI
        prompt = PromptTemplate(
            input_variables=["user_query", "data"],
            template="""
            You are an expert in providing concise and relevant responses based on data. Here is the user's query and the data obtained from Cube.js:
            
            User Query: "{user_query}"
            
            Data:
            {data}
            
            Instructions:
            - Format the response based strictly on the data provided. Do not generate additional details or fabricate information.
            - If the data contains only counts or numerical values (e.g., product count), do not create a list of products.
            - For lists of items or categories, use bullet points or numbered lists only if the data explicitly includes these details.
            - If only summary information (e.g., product count) is available, state this clearly in the response.
            - For tabular data, use a markdown table and ensure all rows are included exactly as they appear in the data.
            - If there is insufficient data to answer the query fully, clearly state what is missing.
            - Ensure the response is easy to understand, concise, and addresses the user's query completely.
            
            
            Response:
            """
        )

        # Generate the formatted response
        sequence = prompt | llm
        inputs = {
            "user_query": user_query,
            "data": formatted_data
        }

        logger.info(f"Generated prompt inputs: {inputs}")
        response = sequence.invoke(inputs)
        logger.info(f"Raw response from OpenAI: {response}")

        formatted_response = response.strip()
        return formatted_response

    except Exception as e:
        logger.error(f"Error formatting data with OpenAI: {str(e)}")
        return "Error formatting response. Please try again later."
