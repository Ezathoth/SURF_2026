from database import Neo4jDatabase, URI, USERNAME, PASSWORD
from queries import get_multihop_path

db = Neo4jDatabase(
    URI,
    USERNAME,
    PASSWORD
)

print("=== Phase 8.4 Multi-hop Path Query Test ===")
start_entity = input("Enter Start Entity (e.g. Pemetrexed / BAP1): ").strip()
end_entity = input("Enter End Entity (e.g. Malignant Pleural Mesothelioma / hsa04390): ").strip()

results = get_multihop_path(
    db,
    start_entity,
    end_entity
)

print("-" * 60)

if not results:
    print(f"No multi-hop path found between '{start_entity}' and '{end_entity}'.")
else:
    print(f"Found {len(results)} path(s):\n")
    for idx, res in enumerate(results, start=1):
        nodes = res["NodeChain"]
        rels = res["RelChain"]

        # 拼接打印完整链路: [Node1] --REL1--> [Node2] --REL2--> [Node3]
        path_str = f"Path {idx} ({res['HopLength']} hops): "
        for i in range(len(rels)):
            path_str += f"[{nodes[i]}] --{rels[i]}--> "
        path_str += f"[{nodes[-1]}]"

        print(path_str)

db.close()