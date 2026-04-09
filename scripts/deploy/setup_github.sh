#!/bin/bash
# GitHub Repository Setup Script for MOSS
# Run this after creating the repository on GitHub

echo "=========================================="
echo "MOSS GitHub Repository Setup"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "README_GITHUB.md" ]; then
    echo "Error: Please run this script from the moss/ directory"
    exit 1
fi

# Copy the GitHub README to main README
cp README_GITHUB.md README.md
echo "[1/5] Copied README for GitHub"

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
    echo "[2/5] Initialized git repository"
else
    echo "[2/5] Git already initialized"
fi

# Add all files
git add .
echo "[3/5] Added files to git"

# Initial commit
git commit -m "Initial commit: MOSS framework with 5 validated experiments

- Multi-objective self-driven system implementation
- 5 simulation experiments validating the framework
- ICLR 2027 workshop submission paper
- Documentation and examples

Authors: Cash, Fuxi (equal contribution)"

echo "[4/5] Created initial commit"

# Instructions for connecting to GitHub
echo ""
echo "=========================================="
echo "Next Steps:"
echo "=========================================="
echo ""
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo ""
echo "2. Name it: moss (or your preferred name)"
echo ""
echo "3. Do NOT initialize with README (we already have one)"
echo ""
echo "4. Connect and push:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/moss.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "5. Add repository metadata on GitHub:"
echo "   - Description: Multi-Objective Self-Driven System for AI Autonomous Evolution"
echo "   - Topics: ai, artificial-intelligence, autonomous-agents, multi-objective-optimization, self-driven-ai"
echo "   - Website: (optional) link to paper or demo"
echo ""
echo "=========================================="
