import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PIPELINE_STEPS = [
    ("Step 1 — Scraping", PROJECT_ROOT / "scraper.py"),
    ("Step 2 — Cleaning", PROJECT_ROOT / "cleaner.py"),
    ("Step 3 — Embedding", PROJECT_ROOT / "embedder.py"),
    ("Step 4 — H5 Conversion", PROJECT_ROOT / "h5_converter.py"),
    ("Step 5 — Graph Construction", PROJECT_ROOT / "graph_construction.py"),
    ("Step 6 — Community Detection", PROJECT_ROOT / "community_detection.py"),
    ("Step 7 — Organzing Clusters", PROJECT_ROOT / "organizer.py"),
    ("Step 8 — Cluster Definition", PROJECT_ROOT / "cluster_definition.py"),
    ("Step 9 — Cluster Distinction", PROJECT_ROOT / "cluster_distinction.py"),
    ("Step 10 — Trend Extraction", PROJECT_ROOT / "extract_trends.py"),
    ("Step 11 — Dimension Assessment", PROJECT_ROOT / "assess_dimensions.py"),
]


def run_pipeline(log_callback):

    for step_name, script_path in PIPELINE_STEPS:

        script_path = str(script_path)

        log_callback(f"\n===== {step_name} =====\n")
        log_callback(f"Running: {script_path}\n\n")

        process = subprocess.Popen(
            [sys.executable, "-u", script_path],  # -u = unbuffered
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # STREAM EM TEMPO REAL
        for line in iter(process.stdout.readline, ''):
            log_callback(line)

        process.stdout.close()
        process.wait()

        if process.returncode != 0:
            raise RuntimeError(f"Pipeline failed at {step_name}")

        log_callback(f"\n{step_name} completed\n")