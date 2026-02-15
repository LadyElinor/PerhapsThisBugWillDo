# Fork-Point Diagnostics

- pilot: `results\reachability\physics\pilot_2026-02-14.csv`
- exits: `results\reachability\physics\exits_2026-02-14.csv`
- mode_col: `mode_key`

## Core diagnostics
- late_ratio (escape_time>1000 among hits): **0.3556** (32/90)
- flips_1000_to_10000: **32**
- fork_verdict: **mixed_or_uncertain**

## Reachability lift by policy
- anneal: 0.317 -> 0.467 (flips=9)
- greedy: 0.300 -> 0.517 (flips=13)
- tempered: 0.350 -> 0.517 (flips=10)

## Concentration (accepted-only)
- anneal: top1=0.100, top3=0.292, n=8008, unique_modes=24
- greedy: top1=0.164, top3=0.465, n=7401, unique_modes=8
- tempered: top1=0.114, top3=0.304, n=9478, unique_modes=24

## Concentration (accessible-only)
- anneal: top1=0.079, top3=0.231, n=14884, unique_modes=24
- greedy: top1=0.164, top3=0.465, n=7401, unique_modes=8
- tempered: top1=0.100, top3=0.264, n=14424, unique_modes=24

## Concentration (weighted by accepted_weight)
- anneal: top1_w=0.097, top3_w=0.284, w_total=8101.500, unique_modes=24
- greedy: top1_w=0.164, top3_w=0.465, w_total=7401.000, unique_modes=8
- tempered: top1_w=0.115, top3_w=0.306, w_total=9389.031, unique_modes=24

