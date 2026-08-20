from database import Neo4jDatabase, URI, USERNAME, PASSWORD
from queries import search_entity


db = Neo4jDatabase(
    URI,
    USERNAME,
    PASSWORD
)

try:

    keyword = "TP53"

    results = search_entity(
        db,
        keyword
    )

    print("\nSearch:", keyword)
    print("-" * 60)

    for result in results:
        print(result)

finally:

    db.close()