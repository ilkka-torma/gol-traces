# Game of Life traces

These Python scripts accompany the manuscript "Gardens of Eden in the Game of Life" ([arXiv version](https://arxiv.org/abs/1912.00692)) by Ville Salo and Ilkka Törmä.

Let **X** be the set of binary configurations on the upper half-plane that evolve into the all-0 configuration in one application of the the Game of Life.
It is defined by local rules: every 3×3 sub-pattern must evolve into 0 in one step.
The (one-sided height-2) trace of **X** is the set of infinite horizontal rows of height 2 that occur at the bottom of its configurations.
The radius-**r** trace is the overapproximation to the true trace where the local rule is only checked in the **r+2** bottom rows.
The **p**-periodic radius-**r** trace is the underapproximation to the true trace where the configuration is required to be vertically **p**-periodic everywhere except for the **r+2** bottom rows.

The trace and these approximations are completely defined by the sets of finite patterns that can occur in them, and in the case of the approximations, these sets form regular languages.
The script `sft-traces.py` computes the finite automata corresponding to the radius-4 trace and the 3-periodic radius-3 trace of **X**, and verifies that they are equal.
Hence they also equal the true trace.
The results of the manuscript are based on this fact.

The script `check-ext.py` verifies that all 2×6 patterns occur in the radius-1 trace of **X**.
We use this fact in the proof of one of the auxiliary results (Lemma 5).


# Usage

The scripts are written in pure Python 3 and use no external libraries.
Run them from the command line as

```
python sft-traces.py
python check-ext.py
```