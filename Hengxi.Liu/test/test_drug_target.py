from database import Neo4jDatabase, URI, USERNAME, PASSWORD
from queries import get_drug_target_disease_chain

db = Neo4jDatabase(
    URI,
    USERNAME,
    PASSWORD
)

print("=== Phase 8.6 Drug / Target / Disease Closed-Loop Query Test ===")
keyword = input("Enter Drug Name or DrugBank ID (e.g. Pemetrexed / Cisplatin / DB00642): ").strip()

results = get_drug_target_disease_chain(db, keyword)

print("-" * 60)

if not results:
    print(f"No drug-target-disease chain found for '{keyword}'.")
else:
    print(f"Found {len(results)} Drug Record(s):\n")
    for idx, drug in enumerate(results, start=1):
        print(f"[{idx}] Drug: {drug['DrugName']} ({drug['DrugID']})")
        print(f"    Clinical Status: {drug['ClinicalStatus']}")
        print(f"    Target Disease: {drug['DiseaseName']}")
        print(f"    Target Proteins: {', '.join(drug['TargetProteins']) if drug['TargetProteins'] else 'None'}")
        print(f"    Related Genes: {', '.join(drug['RelatedGenes']) if drug['RelatedGenes'] else 'None'}")
        print(f"    Mechanism: {drug['Mechanism']}")
        print("-" * 60)

db.close()