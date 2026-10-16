# COTS-1 acceptance and release gates

The analytical baseline is complete enough to review component choices and construct a restrained interface/leg experiment. **Whole-rover fabrication and walking release are still open.** Passing software checks does not close physical gates, and a newly written acceptance target is not a test result.

| Gate | Required evidence and pass criterion | Present status |
|---|---|---|
| A1: geometry and static model | Valid IK/FK, finite-difference Jacobian, force/moment conservation, infeasible-support rejection; 1,944 baseline cases feasible with configured margins | Automated |
| A2: packaging exchange | Valid solids; STEP reimport preserves solid count and volume; no sampled actuator/frame/equipment intersections | Automated, limited collision scope |
| M1: material and mass | Certificates meet tube ≥240 MPa and shaft ≥900 MPa yield; actual gross mass ≤60 kg and COM within measured/configured bounds; ≥5% unallocated mass before optional payload | Open |
| M2: complete mechanical drawings | Bearing fits/retention, aligned torque coupler, all fasteners, motor/ATI adapters, gimbal stops, cable routing, park stops and chassis joints reviewed; detailed assembled CAD has no unintended swept collisions | Open |
| M3: motor interface coupons | Fit both coupons to the actual ordered motor without forcing; verify bolt-circle orientation, pilot, engagement and cable clearance; no fastener bottoms out | Open |
| M4: restrained leg proof | Fixture applies representative combined loads covering 300 N normal and friction-pyramid lateral loads; recorded motor/fixture torques stay within caps; zero permanent deformation, fastener slip, sensor bypass or bearing binding after unloading | Open |
| M5: drive thermal/holding behavior | Incremental joint tests to worst required working hold; temperatures remain below supplier limits and stabilize (<1°C rise over final 10 min of a ≥60 min hold); no torque/current fault, drift or thermal derating; repeat at declared ambient | Open |
| E1: voltage and regeneration | Scope motor bus during startup, reversal, battery/bench disconnect and E-stop; never exceed selected driver's operating limits; resistor pulse and average temperatures within manufacturer limits; confirm response if clamp loses input or trips | Open |
| E2: power and source | Measured bus current ≤16 A steady operating budget, within pack transient specification; auxiliary output ≤100.8 W with ambient derating and no brownouts; measure usable energy above 34 V | Open |
| C1: calibration and signs | Independently measured joint signs, switch homes and hard limits; ATI wrench transformed to foot frame and checked with known weights/levers; gravity-compensated contact force error ≤5% or 5 N, whichever is larger, over test range | Open |
| C2: fault response | Inject stale CAN, dropped Ethernet, wrong calibration, source sag and host crash while restrained; observe configured 40/100 ms detectors and documented actuator/contactor response; no reliance on untested motor watchdog | Open |
| L1: landing shoes | Guided, guarded drops with incremental ballast through the 55.90 J worst-case energy screen; confirm real peak reactions within designed frame/guide limits, damper stroke reserve, no side binding or tipping; prove mechanical park-stop load path | Open |
| W1: flat-floor gait | 100 full cycles at measured mass, then 10 min continuous; no unintended support loss, cap violation, cable snag or measured foot slip >5 mm; independent catch remains slack during normal gait | Open |
| W2: slope progression | Repeat W1 at 2° then 5°, in longitudinal and diagonal directions; measured contact forces and friction remain within model envelope; 10° only after model update and separate test approval | Open |
| S1: soil and anchoring | Controlled substrate depth, density and particle distribution; independently measured sinkage/slip and extraction forces; fit on training data and validate held-out trials | Open; no old traction model promoted |
| Q1: lunar article | Separate mass architecture, vacuum lubrication/material selection, thermal-vacuum cycles, dust endurance, radiation and launch/vibration qualification | Outside this ground-prototype release |

M4 must use a fixture capable of applying coupled forces without driving a joint beyond its commanded torque rating. Structural overload proof, if required, is performed with appropriately blocked/supporting fixtures and a reviewed load case; do not use the motor itself to apply an unspecified overload. Review the ATI combined-load envelope before applying a proof wrench.

For M5, 48 Nm catalog rating is not proof of stationary thermal endurance at 36 V. If the worst working hold cannot be sustained, reduce gross mass/load envelope or change the actuator/reduction and regenerate the design. Do not increase the software cap to hide a failure.

For L1, energy capacity alone does not set peak deceleration. Obtain the damper force-stroke curve or measure it on a fixture and size the landing mounts to the resulting peak loads before a complete rover drop. Keep the overhead catch until the response is independently demonstrated. A slope or uneven surface can cause one shoe to contact first; no all-four equal-load assumption is permitted.

## Test data and progression

Use a restrained single-leg rig first: three motors, six support bearings, one calibrated ATI system, the chosen source/clamp hardware and independent force/torque instrumentation. Capture timestamped joint commands/feedback, calibrated six-axis force, bus voltage/current, temperatures, contactor state and fixture displacement. Record source revisions, firmware, calibration serials, ambient conditions, operator and configuration hash. Retain raw data as well as summaries; a missing channel or dropped record is a failed/incomplete run, not a zero.

Only after interface, structural, thermal and power tests pass should six-leg fabrication be released. Commission the assembled machine on a hard floor, then controlled granular soil. Lunar-gravity offloading changes weight but does not make Earth-gravity soil or consumer components lunar-qualified.

The source analysis, drawings and tests in this change are new engineering evidence. They leave the earlier `DECISION_MEMO.md` soil/anchor stop gates intact. No purchase or vendor communication is part of this design change.
