import os
import time
import streamlit as st
import pandas as pd
from src.utils.io import ensure_dirs
from src.utils.parsing import parse_args, load_config
from src.utils.pipeline_runner import run_pipeline, PIPELINE_STEPS
from src.utils.data_loader import load_results, search_dataframe
from src.visualizations.charts import cluster_distribution, trend_frequency

def render_steps():

    status_container.empty()

    with status_container:

        for step, status in step_status.items():

            if status == "done":
                st.success(f"{step} Completo.")

            elif status == "running":
                st.info(f"{step} Executando.")

            else:
                st.write(f"{step}")

args = parse_args()
cfg = load_config(args)

paths = cfg["paths"]
ensure_dirs(paths["raw"], paths["processed"], paths["checkpoints"], paths["output"])

path = f'{cfg["paths"]["processed"]}'

result_file = os.path.join(
    cfg["paths"]["processed"],
    "clusters_defined_distinguished_trends_assessed.csv"
)

st.set_page_config(
    page_title="NeuroTrend Explorer",
    layout="wide",
)

# ----------------------------------------------------
# Custom Styling (ChatGPT-like minimal UI)
# ----------------------------------------------------

st.markdown(
"""
<style>
.stButton>button {
    background-color:#111;
    color:white;
    border-radius:8px;
    padding:10px 18px;
}

.block-container{
    padding-top:2rem;
}

div[data-testid="stProgressBar"] > div > div {
    background-color: #00c2ff;
}

</style>
""",
unsafe_allow_html=True,
)

# ----------------------------------------------------
# Sidebar
# ----------------------------------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Section",
    [
        "Run Pipeline",
        "View Results",
        "Visualizations"
    ]
)

# ----------------------------------------------------
# Pipeline Page
# ----------------------------------------------------

if page == "Run Pipeline":

    st.title("Pipeline Execution")

    st.write("Run the full data pipeline to generate updated clusters and trends.")

    run_button = st.button(
        "Run Pipeline",
        disabled=st.session_state.get("running", False)
    )

    # Layout
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Pipeline Steps")
        status_container = st.container()

    with col2:
        st.subheader("Logs")
        log_placeholder = st.empty()

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Estado inicial das etapas
    step_status = {name: "pending" for name, _ in PIPELINE_STEPS}

    def render_steps():

        status_container.empty()

        with status_container:

            for step, status in step_status.items():

                if status == "done":
                    st.success(f"{step}")

                elif status == "running":
                    st.info(f"{step}")

                else:
                    st.write(step)

    render_steps()

    if run_button:

        st.session_state["running"] = True

        logs = []

        def log_callback(message):

            logs.append(message)

            log_placeholder.markdown(
                f"""
                <div style="height:400px;overflow:auto;background:#111;padding:10px;border-radius:8px">
                <pre style="color:#00ff9c">{''.join(logs)}</pre>
                </div>
                """,
                unsafe_allow_html=True
            )

        try:

            status_text.info("Running pipeline...")

            run_pipeline(log_callback)

            progress_bar.progress(1.0)

            status_text.success("Pipeline finished successfully")

        except Exception as e:

            st.error(f"Pipeline failed: {str(e)}")

        finally:

            st.session_state["running"] = False

# ----------------------------------------------------
# Results Page
# ----------------------------------------------------

elif page == "View Results":

    st.title("Cluster Results")

    if not result_file:
        st.warning("Resultados não encontrados. Execute a ferramenta primeiro.")
        st.stop()

    df = load_results(result_file)

    keyword = st.text_input("Search keyword")

    filtered_df = search_dataframe(df, keyword)

    st.dataframe(
        filtered_df,
        use_container_width=True
    )

    st.write(f"{len(filtered_df)} results")


# ----------------------------------------------------
# Visualization Page
# ----------------------------------------------------

elif page == "Visualizations":

    st.title("Data Visualizations")

    if not result_file:
        st.warning("Resultados não encontrados. Execute a ferramenta primeiro.")
        st.stop()

    df = load_results(result_file)

    if st.button("Load Charts"):

        fig1 = cluster_distribution(df)

        if fig1:
            st.plotly_chart(fig1, use_container_width=True)

        fig2 = trend_frequency(df)

        if fig2:
            st.plotly_chart(fig2, use_container_width=True)