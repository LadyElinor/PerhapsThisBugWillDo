# NASA-JPL Retry Queue (Prioritized)

- Source ingest failures: 79
- Recovered via targeted retry log: 11
- Remaining pending retry: 68

## Priority policy
- 3 = critical lunar-weevil relevance (DTN/comms/perception/sim/mobility/task verification).
- 2 = high architecture adjacency (rover/localization/isaacsim references).
- 1 = medium possible relevance.
- 0 = low/default.

## Top pending items

| repo | priority | reason |
|---|---:|---|
| nasa-jpl/ION-DTN | 3 | critical:ion-dtn |
| nasa-jpl/ion-core | 3 | critical:ion-core |
| nasa-jpl/landmark_tools | 2 | high:landmark |
| nasa-jpl/ACI-colorization | 0 | low:generic |
| nasa-jpl/CouchbaseSync | 0 | low:generic |
| nasa-jpl/DataDrive-Frontend | 0 | low:generic |
| nasa-jpl/DataDrive-Middleware | 0 | low:generic |
| nasa-jpl/DataDrive-Notification-Lambdas | 0 | low:generic |
| nasa-jpl/DataDrive-Thumbnail-Generator | 0 | low:generic |
| nasa-jpl/LLM_Exploration_Workflows | 0 | low:generic |
| nasa-jpl/MACOS_resources | 0 | low:generic |
| nasa-jpl/MonteCop | 0 | low:generic |
| nasa-jpl/SAAS | 0 | low:generic |
| nasa-jpl/SAWSCS-SBC | 0 | low:generic |
| nasa-jpl/ScrubView | 0 | low:generic |
| nasa-jpl/Space-Balls-MST | 0 | low:generic |
| nasa-jpl/SpaceImages-iOS | 0 | low:generic |
| nasa-jpl/TetherCAD | 0 | low:generic |
| nasa-jpl/ViewCubeHelper | 0 | low:generic |
| nasa-jpl/auto_SAR_Ocean_Contrast | 0 | low:generic |
