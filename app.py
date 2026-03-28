import streamlit as st
import pandas as pd
from src.utils.pipeline_runner import run_pipeline, PIPELINE_STEPS
from src.utils.data_loader import load_results, search_dataframe
from src.visualizations.charts import cluster_distribution, trend_frequency

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

    st.write(
        "Run the full data pipeline to generate updated clusters and trends."
    )

    run_button = st.button("Run Pipeline")

    log_placeholder = st.empty()

    if run_button:

        logs = []

        def log_callback(message):
            logs.append(message)
            log_placeholder.markdown(
                f"```bash\n{''.join(logs)}\n```"
            )

        try:

            with st.spinner("Running pipeline..."):

                run_pipeline(log_callback)

            st.success("Pipeline completed successfully")

        except Exception as e:

            st.error(f"Pipeline failed: {str(e)}")


# ----------------------------------------------------
# Results Page
# ----------------------------------------------------

elif page == "View Results":

    st.title("Cluster Results")

    df = load_results()

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

    df = load_results()

    if st.button("Load Charts"):

        fig1 = cluster_distribution(df)

        if fig1:
            st.plotly_chart(fig1, use_container_width=True)

        fig2 = trend_frequency(df)

        if fig2:
            st.plotly_chart(fig2, use_container_width=True)