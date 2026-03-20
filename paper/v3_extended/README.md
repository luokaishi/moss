# MOSS v3.1.0 Paper

**Title**: From Society to Self: Self-Generated Purpose in Autonomous Systems

**Authors**: Cash, Fuxi

**Target Venue**: NeurIPS 2027

## Quick Links

- **Main Paper**: [paper_v31_draft.tex](./paper_v31_draft.tex)
- **References**: [references.bib](./references.bib)
- **Figures**: [figures/](./figures/)
- **Supplementary**: [supplementary/](./supplementary/)
- **NeurIPS Checklist**: [NEURIPS_SUBMISSION_CHECKLIST.md](./NEURIPS_SUBMISSION_CHECKLIST.md)

## Abstract

We present MOSS v3.1, extending the Multi-Objective Self-Driven System from 8 to 9 dimensions to explore the emergence of self-generated meaning in autonomous agents. v3.1 introduces **Purpose** (D9): the capacity for agents to generate their own answers to "Why do I exist?" 

**Key Results**:
- Purpose Divergence: 4 types from identical starts
- Purpose Stability: 0.9977 (1k steps), 100% (10k steps)
- Purpose Fulfillment: +26.66% satisfaction
- D9 Validation: +632% adaptation improvement

## Paper Structure

1. **Introduction** - Self-generated meaning in AI
2. **Related Work** - 5 subsections, 40+ citations
3. **Method** - 9D architecture, Purpose Generator
4. **Experiments** - 4 hypotheses + D9 validation
5. **Discussion** - Functionalism, AI Safety
6. **Conclusion** - Future work

## Compiling PDF

### Option 1: Local LaTeX
```bash
pdflatex paper_v31_draft.tex
bibtex paper_v31_draft
pdflatex paper_v31_draft.tex
pdflatex paper_v31_draft.tex
```

### Option 2: Overleaf
1. Download this folder as ZIP
2. Upload to [overleaf.com](https://overleaf.com)
3. Compile with pdfLaTeX

## Status

- [x] Paper draft complete
- [x] 40+ references added
- [x] 5 figures ready
- [x] Supplementary materials prepared
- [ ] PDF compiled ⏳
- [ ] NeurIPS 2027 CFP released ⏳

## Citation

```bibtex
@software{moss_v31_2026,
  title={MOSS v3.1.0: Self-Generated Purpose in Autonomous Systems},
  author={Cash and Fuxi},
  year={2026},
  url={https://github.com/luokaishi/moss}
}
```
