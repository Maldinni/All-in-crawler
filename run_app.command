chmod +x run_app.command

#!/bin/bash
cd "$(dirname "$0")"
streamlit run app.py

