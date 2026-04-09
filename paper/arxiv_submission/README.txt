# MOSS Paper - arXiv Submission

## Paper Information

**Title**: Self-Modifying Multi-Objective Optimization: State-Dependent Specialization in Autonomous Agents

**Authors**: Cash (Independent Researcher), Fuxi (MOSS Project Team)

**Categories**: cs.AI (Artificial Intelligence), cs.LG (Machine Learning), cs.MA (Multiagent Systems)

**Comments**: 8 pages, submitted to ICLR 2027 Workshop

## Abstract

We present MOSS (Multi-Objective Self-Driven System for AI Autonomous Evolution), a framework where autonomous agents dynamically evolve their objective weights through experience. The four intrinsic objectives are survival, curiosity, influence, and self-optimization. Unlike fixed-weight approaches, MOSS enables self-adjustment of goal priorities based on performance feedback and internal state (Crisis/Concerned/Normal/Growth). Through extensive long-term experiments (6-hour and 24-hour continuous operation), we demonstrate that self-modifying configurations achieve 40--460% higher cumulative reward than fixed baselines. Our key discovery is path bifurcation: identical initial conditions evolve into divergent stable strategies---social-exploration (6h) versus knowledge-seeking (24h)---depending on runtime context. Weight quantization experiments further validate that state-dependent weight allocation achieves optimal performance (0.3763 overall score). This reveals that self-modification leads not just to better performance but to adaptive, context-aware intelligence, opening new directions for open-ended autonomous learning.

## Files

- `main.tex` - LaTeX source file
- `figures/` - Directory containing 3 PNG figures
  - `fig2_performance.png` - Performance comparison
  - `fig3_path_bifurcation.png` - Path bifurcation visualization
  - `fig4_trajectories.png` - Weight evolution trajectories

## Compilation

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Code and Data Repository

https://github.com/luokaishi/moss

## Contact

moss-project@github.com

## Version History

- v1.0 (2026-03-06): Initial draft
- v2.0 (2026-03-13): Revised with real experiment data, aligned with repository

## License

MIT License (see repository for details)