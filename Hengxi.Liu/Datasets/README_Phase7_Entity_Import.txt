MPM Knowledge Graph — Phase 7 Entity Import Files

Source:
Phase 5 normalized Excel datasets supplied for Neo4j preparation.

Files:
- Gene.csv
- Protein.csv
- Pathway.csv
- Drug.csv
- Disease.csv
- Publication.csv

Transformations applied:
1. Excel index column removed (it is only a row number).
2. Gene: NCBI_Gene_ID renamed to Gene_ID to match the Neo4j constraint.
3. Disease: Disease_ID renamed to DOID and whitespace normalized
   (e.g. 'DOID: 7474' -> 'DOID:7474').
4. Other Phase 5 fields are retained.
5. Empty Excel cells are exported as empty CSV fields.
6. Identifier values are kept as text in CSV so they can be matched
   consistently with Relationship Source_ID / Target_ID.
7. No Phase 5 Excel file was modified.

Important:
Publication.csv currently contains 65 records because the supplied
Phase 5 Publication_Normalization.xlsx contains 65 rows. This is not
silently expanded to 100.
