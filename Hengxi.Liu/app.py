import streamlit as st
import requests
from streamlit_agraph import agraph, Node, Edge, Config


# ==========================================
# Utility Functions
# ==========================================

def shorten_label(text, max_length=18):

    if len(text) > max_length:
        return text[:max_length] + "..."

    return text



def detect_entity_type(entity):

    """
    Multi-hop fallback entity type detection
    """

    entity_upper = str(entity).upper()


    # Gene examples
    gene_list = [
        "TP53",
        "BAP1",
        "NF2",
        "CDKN2A",
        "BRCA1",
        "BRCA2"
    ]

    if entity_upper in gene_list:
        return "Gene"


    # Pathway ID
    if entity_upper.startswith("HSA"):
        return "Pathway"


    # Disease ontology
    if entity_upper.startswith("DOID"):
        return "Disease"


    # Publication
    if entity_upper.isdigit() and len(entity_upper) == 8:
        return "Publication"


    # DrugBank
    if entity_upper.startswith("DB"):
        return "Drug"


    # Common drugs
    drug_keywords = [
        "PEMETREXED",
        "CISPLATIN",
        "CARBOPLATIN",
        "NIVOLUMAB",
        "PEMBROLIZUMAB"
    ]

    if entity_upper in drug_keywords:
        return "Drug"


    return "Entity"



ENTITY_COLOR = {

    "Gene": "#4C9AFF",

    "Protein": "#9B59B6",

    "Drug": "#E74C3C",

    "Disease": "#F39C12",

    "Pathway": "#2ECC71",

    "Publication": "#95A5A6",

    "Entity": "#BDC3C7"

}



# ==========================================
# Backend API
# ==========================================

API_BASE_URL = "http://127.0.0.1:8000"



st.set_page_config(

    page_title="MPM Knowledge Graph System",

    page_icon="🧬",

    layout="wide"

)



st.title(
    "🧬 Malignant Pleural Mesothelioma Knowledge Graph System"
)


st.caption(
    "Phase 8.9: Multi-omics & Literature Interactive Query Dashboard"
)



# ==========================================
# Sidebar
# ==========================================

st.sidebar.header("🔍 Query Modules")


module = st.sidebar.radio(

    "Select Functionality:",

    [

        "1. Entity Search",

        "2. Relationship Exploration",

        "3. Multi-hop Path Query",

        "4. Supporting Literature Evidence",

        "5. Drug - Target - Disease Chain"

    ]

)



# ==========================================
# Module 1 Entity Search
# ==========================================


if module == "1. Entity Search":


    st.subheader("🔎 Entity Search")


    keyword = st.text_input(

        "Enter Entity:",

        value=""

    )


    st.caption(
        "Example: TP53, BAP1, Pemetrexed, DB00642"
    )


    if st.button("Search Entity"):


        res = requests.get(

            f"{API_BASE_URL}/api/entity/search",

            params={
                "keyword": keyword
            }

        )


        if res.status_code == 200:


            data = res.json().get(
                "data",
                []
            )


            st.success(
                f"Found {len(data)} matched record(s)"
            )


            st.dataframe(

                data,

                use_container_width=True

            )


        else:

            st.error(
                "API Request Failed."
            )




# ==========================================
# Module 2 Relationship Exploration
# ==========================================


elif module == "2. Relationship Exploration":


    st.subheader(
        "🕸️ Relationship & Neighbor Exploration"
    )


    keyword = st.text_input(

        "Enter Central Entity:",

        value=""

    )


    st.caption(
        "Example: TP53, BAP1, Pemetrexed"
    )



    if st.button(
        "Explore Relationships"
    ):


        res = requests.get(

            f"{API_BASE_URL}/api/relationship",

            params={
                "keyword": keyword
            }

        )


        if res.status_code == 200:


            graph = res.json().get(
                "graph",
                {}
            )


            raw_data = res.json().get(
                "raw_data",
                []
            )


            st.write(

                f"**Found {graph['summary']['total_nodes']} Nodes, "
                f"{graph['summary']['total_edges']} Edges**"

            )


            nodes = [

                Node(

                    id=n["id"],

                    label=n["id"],

                    size=14,

                    group=n["group"],

                    font={
                        "size":12
                    }

                )

                for n in graph["nodes"]

            ]



            edges = [

                Edge(

                    source=e["source"],

                    target=e["target"],

                    label=shorten_label(
                        e["type"]
                    ),

                    font={
                        "size":8
                    },

                    smooth=True

                )

                for e in graph["edges"]

            ]



            config = Config(

                width=1100,

                height=650,

                directed=True,

                nodeHighlightBehavior=True,

                collapsible=True

            )


            agraph(

                nodes=nodes,

                edges=edges,

                config=config

            )



            with st.expander(
                "View Raw Relationship Table"
            ):

                st.dataframe(

                    raw_data,

                    use_container_width=True

                )


        else:

            st.error(
                "API Request Failed."
            )

# ==========================================
# Module 3 Multi-hop Path Query
# ==========================================


