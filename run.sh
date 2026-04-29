#!/bin/bash
# Quick-start: use the project venv and launch the Streamlit app
DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$DIR"
"$DIR/.venv/bin/streamlit" run "$DIR/app.py" --server.port 8501
