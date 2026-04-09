#!/bin/bash
# Compile MOSS Paper PDF
# Usage: ./compile_paper.sh

cd "$(dirname "$0")/../paper"

echo "Compiling MOSS Paper..."

# First pass
pdflatex -interaction=nonstopmode main.tex

# Second pass (resolve cross-references)
pdflatex -interaction=nonstopmode main.tex

# Check if successful
if [ -f "main.pdf" ]; then
    cp main.pdf MOSS_Paper_v2.0.1.pdf
    echo "Success: MOSS_Paper_v2.0.1.pdf created"
    ls -lh MOSS_Paper_v2.0.1.pdf
else
    echo "Error: Compilation failed"
    exit 1
fi
