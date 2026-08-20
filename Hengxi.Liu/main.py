from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from database import Neo4jDatabase, URI, USERNAME, PASSWORD
import queries
import formatter

app = FastAPI(
    title="MPM Knowledge Graph API",
    description="Backend API services for Malignant Pleural Mesothelioma Knowledge Graph System",
    version="1.0.0"
)

# 允许跨域请求 (CORS)，方便后续前端 Dashboard 调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 实例化数据库连接
db = Neo4jDatabase(URI, USERNAME, PASSWORD)


@app.get("/")
def root():
    return {
        "system": "MPM Knowledge Graph API Service",
        "status": "Running",
        "version": "1.0.0"
    }


# ------------------------------------------
# 1. 实体搜索接口 (Phase 8.2)
# ------------------------------------------
@app.get("/api/entity/search")
def search_entity_api(keyword: str = Query(..., description="Entity name or ID")):
    results = queries.search_entity(db, keyword)
    return {"query": keyword, "count": len(results), "data": results}


# ------------------------------------------
# 2. 单跳关系/邻居节点接口 (Phase 8.3 & 8.7)
# ------------------------------------------
@app.get("/api/relationship")
def get_relationship_api(keyword: str = Query(..., description="Entity name or ID")):
    raw_results = queries.get_relationships(db, keyword)
    formatted_graph = formatter.format_relationships_to_graph(raw_results)
    return {
        "query": keyword,
        "raw_data": raw_results,
        "graph": formatted_graph
    }


# ------------------------------------------
# 3. 多跳路径图谱接口 (Phase 8.4 & 8.7)
# ------------------------------------------
@app.get("/api/path/multihop")
def get_multihop_api(
    start: str = Query(..., description="Start entity name or ID (e.g. Pemetrexed / BAP1)"),
    end: str = Query(..., description="End entity name or ID (e.g. Malignant Pleural Mesothelioma / hsa04390)")
):
    raw_results = queries.get_multihop_path(db, start, end)
    formatted_graph = formatter.format_multihop_to_graph(raw_results)
    return {
        "start": start,
        "end": end,
        "paths_found": len(raw_results),
        "raw_paths": raw_results,
        "graph": formatted_graph
    }


# ------------------------------------------
# 4. 文献证据链接口 (Phase 8.5)
# ------------------------------------------
@app.get("/api/publication")
def get_publication_api(keyword: str = Query(..., description="Entity name or ID (e.g. BAP1 / Pemetrexed)")):
    results = queries.get_publication_evidence(db, keyword)
    return {"query": keyword, "count": len(results), "publications": results}


# ------------------------------------------
# 5. 药物-靶点-疾病闭环接口 (Phase 8.6)
# ------------------------------------------
@app.get("/api/drug-target")
def get_drug_target_api(keyword: str = Query(..., description="Drug name or DrugBank ID (e.g. Pemetrexed / Cisplatin / DB00642)")):
    results = queries.get_drug_target_disease_chain(db, keyword)
    return {"query": keyword, "count": len(results), "data": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)