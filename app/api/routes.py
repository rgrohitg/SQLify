#routes.py
from fastapi import APIRouter, HTTPException
from app.models.schemas import FeedbackRequest, NLPQueryRequest, NLPQueryResponse
from app.core.nlp_processor import process_nlp_query
from app.utils.logger import logger
from app.vector_store.store_manager import add_query_to_vector_store, search_similar_queries

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Handle feedback submission for a particular query.
    """
    try:
        # Retrieve the query result by request ID
        results = search_similar_queries(feedback.request_id, k=1)
        if not results:
            logger.warning(f"Feedback submission failed: Request ID {feedback.request_id} not found.")
            raise HTTPException(status_code=404, detail="Request ID not found")

        result = results[0]
        updated_metadata = result.get('metadata', {})
        logger.info(f"Current metadata for Request ID {feedback.request_id}: {updated_metadata}")

        # Update the feedback in the metadata
        updated_metadata['feedback'] = {"rating": feedback.rating, "message": feedback.message}

        # Update the vector store with the new metadata
        add_query_to_vector_store(feedback.request_id, result['response'], updated_metadata)

        logger.info(f"Feedback updated successfully for Request ID {feedback.request_id}")
        return {"status": "success", "message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Error submitting feedback")


@router.post("/ask", response_model=NLPQueryResponse)
async def nlp_to_sql(request: NLPQueryRequest):
    """
    Handle the natural language query and process it into a Cube.js query or SQL.
    """
    try:
        logger.info(f"Processing NLP query: {request.query}")

        # Process the query and generate the corresponding SQL or Cube.js query
        formatted_data, request_id = process_nlp_query(request.query)

        logger.info(f"NLP query processed successfully: {request.query}")
        return NLPQueryResponse(query=request.query, formatted_data=formatted_data, request_id=request_id)
    except ValueError as ve:
        # Catch more specific errors like query generation issues
        logger.warning(f"ValueError encountered while processing NLP query: {str(ve)}")
        raise HTTPException(status_code=400, detail=f"Query error: {str(ve)}")
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Error processing NLP query: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")

#
#
# # Fetch all queries
# @router.get("/fetch_all")
# async def fetch_all():
#     queries = fetch_all_queries()
#     if queries:
#         return {"data": queries}
#     else:
#         return {"message": "No queries found."}
#
# # Delete a specific query by ID
# @router.delete("/delete_query/{request_id}")
# async def delete_query(request_id: str):
#     try:
#         delete_query_from_vector_store(request_id)
#         return {"message": f"Query with request ID {request_id} deleted successfully."}
#     except Exception as e:
#         return {"error": str(e)}
#
# # Delete all queries
# @router.delete("/delete_all")
# async def delete_all():
#     try:
#         delete_all_queries()
#         return {"message": "All queries deleted successfully."}
#     except Exception as e:
#         return {"error": str(e)}
#
#
#
