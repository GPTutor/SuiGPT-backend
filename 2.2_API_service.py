import ssl
from elasticsearch import Elasticsearch

from dotenv import dotenv_values

config = dotenv_values(".env")

# Elasticsearch Config
es = Elasticsearch(
    ["https://localhost:9200"],
    http_auth=("elastic", config["ELASTIC_PASSWORD"]),
    verify_certs=True,
    ca_certs="http_ca.crt",
)

# Check Connection
if not es.ping():
    raise ValueError("Fail to connect to Elasticsearch")
else:
    print("Connect to Elasticsearch Success")


from fastapi import FastAPI, HTTPException, Response, status, Body
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch

# Initialize FastAPI app
PROJECT_NAME = "SuiGPT Backend to get relevant_codes"
PROJECT_VERSION = "0.0.1"
app = FastAPI(docs_url=None, title=PROJECT_NAME, version=PROJECT_VERSION)

# Enable CORS (Cross-Origin Resource Sharing)
origins = ["*"]  # You can restrict origins as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi


@app.get("/api/docs", include_in_schema=False)
async def get_documentation():
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="docs")


@app.get("/api/openapi.json", include_in_schema=False)
async def openapi():
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


@app.get("/api/search")
async def get_relevant_codes_by_query(
    query: str = "A fungible coin name and symbol is Eason that I can manage to airdrop by a list of whitelists",
):
    # Define the Elasticsearch query
    query = {
        "query": {
            "more_like_this": {
                "fields": ["code_summary", "code_title"],
                "like": query,
                "min_term_freq": 1,
                "max_query_terms": 12,
            }
        }
    }

    # Execute the MLT query
    index_name = "sui_gpt"  # Replace with your Elasticsearch index name
    results = es.search(index=index_name, body=query)

    # Create a dictionary to store the extracted fields
    result_dict = {}

    # Iterate through each document in the Elasticsearch results
    for doc in results["hits"]["hits"]:
        # Extract the 'code_title' field
        title = doc["_source"]["code_title"]

        # Extract other fields
        source_move = doc["_source"]["source_move"]
        annotated_move = doc["_source"]["annotated_move"]
        annotated_commented_move = doc["_source"]["annotated_commented_move"]
        code_summary = doc["_source"]["code_summary"]

        # Store the extracted field values in a dictionary
        result_dict[title] = {
            "source_move": source_move,
            "annotated_move": annotated_move,
            "annotated_commented_move": annotated_commented_move,
            "code_summary": code_summary,
            "code_title": title,
        }

    # Take the top 3 items
    top_3_results = dict(list(result_dict.items())[:3])

    output = {
        "match_titles": list(result_dict.keys()),
        "top3_match_titles": list(top_3_results.keys()),
        "top3_match": top_3_results,
    }
    return output


class QueryModel(BaseModel):
    query: str = "A fungible coin name and symbol is Eason that I can manage to airdrop by a list of whitelists"
        

@app.post("/api/get_prompt_by_query")
async def get_prompt_by_query(body: QueryModel):
    # Extract the query from the request body
    query = body.query

    # Call the function to get relevant codes
    result = await get_relevant_codes_by_query(query=query)

    # Construct the relevant code in prompt
    relevant_code_in_prompt = ""
    for title, fields in result["top3_match"].items():
        relevant_code_in_prompt += (
            f"{title}\n```move{fields['annotated_commented_move']}```\n\n"
        )

    # Construct the output prompt
    output_prompt = [
        {
            "role": "system",
            "content": f"You are a helpful assistant that generate the move code according to user's instruction and the context. Your output code should be surrounded with triple backquote (```) and new line. Please make very very sure to generate code snippets in the correct move format (which is similar to Rust), but note that move module import (use) inside the module instead of at top of the file. You don't need to interact with user, ask further information, or explain anything. Just generate code directly (But you can add comments in the code). Below are some relevant Move Smart contract code that you can refer to. You may synthesis codes from these contracts to produce the code that user wants.\n\n{relevant_code_in_prompt}\n\nYou should follow the syntax and parameter arrangement of each function. You should not finish earlier, please output code completely after the correct closing {'}'}",
        },
        {"role": "user", "content": f"Instruction: {query}"},
    ]

    return output_prompt


if __name__ == "__main__":
    import uvicorn

    import nest_asyncio

    nest_asyncio.apply()

    # Run the FastAPI application
    if "PORT" in config.keys():
        port = config["PORT"]
    else:
        port = 14002
    uvicorn.run(app, host="0.0.0.0", port=port)