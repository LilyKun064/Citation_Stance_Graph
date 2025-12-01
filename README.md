# Citation-Stance Graph Toolkit

A clean, end-to-end workflow that transforms a Zotero collection into an
interactive citation network enriched with OpenAlex metadata, scite
global tallies, and LLM-inferred rhetorical roles
(SUPPORT / DISPUTE / BACKGROUND / METHOD).
Original idea was a combination of Scite and Zotero BetterNotes. 

This toolkit answers:
**“Which papers in my collection cite each other, and do they agree, disagree, or reference each other as background?”**

## 📢 Project Status — Simple Prototype (Collaborators Welcome!)

This repository contains a very early, experimental prototype of a citation-stance graph system.
It currently supports:
- Extracting DOIs from a Zotero library
- Fetching OpenAlex metadata
- Building a citation graph
- Fetching scite global tallies
- Using an LLM to classify citation roles (support / dispute / background / method)
- Producing an interactive HTML visualization

This is not a finished tool.
Right now it is a minimal working model that I built for my own research purposes.

However, I would love help turning this into a polished, reliable, community-friendly project.

If you’re interested in:
- improving data pipelines
- integrating PDF full-text stance detection
- building a UI or dashboard
- enhancing visualizations
- adding more metadata sources
- developing better models for rhetorical roles
- making this into a pip installable package
please feel free to open issues, start discussions, or submit pull requests.

I’m very open to collaborations and suggestions from anyone who finds this idea useful or exciting.
Let’s build this together. 💛

## Update: One-Step Handling

Run the full citation-stance pipeline for a Zotero collection from **any directory**. The pipeline no longer requires your Zotero export file to be placed inside the project structure.

### Usage (from repo root, inside venv):

    python scripts/run_full_pipeline_from_zotero.py <collection_slug> <zotero_json_path>

- `<collection_slug>` is something like: `LLM_Gender_Bias`
- `<zotero_json_path>` can be **ANY** `.json` file path (Downloads, Desktop, Zotero temp folder, etc.)

### How it works internally

- The script accepts your JSON from anywhere on your machine.
- It automatically copies it (if needed) into:

      data/<collection_slug>/raw/zotero/<collection_slug>.json

- If the file is already in this location, the script detects it and skips the copy.
- Then it runs all pipeline steps sequentially, ending with:

      data/<collection_slug>/processed/citation_graph_edge_roles.html

This update makes Zotero integration fully seamless and zero-maintenance.


---

## 🚀 Pipeline Overview

The pipeline processes your Zotero library through these stages:

1. Zotero JSON → DOIs  
2. DOIs → OpenAlex metadata (titles, authors, abstracts, references)  
3. OpenAlex → citation tables  
4. Filter edges to only within your collection  
5. scite → global tallies (supporting / contradicting counts)  
6. Merge tallies into paper metadata  
7. Build a NetworkX citation graph  
8. LLM (title + abstract) → rhetorical classification for each citation edge  
9. Final interactive HTML visualization with color-coded arrows

---

# 📁 Directory Structure (Clean & Final)

```
citation_stance_graph/
  data/
    MyCollection/
      raw/
        zotero/
        openalex/
        scite/
      interim/
      processed/
  scripts/
    extract_dois.py
    fetch_openalex.py
    build_nodes_and_edges.py
    filter_collection_edges.py
    fetch_scite_tallies.py
    scite_tallies_to_csv.py
    merge_scite_into_papers.py
    build_graph_openalex_with_scite.py
    classify_edge_roles_llm.py
    plot_graph_interactive_edge_roles.py

  src/csg/
    io/
      zotero_json.py
      openalex_api.py
      openalex_parse.py
    llm/
      classify_edge_role.py
    models/
      data_structure.py

  README.md
  requirements.txt
  .env
```

---

# 🛠 Installation

### 1. Create environment
```bash
pip install -r requirements.txt
```

### 2. Add your API key
Create a `.env` file at project root:

```
OPENAI_API_KEY=your_key_here
```

No scite API key is needed for global tallies.

---

# 🔄 Full Pipeline (Step-by-Step Commands)

## **Step 1 — Extract DOIs from Zotero JSON**
Place your Zotero export here:
```
data/Your_Collection_Name/raw/zotero/YourCollection.json
```

Run:
```bash
python scripts/run_from_zotero_json.py Your_Collection_Name
```

Produces:
```
data/interim/doi_list.txt
```

---

## **Step 2 — Fetch OpenAlex metadata for each DOI**
```bash
python scripts/fetch_openalex_for_dois.py Your_Collection_Name
```

Produces:
```
data/raw/openalex/<id>.json
```

Each file includes:
- Title
- Authors
- Abstract
- Year
- OpenAlex ID
- Reference list

---

## **Step 3 — Build citation tables**
```bash
python scripts/build_openalex_citation_graph.py Your_Collection_Name
```

Produces:
```
data/processed/papers.csv
data/processed/citation_edges_raw.csv
```

---

## **Step 4 — Keep only citations within your collection**
```bash
python scripts/filter_collection_edges.py Your_Collection_Name
```

Produces:
```
data/processed/citation_edges_collection.csv
```

---

## **Step 5 — Fetch scite global tallies (no API key required)**
```bash
python scripts/fetch_scite_tallies.py Your_Collection_Name
```

Produces:
```
data/raw/scite/tallies.json
```

---

## **Step 6 — Convert tallies to CSV**
```bash
python scripts/parse_scite_tallies.py Your_Collection_Name
```

Produces:
```
data/processed/scite_tallies.csv
```

---

## **Step 7 — Merge tallies into paper metadata**
```bash
python scripts/merge_scite_into_papers.py Your_Collection_Name
```

Produces:
```
data/processed/papers_with_scite.csv
```

---

## **Step 8 — Build final citation graph**
```bash
python scripts/build_networkx_graph.py Your_Collection_Name
```

Produces:
```
citation_graph_openalex_with_scite.graphml
```

---

## **Step 9 — LLM rhetorical-role classification (title + abstract)**
```bash
python scripts/classify_collection_edges_llm.py Your_Collection_Name
```

Produces:
```
edge_roles_llm.csv
```

---

## **Step 10 — Generate interactive visualization**
```bash
python scripts/plot_graph_interactive_edge_roles.py Your_Collection_Name
```

Produces:
```
citation_graph_edge_roles.html
```

This visualization shows:
- Nodes = papers  
- Edges = citations  
- Green = SUPPORT  
- Red = DISPUTE  
- Gray = BACKGROUND or METHOD  
- Labels = Author Year  
- Hover tooltips with full title, DOI, and scite tallies  
- Tight, readable layout using PyVis  

---

# ✨ Notes

- scite **pairwise** (sentence-level) API is not used.  
- Global scite tallies **are** used and require **no API key**.  
- LLM classifications are based on **titles + abstracts** (from OpenAlex).  
- You can extend this toolkit with PDF extraction, clustering, topic models, or community detection.

---

# 📬 Contact

If you want:
- A fully automated one-command pipeline  
- Co-citation or bibliographic coupling analysis  
- Topic clustering or embedding-based graph layouts  
- PDF-based stance extraction (GROBID)  

Just ask!
