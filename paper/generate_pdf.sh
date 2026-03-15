#!/bin/bash
# generate_pdf.sh - Generate PDF from LaTeX source

cd "$(dirname "$0")"

echo "=== Generating MOSS Paper PDF ==="
echo

# Check if pdflatex is available
if ! command -v pdflatex &> /dev/null; then
    echo "Error: pdflatex not found. Please install TeX Live:"
    echo "  Ubuntu/Debian: sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended"
    echo "  macOS: brew install --cask mactex"
    echo "  Or use Overleaf: https://overleaf.com"
    exit 1
fi

echo "Step 1: First compilation..."
pdflatex -interaction=nonstopmode main.tex || true

echo
echo "Step 2: Generate bibliography (if needed)..."
if [ -f "main.aux" ]; then
    bibtex main || true
fi

echo
echo "Step 3: Second compilation..."
pdflatex -interaction=nonstopmode main.tex || true

echo
echo "Step 4: Final compilation..."
pdflatex -interaction=nonstopmode main.tex

if [ -f "main.pdf" ]; then
    echo
    echo "=== PDF Generated Successfully ==="
    echo "File: main.pdf"
    ls -lh main.pdf
    echo
    echo "You can now submit this PDF to ICLR Workshop"
else
    echo
    echo "Error: PDF generation failed. Check main.log for errors."
    exit 1
fi
