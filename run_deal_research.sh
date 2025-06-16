#!/bin/bash
cd backend
echo "Starting Deep Deal Research application..."
streamlit run src/streamlit_app.py --server.port=8501
