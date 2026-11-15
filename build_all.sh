#!/usr/bin/env bash
# Rebuild every generated file: 3D models, printable STLs, circuit diagrams, viewer.
set -e
pip install -r requirements.txt
python hardware/cad/build_models.py
python hardware/cad/schematics.py
python hardware/cad/preview.py
python hardware/cad/build_viewer.py
