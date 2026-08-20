from database import Neo4jDatabase, URI, USERNAME, PASSWORD
from queries import get_relationships


db = Neo4jDatabase(
    URI,
    USERNAME,
    PASSWORD
)

keyword = input("Search entity: ")

results = get_relationships(
    db,
    keyword
)

print("-" * 60)

if not results:
    print("No relationships found.")
else:
    for result in results:
        print(
            f"{result['SourceType']} "
            f"[{result['SourceEntity']}] "
            f"--{result['Relationship']}--> "
            f"{result['TargetType']} "
            f"[{result['TargetEntity']}]"
        )

db.close()