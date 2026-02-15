# Phase Trace Readout (t=500, 120 seeds/cell)

## baseline
               cell_id  T_level  anneal_T  tempered_T  access_mult  N_at_risk  prevalence  AUC_M_acc_w  AUC_dE_over_T  AUC_M_plus_dE     dAUC            class  dE_over_T_p10  dE_over_T_p90
cell_01_baseline_a0.63 baseline       0.9         1.2         0.63        199    0.422111     0.564286       0.434783       0.566563 0.002277  onset-dominated       0.686249       0.973111
cell_02_baseline_a0.64 baseline       0.9         1.2         0.64        203    0.453202     0.611927       0.368782       0.641696 0.029769  onset-dominated       0.691595       0.973627
cell_03_baseline_a0.65 baseline       0.9         1.2         0.65        202    0.425743     0.558841       0.396552       0.630513 0.071672 barrier-emergent       0.686222       0.970016
cell_04_baseline_a0.66 baseline       0.9         1.2         0.66        206    0.456311     0.494491       0.487652       0.523176 0.028685  onset-dominated       0.690277       0.977161
peak_access=0.65, peak_dAUC=0.0717
accesses_dAUC>=0.03: [0.65]
accesses_dAUC>=0.05: [0.65]

## high
           cell_id T_level  anneal_T  tempered_T  access_mult  N_at_risk  prevalence  AUC_M_acc_w  AUC_dE_over_T  AUC_M_plus_dE      dAUC           class  dE_over_T_p10  dE_over_T_p90
cell_05_high_a0.66    high      1.05         1.4         0.66        200    0.430000     0.612709       0.366585       0.635047  0.022338 onset-dominated       0.596656       0.851730
cell_06_high_a0.67    high      1.05         1.4         0.67        199    0.482412     0.537116       0.450597       0.550566  0.013451 onset-dominated       0.600268       0.855374
cell_07_high_a0.68    high      1.05         1.4         0.68        208    0.408654     0.610426       0.368819       0.630033  0.019608 onset-dominated       0.599723       0.853015
cell_08_high_a0.69    high      1.05         1.4         0.69        201    0.398010     0.554236       0.444112       0.553926 -0.000310 onset-dominated       0.600414       0.854814
peak_access=0.66, peak_dAUC=0.0223
accesses_dAUC>=0.03: []
accesses_dAUC>=0.05: []
