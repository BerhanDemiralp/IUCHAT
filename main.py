"""Streamlit entry point wrapper - directs to app.main."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from app.main import main

if __name__ == "__main__":
    main()
