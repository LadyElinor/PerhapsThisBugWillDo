# ONSET_HAZARD_READOUT

Scope: physics, at-risk set, anneal+tempered, x=log(M_acc_w+1e-12), L2-logit + quantile-bin monotonic check.

## Conclusion (3 lines)
- beta_hat is positive at all probes: t250=3.710, t500=5.566, t1000=5.275.
- AUC stays above chance at all probes: t250=0.563, t500=0.616, t1000=0.625.
- Binned escape rates increase with x in each probe, supporting an onset-accessibility law.

## Compact table
```
 t_probe  N_at_risk  prevalence  beta_hat  beta_se  beta_ci95_lo  beta_ci95_hi      AUC  delta_AUC_vs_0.5 monotonic_bins_escape_rate
     250        117    0.589744  3.710042 2.250408     -0.813417      8.307685 0.563104          0.063104   0.54,0.52,0.61,0.61,0.67
     500        100    0.520000  5.565749 2.612852      0.681259     10.707446 0.616186          0.116186   0.40,0.30,0.60,0.70,0.60
    1000         69    0.304348  5.274784 3.362480     -1.294202     12.155702 0.625000          0.125000   0.21,0.36,0.15,0.36,0.43
```

## Implication for regime sweep
- Use this as baseline; search for settings where ΔE/T adds incremental AUC beyond log(M_acc_w).
