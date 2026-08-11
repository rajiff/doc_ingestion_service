from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

def test_collection_exists_exception():
    """Test if the collection in vector store exists or not"""
    # Initialize client
    client = QdrantClient(url="http://localhost:6333")

    collection_name = "non_existent_collection"

    try:
        # Attempting to fetch a missing collection triggers an UnexpectedResponse
        collection_info = client.get_collection(collection_name=collection_name)
        print("Collection exists!")

    except UnexpectedResponse as e:
        # Check if the exception represents a 404 Not Found error
        if e.status_code == 404:
            print(f"Exception Caught: Collection '{collection_name}' does not exist.")
        else:
            # Handle other API/HTTP errors (e.g., 400 Bad Request, 500 Server Error)
            print(f"An unexpected API error occurred: {e}")

if __name__ == "__main__":
    test_collection_exists_exception()
