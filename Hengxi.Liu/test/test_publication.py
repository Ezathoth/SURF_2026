from database import Neo4jDatabase, URI, USERNAME, PASSWORD
from queries import get_publication_evidence

db = Neo4jDatabase(
    URI,
    USERNAME,
    PASSWORD
)

print("=== Phase 8.5 Publication Query Test ===")
keyword = input("Enter Entity Name or ID (e.g. BAP1 / Pemetrexed): ").strip()

results = get_publication_evidence(db, keyword)

print("-" * 60)

if not results:
    print(f"No publication evidence found for '{keyword}'.")
else:
    print(f"Found {len(results)} supporting publication(s):\n")
    for idx, pub in enumerate(results, start=1):
        print(f"[{idx}] PMID: {pub['PMID']} ({pub['Year']}) - {pub['Journal']}")
        print(f"    Title: {pub['Title']}")
        print(f"    Target Entity: {pub['TargetType']} [{pub['TargetName']}]")
        print(f"    Evidence Level: {pub['EvidenceLevel']}")
        print(f"    Main Finding: {pub['MainFinding']}")
        print("-" * 60)

db.close()