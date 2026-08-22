"""Cypher query definitions for the MPM Knowledge Graph.

Security note: user-controlled values are passed as Cypher parameters rather
than concatenated into query strings. Multi-hop traversal is deliberately
restricted to 1-3 hops to bound query cost.
"""

SEARCH_ENTITY_QUERY = """
MATCH (n)
WHERE
    n.Standard_Name = $keyword
    OR n.Gene_ID = $keyword
    OR n.UniProt_ID = $keyword
    OR n.Pathway_ID = $keyword
    OR n.DrugBank_ID = $keyword
    OR n.DOID = $keyword
    OR n.PMID = $keyword
RETURN
    labels(n)[0] AS EntityType,
    n.Standard_Name AS Standard_Name,
    n.Gene_ID AS Gene_ID,
    n.UniProt_ID AS UniProt_ID,
    n.Pathway_ID AS Pathway_ID,
    n.DrugBank_ID AS DrugBank_ID,
    n.DOID AS DOID,
    n.PMID AS PMID
ORDER BY EntityType
"""


def search_entity(db, keyword):
    return db.execute_query(
        SEARCH_ENTITY_QUERY,
        {"keyword": keyword}
    )

RELATIONSHIP_QUERY = """
MATCH (n)-[r]->(m)
WHERE
    n.Standard_Name = $keyword
    OR n.Gene_ID = $keyword
    OR n.UniProt_ID = $keyword
    OR n.Pathway_ID = $keyword
    OR n.DrugBank_ID = $keyword
    OR n.DOID = $keyword
    OR n.PMID = $keyword

RETURN
    labels(n)[0] AS SourceType,
    coalesce(
        n.Standard_Name,
        n.Gene_ID,
        n.UniProt_ID,
        n.Pathway_ID,
        n.DrugBank_ID,
        n.DOID,
        n.PMID
    ) AS SourceEntity,
    type(r) AS Relationship,
    labels(m)[0] AS TargetType,
    coalesce(
        m.Standard_Name,
        m.Gene_ID,
        m.UniProt_ID,
        m.Pathway_ID,
        m.DrugBank_ID,
        m.DOID,
        m.PMID
    ) AS TargetEntity
ORDER BY TargetType, TargetEntity
"""


def get_relationships(db, keyword):
    return db.execute_query(
        RELATIONSHIP_QUERY,
        {"keyword": keyword}
    )


# ==========================================
# Phase 8.4: Multi-hop Path Query (Case-Insensitive)
# ==========================================

MULTIHOP_PATH_QUERY = """
MATCH path = (start)-[*1..3]-(end)
WHERE 
    (
        toLower(start.Standard_Name) CONTAINS toLower($start_keyword) 
        OR toString(start.Gene_ID) = $start_keyword 
        OR toLower(start.UniProt_ID) = toLower($start_keyword) 
        OR toLower(start.Pathway_ID) = toLower($start_keyword) 
        OR toLower(start.DrugBank_ID) = toLower($start_keyword) 
        OR toLower(start.DOID) = toLower($start_keyword) 
        OR toString(start.PMID) = $start_keyword
    )
    AND 
    (
        toLower(end.Standard_Name) CONTAINS toLower($end_keyword) 
        OR toString(end.Gene_ID) = $end_keyword 
        OR toLower(end.UniProt_ID) = toLower($end_keyword) 
        OR toLower(end.Pathway_ID) = toLower($end_keyword) 
        OR toLower(end.DrugBank_ID) = toLower($end_keyword) 
        OR toLower(end.DOID) = toLower($end_keyword) 
        OR toString(end.PMID) = $end_keyword
    )
RETURN 
    [node IN nodes(path) | coalesce(node.Standard_Name, node.Gene_ID, node.UniProt_ID, node.Pathway_ID, node.DrugBank_ID, node.DOID, node.PMID)] AS NodeChain,
    [rel IN relationships(path) | type(rel)] AS RelChain,
    length(path) AS HopLength
ORDER BY HopLength ASC
LIMIT 10
"""

def get_multihop_path(db, start_keyword, end_keyword):
    """
    查询起点实体与终点实体之间的任意多跳路径 (1~3跳)
    """
    return db.execute_query(
        MULTIHOP_PATH_QUERY,
        {
            "start_keyword": start_keyword,
            "end_keyword": end_keyword
        }
    )

# ==========================================
# Phase 8.5: Publication Query
# ==========================================

PUBLICATION_QUERY = """
MATCH (pub:Publication)-[r:SUPPORTS]->(target)
WHERE 
    toLower(target.Standard_Name) CONTAINS toLower($keyword) 
    OR toString(target.Gene_ID) = $keyword 
    OR toLower(target.UniProt_ID) = toLower($keyword) 
    OR toLower(target.Pathway_ID) = toLower($keyword) 
    OR toLower(target.DrugBank_ID) = toLower($keyword) 
    OR toLower(target.DOID) = toLower($keyword)
RETURN 
    pub.PMID AS PMID,
    pub.Standard_Title AS Title,
    pub.Journal AS Journal,
    pub.Year AS Year,
    pub.MainFinding AS MainFinding,
    pub.EvidenceLevel AS EvidenceLevel,
    labels(target)[0] AS TargetType,
    target.Standard_Name AS TargetName
ORDER BY pub.Year DESC
"""

def get_publication_evidence(db, keyword):
    """
    根据实体检索其背后的 PubMed 文献支撑证据
    """
    return db.execute_query(
        PUBLICATION_QUERY,
        {"keyword": keyword}
    )

# ==========================================
# Phase 8.6: Drug / Target / Disease Closed-Loop Query
# ==========================================

DRUG_TARGET_DISEASE_QUERY = """
MATCH (d:Drug)
WHERE 
    toLower(d.Standard_Name) CONTAINS toLower($keyword) 
    OR toLower(d.DrugBank_ID) = toLower($keyword)

OPTIONAL MATCH (d)-[r_treat:TREATS]->(dis:Disease)
OPTIONAL MATCH (d)-[r_target:TARGETS]->(p:Protein)
OPTIONAL MATCH (g:Gene)-[r_encode:ENCODES]->(p)
OPTIONAL MATCH (g)-[r_assoc:ASSOCIATED_WITH]->(dis)

RETURN 
    d.DrugBank_ID AS DrugID,
    d.Standard_Name AS DrugName,
    d.Mechanism AS Mechanism,
    d.ClinicalStatus AS ClinicalStatus,
    coalesce(dis.Standard_Name, 'N/A') AS DiseaseName,
    collect(DISTINCT coalesce(p.Standard_Name, p.UniProt_ID)) AS TargetProteins,
    collect(DISTINCT coalesce(g.Standard_Name, toString(g.Gene_ID))) AS RelatedGenes
ORDER BY DrugName
"""

def get_drug_target_disease_chain(db, keyword):
    """
    查询指定药物（或抗肿瘤药物）对应的靶点蛋白、关联基因及治疗疾病闭环链路
    """
    return db.execute_query(
        DRUG_TARGET_DISEASE_QUERY,
        {"keyword": keyword}
    )