import logging
import os
import secrets
import time

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

from database import Neo4jDatabase, URI, USERNAME, PASSWORD
import queries
import formatter

# --------------------------------------------------
# Security configuration
# --------------------------------------------------
API_KEY = os.getenv("MPM_API_KEY", "")
if not API_KEY:
    raise RuntimeError(
        "MPM_API_KEY is not set. Configure it before starting the backend."
    )

MAX_INPUT_LENGTH = 100

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("mpm_api")

app = FastAPI(
    title="MPM Knowledge Graph API",
    description="Backend API services for Malignant Pleural Mesothelioma Knowledge Graph System",
    version="1.2.0-secure"
)

# Local development only: do not expose the API to arbitrary browser origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8501",
        "http://localhost:8501"
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["X-API-Key", "Accept"]
)

# Database connection
_db = Neo4jDatabase(URI, USERNAME, PASSWORD)


@app.middleware("http")
async def security_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        "IP=%s | %s %s | status=%s | %.1fms",
        client_ip,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms
    )
    return response


def require_api_key(request: Request):
    supplied = request.headers.get("X-API-Key", "")
    if not supplied or not secrets.compare_digest(supplied, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def validate_keyword(value: str, field_name: str = "keyword") -> str:
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty")
    if len(value) > MAX_INPUT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} exceeds the {MAX_INPUT_LENGTH}-character limit"
        )
    return value


@app.get("/")
def root(request: Request):
    require_api_key(request)
    return {
        "system": "MPM Knowledge Graph API Service",
        "status": "Running",
        "version": "1.1.0-secure"
    }


@app.get("/api/entity/search")
def search_entity_api(
    request: Request,
    keyword: str = Query(..., description="Entity name or ID")
):
    require_api_key(request)
    keyword = validate_keyword(keyword)
    results = queries.search_entity(_db, keyword)
    return {"query": keyword, "count": len(results), "data": results}


@app.get("/api/relationship")
def get_relationship_api(
    request: Request,
    keyword: str = Query(..., description="Entity name or ID")
):
    require_api_key(request)
    keyword = validate_keyword(keyword)
    raw_results = queries.get_relationships(_db, keyword)
    formatted_graph = formatter.format_relationships_to_graph(raw_results)
    return {
        "query": keyword,
        "raw_data": raw_results,
        "graph": formatted_graph
    }


@app.get("/api/path/multihop")
def get_multihop_api(
    request: Request,
    start: str = Query(..., description="Start entity name or ID"),
    end: str = Query(..., description="End entity name or ID")
):
    require_api_key(request)
    start = validate_keyword(start, "start")
    end = validate_keyword(end, "end")
    raw_results = queries.get_multihop_path(_db, start, end)
    formatted_graph = formatter.format_multihop_to_graph(raw_results)
    return {
        "start": start,
        "end": end,
        "paths_found": len(raw_results),
        "raw_paths": raw_results,
        "graph": formatted_graph
    }


@app.get("/api/publication")
def get_publication_api(
    request: Request,
    keyword: str = Query(..., description="Entity name or ID")
):
    require_api_key(request)
    keyword = validate_keyword(keyword)
    results = queries.get_publication_evidence(_db, keyword)
    return {"query": keyword, "count": len(results), "publications": results}


@app.get("/api/drug-target")
def get_drug_target_api(
    request: Request,
    keyword: str = Query(..., description="Drug name or DrugBank ID")
):
    require_api_key(request)
    keyword = validate_keyword(keyword)
    results = queries.get_drug_target_disease_chain(_db, keyword)
    return {"query": keyword, "count": len(results), "data": results}


@app.on_event("shutdown")
def shutdown_event():
    _db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
