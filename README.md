
# 📚 Citation-Stance Graph (Interactive App)

**Visualize rhetorical relationships between papers in a Zotero collection.**
Upload a Zotero JSON → fetch OpenAlex metadata → classify citation roles with an LLM → generate an interactive HTML citation graph.

Built originally as a minimal research tool — now evolving into a community-ready project.
**Collaborators very welcome! 💛**

---

# 🚀 NEW: Streamlit App (v2)

A one-step, user-friendly interface to run the entire pipeline **without touching the file structure or scripts**.

## Easy run of the app: 

Just go to https://citationstancegraph.streamlit.app/

Put in your API key, upload your .json. Then you have everything! 

## How to run the app with download

From the repo root:

```
python -m venv .venv
.\.venv\Scripts\activate

cd app
pip install -r requirements.txt
pip install -e .

streamlit run app.py
```

Then in your browser:

1. **Upload** a Zotero JSON export (any path, no special folder needed)  
2. **Paste** your OpenAI API key  
3. **Click “Run analysis”**  
4. View or download the generated **interactive citation graph**  
   (steady layout, color-coded edges, author-year labels)

---

# 🖼 What the app generates

An HTML graph where:

- **Nodes** = papers in your Zotero collection  
- **Edges** = A cites B  
- **Colors** = rhetorical role  
  - 🟩 SUPPORT  
  - 🟥 DISPUTE  
  - 🩶 BACKGROUND  
- **Hover info** includes:
  - full title  
  - DOI  
  - publication year  
  - scite tallies (supporting / contradicting / mentioning)

This graph is saved at:

```
app_output/<collection>/processed/citation_graph_edge_roles.html
```

---

# 📢 Project Status — Simple Prototype (Collaborators Welcome!)

This repository began as an experimental prototype for analyzing citation stance.
It now includes:

- A functional **Streamlit app**
- A reorganized modular package: `visualize_paper_relation`
- A full pipeline:
  - Zotero JSON parsing  
  - DOI extraction  
  - OpenAlex metadata retrieval  
  - Citation extraction  
  - scite global tallies  
  - LLM rhetorical-role classification  
  - Interactive visualization  

This is still **not a finished product** — but a strong foundation for:

- UI/dashboard improvements  
- Better citation stance models  
- PDF full-text integration  
- Better graph layouts  
- Packaging for PyPI  
- Cloud or HuggingFace Spaces deployment  

If any of these excite you, please open issues or PRs.
I would genuinely love collaborators.

---

# 🧠 Architecture

```
citation_stance_graph/
  app/
    app.py
    src/visualize_paper_relation/
      pipeline.py
      zotero.py
      openalex.py
      scite_api.py
      scite_tallies_table.py
      scite_merge.py
      graph_data.py
      graph_build.py
      llm_edge_roles.py
      graph_visualization.py

  scripts_legacy/
  data/
  README.md
  requirements.txt
```

---

# 🔄 Legacy CLI Pipeline (optional)

The original step-by-step scripts remain available inside `scripts_legacy/`
for transparency and reproducibility.

These generate:

- DOI lists  
- OpenAlex metadata  
- Citation edges  
- scite tallies  
- LLM role classifications  
- Interactive HTML graphs  

Use them if you prefer CLI workflows instead of the app.

---

# 🛠 Installation for Development

```bash
git clone https://github.com/<your-username>/citation_stance_graph.git
cd citation_stance_graph

python -m venv .venv
.\.venv\Scriptsctivate

pip install -r requirements.txt
```

(Optional) Create `.env`:

```
OPENAI_API_KEY=your_key_here
SCITE_API_KEY=optional
```

---

# 🌐 Data sources

- Zotero JSON export  
- OpenAlex API  
- scite.ai tallies  
- LLM models (title + abstract classification)  

---

# ✨ Future Directions

Looking for collaborators on:

- PDF full-text stance extraction  
- Document embeddings & topic clustering  
- Community detection over citation graphs  
- Better LLM prompting or fine-tuning  
- Web deployment  
- Zotero plugin development
- JS/React front-end version  

---

# 📬 Contact

Issues, PRs, and discussions are welcome.  
Let’s build this into a genuinely useful open tool for the community. 💛
