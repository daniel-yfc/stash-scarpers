#!/usr/bin/env python3
"""Backward-compatible entry point for the safeguard control suite."""

import runpy

runpy.run_path("tools/self_evaluate.py", run_name="__main__")
