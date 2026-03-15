# Bench Model Error Check

- max force MAE (N): 1.2
- max slip MAE (mm): 0.5
- max stiffness MAE (N/mm): 0.4
- max force CI95 (N): 2.0
- max slip CI95 (mm): 1.0
- max stiffness CI95 (N/mm): 0.65
- calibrated grouped models: 3
- calibrated strategy fallbacks: 3
- status: **PASS**

| group | n | force MAE | slip MAE | stiffness MAE | force CI95 | slip CI95 | stiffness CI95 | pass |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| S0|R1|T_NOMINAL | 3 | 0.022222 | 0.022222 | 0.244444 | 0.032667 | 0.032667 | 0.397407 | True |
| S1|R1|T_NOMINAL | 3 | 0.022222 | 0.022222 | 0.311111 | 0.032667 | 0.032667 | 0.51027 | True |
| S2|R2|T_NOMINAL | 3 | 0.022222 | 0.0 | 0.377778 | 0.032667 | 0.0 | 0.62324 | True |
