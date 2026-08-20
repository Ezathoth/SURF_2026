# ==========================================
# Phase 8.7: Query Result Formatter
# ==========================================

def format_relationships_to_graph(records):
    """
    将 get_relationships 的查询结果转为标准 Node-Edge 图结构 JSON
    """
    nodes = {}
    edges = []

    for rec in records:
        src_type = rec.get("SourceType", "Entity")
        src_id = rec.get("SourceEntity")
        rel_type = rec.get("Relationship", "RELATED")
        tgt_type = rec.get("TargetType", "Entity")
        tgt_id = rec.get("TargetEntity")

        if src_id and src_id not in nodes:
            nodes[src_id] = {"id": src_id, "label": src_type, "group": src_type}

        if tgt_id and tgt_id not in nodes:
            nodes[tgt_id] = {"id": tgt_id, "label": tgt_type, "group": tgt_type}

        if src_id and tgt_id:
            edges.append({
                "source": src_id,
                "target": tgt_id,
                "type": rel_type,
                "label": rel_type
            })

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
    }


def format_multihop_to_graph(records):
    """
    将 get_multihop_path 的多跳路径结果转为全网图拓扑 JSON
    """
    nodes = {}
    edges = []

    for rec in records:
        node_chain = rec.get("NodeChain", [])
        rel_chain = rec.get("RelChain", [])

        for node_id in node_chain:
            if node_id and node_id not in nodes:
                nodes[node_id] = {"id": node_id, "label": "Entity"}

        for i in range(len(rel_chain)):
            u = node_chain[i]
            v = node_chain[i + 1]
            rel = rel_chain[i]
            edges.append({
                "source": u,
                "target": v,
                "type": rel,
                "label": rel
            })

    # 去重边
    unique_edges = [dict(t) for t in {tuple(d.items()) for d in edges}]

    return {
        "nodes": list(nodes.values()),
        "edges": unique_edges,
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(unique_edges)
        }
    }