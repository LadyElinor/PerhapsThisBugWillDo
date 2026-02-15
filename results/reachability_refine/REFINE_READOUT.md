# Local Refinement Sweep (t=500)

```
cell_id  barrier_mult  access_mult temp_level  N_at_risk  prevalence  AUC_M_acc_w  AUC_dE_over_T  AUC_combined  dAUC_combined_minus_Macc  M_acc_w_median  M_acc_w_p10  M_acc_w_p90  dE_over_T_p10  dE_over_T_p90       cell_class
cell_03           1.0         0.65   baseline        100    0.460000     0.574074       0.358696      0.654992                  0.080918      144.658996   131.461336   159.274781       0.687936       0.964158 BARRIER-EMERGENT
cell_05           1.0         0.70   baseline         97    0.463918     0.555556       0.408547      0.593590                  0.038034      151.572385   131.865666   158.994571       0.688403       0.977370     TRANSITIONAL
cell_06           1.0         0.70        low         96    0.468750     0.549891       0.488889      0.586492                  0.036601      113.288663    97.683830   128.937517       0.961664       1.341148     TRANSITIONAL
cell_01           1.0         0.60   baseline         91    0.483516     0.648453       0.336557      0.666344                  0.017892      135.776350   129.439882   158.477555       0.693784       0.964263  ONSET-DOMINATED
cell_04           1.0         0.65        low        101    0.455446     0.555336       0.432411      0.560079                  0.004743      119.976034    96.635327   129.218540       0.961055       1.320950  ONSET-DOMINATED
cell_02           1.0         0.60        low        102    0.470588     0.568673       0.448688      0.566744                 -0.001929      104.650795    95.979721   127.988977       0.948443       1.295080  ONSET-DOMINATED
```

Legend: ONSET-DOMINATED (<0.02), TRANSITIONAL (0.02-0.05), BARRIER-EMERGENT (>=0.05)