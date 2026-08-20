import json
from database import Neo4jDatabase, URI, USERNAME, PASSWORD
from queries import get_relationships, get_multihop_path
from formatter import format_relationships_to_graph, format_multihop_to_graph

db = Neo4jDatabase(URI, USERNAME, PASSWORD)

print("=== Phase 8.7 Query Result Formatting Test ===")

# 1. 测试单跳关系格式化
raw_rels = get_relationships(db, "BAP1")
graph_json_1 = format_relationships_to_graph(raw_rels)

print("\n1. Relationship Graph JSON (BAP1):")
print(json.dumps(graph_json_1, indent=2, ensure_ascii=False))

# 2. 测试多跳路径格式化
raw_paths = get_multihop_path(db, "Pemetrexed", "Malignant Pleural Mesothelioma")
graph_json_2 = format_multihop_to_graph(raw_paths)

print("\n2. Multi-hop Path Graph JSON (Pemetrexed -> MPM):")
print(json.dumps(graph_json_2, indent=2, ensure_ascii=False))

db.close()