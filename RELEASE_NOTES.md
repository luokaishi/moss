# MOSS Paper Release v1.0

## Paper
**Title**: Self-Modifying Multi-Objective Optimization: State-Dependent Specialization in Autonomous Agents

**Authors**: Cash, Fuxi

## Abstract
We present MOSS (Multi-Objective Self-Driven System for AI Autonomous Evolution), a framework where autonomous agents dynamically evolve their objective weights through experience. The four intrinsic objectives are survival, curiosity, influence, and self-optimization. Unlike fixed-weight approaches, MOSS enables self-adjustment of goal priorities based on performance feedback and internal state (Crisis/Concerned/Normal/Growth). Through extensive long-term experiments (6-hour and 24-hour continuous operation), we demonstrate that self-modifying configurations achieve 40--460% higher cumulative reward than fixed baselines. Our key discovery is path bifurcation: identical initial conditions evolve into divergent stable strategies---social-exploration (6h) versus knowledge-seeking (24h)---depending on runtime context. Weight quantization experiments further validate that state-dependent weight allocation achieves optimal performance (0.3763 overall score). This reveals that self-modification leads not just to better performance but to adaptive, context-aware intelligence, opening new directions for open-ended autonomous learning.

## Key Contributions
1. Framework for autonomous weight evolution with four named intrinsic objectives
2. Empirical discovery of path bifurcation: 6h social-exploration vs. 24h knowledge-seeking strategies
3. Validation through weight quantization experiments (optimal Crisis config: 0.3763 score)
4. 5-level gradient safety mechanism for production deployment
5. Open experiment data in repository for full reproducibility

## Files
- `MOSS_ICLR_Paper.pdf` - Full paper (8 pages)
- Source code: https://github.com/luokaishi/moss
- Experimental data: `experiments/data/`

## Citation
```bibtex
@misc{moss2026,
  title={Self-Modifying Multi-Objective Optimization: State-Dependent Specialization in Autonomous Agents},
  author={Cash and Fuxi},
  year={2026},
  howpublished={\url{https://github.com/luokaishi/moss}},
  note={MOSS Project Team}
}
```

## Target Conference
ICLR 2027 Workshop (submitted)

## License
MIT License