elif module == "3. Multi-hop Path Query":


    st.subheader(
        "🚀 Multi-hop Path Discovery"
    )


    col1, col2 = st.columns(2)


    with col1:


        start = st.text_input(

            "Start Entity:",

            value=""

        )


        st.caption(
            "Example: TP53, BAP1, Pemetrexed"
        )


    with col2:


        end = st.text_input(

            "End Entity:",

            value=""

        )


        st.caption(
            "Example: hsa04330, DOID:7474"
        )



    if st.button(
        "Find Paths"
    ):


        res = requests.get(

            f"{API_BASE_URL}/api/path/multihop",

            params={

                "start": start,

                "end": end

            }

        )



        if res.status_code == 200:


            graph = res.json().get(

                "graph",

                {}

            )


            paths = res.json().get(

                "raw_paths",

                []

            )



            st.success(

                f"Found {len(paths)} path(s) between "
                f"'{start}' and '{end}'"

            )



            # ==========================================
            # Improved Multi-hop Visualization
            # ==========================================


            nodes = []



            for n in graph.get("nodes", []):


                entity_id = n.get(

                    "id",

                    "Unknown"

                )


                # 优先读取 formatter 提供的信息
                entity_type = n.get(

                    "group",

                    n.get(

                        "label",

                        detect_entity_type(entity_id)

                    )

                )



                nodes.append(

                    Node(

                        id=entity_id,

                        label=entity_id,

                        size=14,

                        group=entity_type,

                        color=ENTITY_COLOR.get(

                            entity_type,

                            "#BDC3C7"

                        ),

                        font={

                            "size":12

                        }

                    )

                )



            edges = []



            for e in graph.get("edges", []):


                edges.append(

                    Edge(

                        source=e["source"],

                        target=e["target"],

                        label=shorten_label(

                            e["type"]

                        ),

                        font={

                            "size":8

                        },

                        smooth=True

                    )

                )



            config = Config(

                width=1100,

                height=650,

                directed=True,

                nodeHighlightBehavior=True,

                collapsible=True

            )



            agraph(

                nodes=nodes,

                edges=edges,

                config=config

            )




            with st.expander(

                "View Path Details"

            ):


                for idx, p in enumerate(

                    paths,

                    start=1

                ):


                    st.markdown(

                        f"**Path {idx} "
                        f"({p['HopLength']} hops):** "
                        f"`{' -> '.join(p['NodeChain'])}`"

                    )



        else:


            st.error(

                "API Request Failed."

            )



# ==========================================
# Module 4 Publication Evidence
# ==========================================


elif module == "4. Supporting Literature Evidence":


    st.subheader(

        "📚 Literature & Evidence Lineage"

    )



    keyword = st.text_input(

        "Enter Target Entity:",

        value=""

    )


    st.caption(

        "Example: TP53, BAP1, Pemetrexed"

    )



    if st.button(

        "Query Publications"

    ):


        res = requests.get(

            f"{API_BASE_URL}/api/publication",

            params={

                "keyword": keyword

            }

        )


        if res.status_code == 200:


            pubs = res.json().get(

                "publications",

                []

            )


            st.success(

                f"Found {len(pubs)} publication(s)"

            )



            for p in pubs:


                with st.container():


                    st.markdown(

                        f"#### [{p['Year']}] {p['Title']}"

                    )


                    st.caption(

                        f"**Journal**: {p['Journal']} | "
                        f"**PMID**: {p['PMID']} | "
                        f"**Evidence Level**: "
                        f"{p['EvidenceLevel']}"

                    )


                    st.info(

                        f"**Main Finding**: "
                        f"{p['MainFinding']}"

                    )


                    st.divider()



        else:


            st.error(

                "API Request Failed."

            )



# ==========================================
# Module 5 Drug Target Disease Chain
# ==========================================


elif module == "5. Drug - Target - Disease Chain":


    st.subheader(

        "💊 Drug - Target - Disease Closed Loop"

    )



    keyword = st.text_input(

        "Enter Drug Name or DrugBank ID:",

        value=""

    )


    st.caption(

        "Example: Pemetrexed / Cisplatin / DB00642"

    )



    if st.button(

        "Query Closed Loop"

    ):


        res = requests.get(

            f"{API_BASE_URL}/api/drug-target",

            params={

                "keyword": keyword

            }

        )



        if res.status_code == 200:


            drugs = res.json().get(

                "data",

                []

            )


            st.success(

                f"Found {len(drugs)} record(s)"

            )



            for d in drugs:


                st.markdown(

                    f"### 💊 {d['DrugName']} "
                    f"(`{d['DrugID']}`)"

                )


                st.write(

                    f"**Clinical Status**: "
                    f"{d['ClinicalStatus']}"

                )


                st.write(

                    f"**Target Disease**: "
                    f"{d['DiseaseName']}"

                )


                st.write(

                    f"**Mechanism**: "
                    f"{d['Mechanism']}"

                )


                st.divider()



        else:


            st.error(

                "API Request Failed."

            )