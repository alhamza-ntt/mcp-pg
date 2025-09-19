

from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient, SearchIndexingBufferedSender
from config import  COGNITIVE_SEARCH_CONFIG, ADA_CONFIG
from openai import AzureOpenAI

def get_embedding(input_string):
   
    openai_client = AzureOpenAI(
        api_key=ADA_CONFIG["api_key"],
        api_version=ADA_CONFIG["api_version"],
        azure_endpoint=ADA_CONFIG["api_base"],
        azure_deployment=ADA_CONFIG["deployment_name"],
    )
    response = openai_client.embeddings.create(
        input=input_string,
        model=ADA_CONFIG["model"],
    )
    results = response.data[0].embedding
    openai_client.close()
    return results

def search_in_index(query, top_k_contexts=5):
    """
    Performs hybrid retrieval in Azure Cognitive Search.

    Args:
        query (str): The search query string.
        top_k_contexts (int): The number of top results to retrieve (default is 5).

    Returns:
        List[dict]: A list of search results with content, title, and reranker scores.
    """
    search_client = SearchClient(
        endpoint=COGNITIVE_SEARCH_CONFIG["endpoint"],
        index_name=COGNITIVE_SEARCH_CONFIG["index_name"],
        credential=AzureKeyCredential(COGNITIVE_SEARCH_CONFIG["api_key"])
    )

    # Generate embedding for the query
    vector = VectorizedQuery(
        vector=get_embedding(query),  # Get embedding for query
        k_nearest_neighbors=top_k_contexts,
        fields="contentVector",
        exhaustive=True
    )

    # Perform hybrid search 
    results = search_client.search(
        search_text=query,  # BM25 keyword search
        search_fields= ["content","metadata/filetype","metadata/filename"],
        vector_queries=[vector],  # Vector search
        query_type="semantic",  # Enable semantic reranking
        semantic_configuration_name="default",  # Use default semantic config
        #select=["chunk_id", "content","metadata/filename" ,"metadata/has_image"],  # Only retrieve fields explicitly allowed #metadata
        top=top_k_contexts
    )

    # Extract relevant data from results
    contexts = []
    for result in results:
        contexts.append({
            "chunk_id": result["chunk_id"],
            "content": result['content'],
            "filename": result['metadata']['filename'], 
            "search_score": result["@search.score"],
            "has_image": result['metadata']['has_image'],
        })

    search_client.close()

    return contexts



if __name__ == "__main__":
    print(search_in_index("What is on step 5" , top_k_contexts=1))





