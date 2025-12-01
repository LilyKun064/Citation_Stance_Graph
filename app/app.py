from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
import base64

import streamlit as st

# -------------------------------------------------------------------
# Ensure app/src is on sys.path so we can import visualize_paper_relation
# -------------------------------------------------------------------
APP_ROOT = Path(__file__).resolve().parent
SRC_DIR = APP_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from visualize_paper_relation.pipeline import run_pipeline  # noqa: E402

# Project root (repo root = parent of app/)
PROJECT_ROOT = APP_ROOT.parent

# Path to your cat logo image
LOGO_PATH = APP_ROOT / "assets" / "Jesse.png"


def show_logo_top_right():
    """
    Show the cat logo fixed in the top-right corner.
    Uses base64 + HTML/CSS so it stays independent of layout.
    """
    if not LOGO_PATH.exists():
        # Fail silently if the logo is missing
        return

    with open(LOGO_PATH, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode("utf-8")

    # Small, circular logo with a subtle shadow
    logo_html = f"""
    <style>
    .app-logo-container {{
        position: fixed;
        top: 80px;
        right: 30px;
        z-index: 9999;
    }}
    .app-logo-container img {{
        width: 72px;
        height: 72px;
        object-fit: cover;
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(0, 0, 0, 0.4);
        border: 2px solid #ffffff;
    }}
    </style>
    <div class="app-logo-container">
        <img src="data:image/png;base64,{b64}" alt="Cat logo">
    </div>
    """

    st.markdown(logo_html, unsafe_allow_html=True)


# -------------------------------------------------------------------
# Streamlit page config
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Visualize Paper Relations",
    layout="wide",
)

# Show the cat logo in the top-right corner
show_logo_top_right()

st.title("📚 Visualize Paper Relations from Zotero JSON")


st.markdown(
    """
This app takes a Zotero **JSON export** of your collection and builds a citation graph with:

- OpenAlex metadata  
- scite.ai tallies  
- Per-edge rhetorical roles from an LLM (SUPPORT / DISPUTE / BACKGROUND / METHOD)  
- An interactive, steady (non-spinning) HTML graph  

**Steps:**
1. Export your Zotero collection as **BetterBibTex JSON**.  
2. Upload the `.json` file below.  
3. Paste your **OpenAI API key**.  
4. Click **Run analysis** and wait for the graph to appear (it might take a while).
"""
)


# -------------------------------------------------------------------
# Sidebar inputs
# -------------------------------------------------------------------
st.sidebar.header("Settings")

api_key = st.sidebar.text_input(
    "OpenAI API key",
    type="password",
    help="Used locally to call the OpenAI API for edge-role classification.",
)

uploaded_file = st.file_uploader(
    "Upload Zotero JSON export",
    type=["json"],
    help="Export your Zotero collection as JSON and upload that file here.",
)

default_out_dir = PROJECT_ROOT / "app_output"
out_dir_str = st.sidebar.text_input(
    "Output folder (on disk)",
    value=str(default_out_dir),
    help="Where intermediate files and the final HTML graph will be saved.",
)

run_button = st.button("🚀 Run analysis", type="primary")


# -------------------------------------------------------------------
# Main app logic
# -------------------------------------------------------------------
if run_button:
    # Basic validation of inputs
    if not uploaded_file:
        st.error("Please upload a Zotero JSON file first.")
        st.stop()

    if not api_key:
        st.error("Please paste your OpenAI API key in the sidebar.")
        st.stop()

    # Make sure the OpenAI client in the pipeline sees the key
    os.environ["OPENAI_API_KEY"] = api_key

    # Resolve output directory
    out_dir = Path(out_dir_str).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    st.info(f"Output directory: `{out_dir}`")

    # Save uploaded Zotero JSON to a temporary file, then pass its path
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        zotero_json_path = tmpdir_path / "collection.json"
        zotero_json_path.write_bytes(uploaded_file.getbuffer())

        st.write("✅ Zotero JSON saved, starting pipeline...")

        with st.spinner("Running full pipeline (OpenAlex, scite, LLM, graph)..."):
            try:
                results = run_pipeline(
                    zotero_json_path=zotero_json_path, output_dir=out_dir
                )
            except Exception as e:
                st.error(f"Pipeline error: {e}")
                st.stop()

    st.success("Pipeline finished.")

    # ------------------------------------------------------------------
    # Load and display the final HTML graph
    # ------------------------------------------------------------------
    graph_html_path = (
        results.get("graph_html")
        or results.get("graph_html_path")
        or (out_dir / "processed" / "citation_graph_edge_roles.html")
    )

    if not graph_html_path.exists():
        st.error(
            "The pipeline completed, but I couldn't find the final HTML graph at:\n\n"
            f"`{graph_html_path}`\n\n"
            "Check that the visualization step wrote the expected file."
        )
    else:
        html_str = graph_html_path.read_text(encoding="utf-8")

        st.subheader("Interactive citation graph")
        st.caption(
            "Edges are colored by LLM role: green = SUPPORT, red = DISPUTE, "
            "gray = BACKGROUND / METHOD."
        )

        st.components.v1.html(html_str, height=800, scrolling=True)

        st.download_button(
            label="💾 Download graph HTML",
            data=html_str,
            file_name="citation_graph_edge_roles.html",
            mime="text/html",
        )

        with st.expander("Show output paths on disk"):
            st.write(f"Output directory: `{out_dir}`")
            for key, value in results.items():
                if isinstance(value, Path):
                    st.write(f"- **{key}**: `{value}`")
