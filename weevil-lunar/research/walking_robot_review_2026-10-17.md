# Walking-robot research for Lunar Weevil

Review date: **2026-10-17**. Status: **research and source audit only; proposed experiments unexecuted**.

## Decision

Prioritize **robust, load-constrained COM and foothold planning**, followed by explicit contact-state uncertainty and calibrated actuator modelling. Public walking demonstrations do not establish that any borrowed mechanism or controller meets Weevil's complete sampled support-loss requirement.

The most relevant methods are Jet-leg's feasible-region construction and its reachable-region extension. SpiderBot, ODRI/Solo, HEBI Daisy and MiniRHex provide useful mechanism, calibration or control examples. Hugging Face policies provide reproducibility examples and possible future simulator baselines; none of the reviewed policies is a Weevil controller.

This note is separate from CAD and geometric-interface work. It changes no checker, engineering limit, frozen result, motion authorization or fabrication status.

## Existing evidence that determines priority

The [completed investigation](../verification/cots/support_loss_01/README.md) at commit `d1f9cc12d106134c5c47d6d52e4bcb0169bcac80` reproduced 1,080 nominal passes and 2,925 contingency rejections. Of those rejections, 1,076 are impossible under unilateral support geometry alone; another 1,849 already contradict equilibrium plus the 300 N normal cap. All 2,160 same-side missing-leg-pair cases fail. These are sampled mathematical results, not failure probabilities.

The declared common-sway/reach/stride/order family is already closed by its necessary-condition bound: even its favorable witness requires at least 356.65 N on one foot. None of the external sources invalidates that bound. Reopening the family with a new controller name or reward function would not address the contradiction.

## Available projects and useful transfers

| Project | Verified availability and evidence | Useful transfer to Weevil | Boundary |
|---|---|---|---|
| [Jet-leg](https://github.com/orsoromeo/jet-leg) and [Improved Feasible Region](https://github.com/abdelrahman-h-abdalla/jet-leg) | Python repositories; original force-constraint implementation inspected. The [original paper](https://arxiv.org/abs/1903.07999v3) addresses force/torque feasibility; the [extension](https://arxiv.org/abs/2011.07967v2) adds reachable COM regions and reports HyQ/Aliengo experiments. | Compute where the COM may be while retaining force, torque and reach limits. Intersect those regions across every additional foot loss. | Quadruped-oriented code needs a six-leg adaptation and an exact constraint audit. Its published guarantees apply to its assumptions. |
| [SpiderBot](https://github.com/ERC-BPGC/SpiderBot) | CAD/STEP, closed-linkage MuJoCo assets, training and deployment code, policies. [Authors' preprint](https://arxiv.org/html/2609.26989v1) reports a 3 kg, two-DOF-per-leg spring-assisted hexapod with hardware trials. | Study passive gravity compensation and model linkage closure explicitly. | Springs can reduce actuator effort; they do not erase total ground reaction or the 300 N cap. Reduced foot-placement freedom may be harmful here. |
| [ODRI/Solo hardware](https://github.com/open-dynamic-robot-initiative/open_robot_actuator_hardware) | Modular actuator, leg, robot and calibration designs; [paper](https://arxiv.org/abs/1910.00093v2) reports torque/impedance characterization. | Adopt traceable joint-zero conventions, actuator models and independent leg-force validation requirements. | A small quadruped's demonstrated actuator performance does not scale directly to a 60 kg prototype. Physical validation remains future work. |
| [HEBI Daisy ROS example](https://github.com/HebiRobotics/hebi-ros-daisy) | Public hexapod C++ code; foot-force allocation and leg-torque code inspected. | Separate body motion, gait state, stance-load transfer, gravity compensation and feedback timestamps. | Inspected load sharing is heuristic, not Weevil's constrained equilibrium admission test. The example targets ROS Melodic/Ubuntu 18.04. |
| [MiniRHex](https://github.com/robomechanics/MiniRHex) | Chassis/leg designs, gait software and documented spring characteristics for a small compliant hexapod. | Examine compliance as an explicit mechanical parameter, including its effect on effective contact location. | Compliant locomotion is not evidence of bounded static support-loss feasibility; its contact model differs substantially. |
| [legged_control / OCS2](https://github.com/qiayuanl/legged_control) | NMPC, whole-body control and estimation code; WBC constraints inspected. | Separate task objectives from hard physical constraints, and keep contact forces visible in diagnostics. | The README says the project is unsupported. Its four-leg assumptions and friction formulation require changes; it is an architectural reference. |
| [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie) | Curated robot models, per-model provenance/licensing and model checks. | Use its model/scene separation and validation practices for a future independent Weevil simulator. | The maintainers explicitly describe model fidelity as ongoing work. A model that loads is not physical validation. |
| [Go2 policy on Hugging Face](https://huggingface.co/diasAiMaster/unitree-go2-velocity-flat) | Model card, ONNX/PyTorch artifacts, deployment/environment/agent configurations and logs listed. | Bundle observation ordering, action scaling, joint mapping and training configuration with every future policy. | Flat-terrain quadruped simulation results; no reviewed evidence for Weevil or its contingency gate. |

The [source manifest](walking_robot_sources_2026-10-17.json) pins eight GitHub revisions, the main Hugging Face model revision, and inspected file blob hashes. It records which papers were inspected only at abstract level. No third-party software or policy was executed.

## Concrete findings from code inspection

### 1. Borrow the feasible-region method, preserve Weevil's mathematics

At [Jet-leg's inspected revision](https://github.com/orsoromeo/jet-leg/blob/532d2b218690e73b3f15d4f3c160c977a92c43ba/jet_leg/constraints/constraints.py):

- Contact arrays and Jacobian handling assume four legs.
- The four-face friction implementation bounds each tangential component separately.
- Normal-force saturation is optional and defaults off in the inspected helper.
- The inspected actuation-polygon calculation sets leg-gravity terms to zero with a TODO.

Weevil retains six-leg kinematics, its conservative leg-gravity torque bound, and explicit force caps. Its friction condition is `abs(Fx) + abs(Fy) <= mu * Fz`. The componentwise form `abs(Fx) <= mu * Fz; abs(Fy) <= mu * Fz` allows additional diagonal forces.

For example, with mu = 0.5, F = (0.5, 0.5, 1) passes the componentwise inequalities but fails Weevil's inequality. This is an algebraic counterexample, not an executed robot experiment. A matching coefficient does not make the cones equivalent.

### 2. Keep an independent acceptance check outside the optimizer

[legged_control's WBC](https://github.com/qiayuanl/legged_control/blob/a7f381c0367e98e31c01336e678eef47e304d40d/legged_wbc/src/WbcBase.cpp) separates torque/contact constraints from tracking objectives, but uses the componentwise friction form and quadruped-specific torque-limit sizing. Its [weighted solver function](https://github.com/qiayuanl/legged_control/blob/a7f381c0367e98e31c01336e678eef47e304d40d/legged_wbc/src/WeightedWbc.cpp) retrieves the primal solution without checking the solver return values in that function.

Use the separation of objectives and constraints as a reference. Retain Weevil's independent residual, unilateral-force, normal-load, friction, torque, COP and stability checks, including fail-closed handling of solver indeterminacy.

### 3. Mechanism and simulator defaults can change the claimed problem

[SpiderBot's actuator/contact configuration](https://github.com/ERC-BPGC/SpiderBot/blob/dd4ebe38aa3a9b2603c30fb9267f3b5d07e79381/src/mjlab/asset_zoo/robots/spiderbot/spiderbot_constants.py) includes actuator delays and explicit effort limits. It also selects foot-only collisions, six-dimensional contacts and sliding friction 1.0. These are useful modelling examples, not compatible replacements for Weevil's frozen friction/contact assumptions or separate clearance checks.

The authors report lower standing power with springs, but higher locomotion energy cost and limited obstacle clearance. For Weevil, spring assistance is a secondary actuator/energy study: the current baseline contradictions already arise before torque constraints are needed.

### 4. Timed load transfer is not confirmed support

[Daisy's load allocation](https://github.com/HebiRobotics/hebi-ros-daisy/blob/1b1247c7d1052591b3f3f9788ba9ab8a8b93b702/src/robot/hexapod.cpp) blends a leg's assigned load near the scheduled beginning and end of a step. Its [leg model](https://github.com/HebiRobotics/hebi-ros-daisy/blob/1b1247c7d1052591b3f3f9788ba9ab8a8b93b702/src/robot/leg.cpp) separately calculates stance, link-gravity and spring/drag contributions.

Transfer that modular decomposition, while keeping commanded stance distinct from confirmed usable contact. A clock reaching touchdown is not sufficient evidence that a foot supports load.

### 5. Calibrated geometry matters before controller sophistication

ODRI documents [joint-zero/index calibration](https://github.com/open-dynamic-robot-initiative/open_robot_actuator_hardware/blob/66af1522b4fba0ec4a1d7790e66f5e4652208d30/mechanics/general/robot_calibration.md) and a [single-leg test stand](https://github.com/open-dynamic-robot-initiative/open_robot_actuator_hardware/blob/66af1522b4fba0ec4a1d7790e66f5e4652208d30/mechanics/leg_test_stand_v2/README.md) with independent six-axis force measurement.

The transferable requirement is to identify joint offsets, compliance, force/current calibration and model error. Future bench evidence would be needed to substantiate those quantities. This review authorizes no bench operation or fabrication.

## Promising literature that is not yet an available implementation here

[SPINDER](https://www.nature.com/articles/s41598-026-56856-0) reports hardware gait experiments with contact switches, an IMU and hierarchical CPG/IK control. However, its paper says CAD/URDF/control software *will* be released, and contact-loss detection/fault-tolerant reorganization is future work. A public implementation was not verified in this review. Retain its separation of rhythmic timing from Cartesian trajectory generation as an architectural idea, not a validated recovery method.

[Fault Tolerant Free Gait and Footstep Planning](https://arxiv.org/abs/2006.07550v2) jointly plans gait and foothold sequences using MCTS for sparse footholds. The primary abstract supports looking beyond a fixed cyclic order, but no usable public implementation was verified. Its fault/environment model must be compared explicitly with arbitrary loss during an existing swing.

A second [Hugging Face policy collection](https://huggingface.co/Kyu3224/quadruped-locomotion-policy) specifies robot-dependent observation/action dimensions for Hound quadrupeds. That illustrates why a downloadable walking policy is not morphology-independent. No reviewed model card establishes all-support-loss coverage.

## Prioritized next offline experiments

These are proposed experiments, **not a new preregistered scored search**. Exact candidate bounds, seeds/budget and numerical tolerances must be committed before execution.

1. **Construct robust feasible COM regions for the current mechanism.** For each stance, intersect the admissible COM sets for every additional supporting-foot loss and every frozen gravity direction. Require the original COM uncertainty samples to remain inside; retain the existing 40 mm margin as a separate condition. Intersect with reachable body poses and the inherited engineering envelope.

   The key quantifier is one pre-loss body pose and foot arrangement that works for every possible additional loss. Separate COM solutions chosen after learning which foot failed do not meet this requirement. Contact-force witnesses may differ across loss cases; their existence still does not prove a realizable transient.

2. **Search independently placed footholds and a compatible body path.** If the robust region is nonempty, use per-leg targets within the existing joint/reach, pad-clearance and 400 mm shaft-arm envelope. This is a different family from the rejected common-translation variants. Select targets by worst-case feasibility/slack, then check a complete progressing periodic gait and all sampled transfers. Do not change hip interfaces in this stage.

   Recompute Jacobians and torque constraints as the body configuration changes. A locally feasible projected region is not automatically valid for a distant posture. A finite search that finds nothing establishes no global impossibility unless accompanied by a valid bound.

3. **Audit contact and model uncertainty offline.** Add simulated/replayed stale feedback, false touchdown, delayed contact, slip indication, joint-zero error and compliance perturbations. Uncertain contacts must not silently enlarge the usable support set. These tests evaluate software decisions; they do not validate a physical detector or recovery controller.

4. **Only then evaluate mechanism alternatives.** If mechanically reachable configurations remain infeasible, open a separately specified architecture study of different support placement or an additional support already carrying load before loss. Include its mass, force path, contact constraints and every applicable new loss case. Do not assume a support can be deployed after failure. Spring assistance and compliance can be compared for effort/energy, but cannot serve as proof against the existing force-balance bound.

A lower COM may reduce slope-induced moment, but does not resolve an ordinary support-polygon failure on flat ground by itself. Reduced mass or stronger actuators would change the frozen design problem and cannot count as success under this investigation's acceptance criteria.

## Acceptance and controls for any subsequent comparison

Retain the 60 kg Earth-prototype model, load factor 1.3, 300 N normal cap, 43.2 Nm torque limit, mu = 0.5 with the original friction pyramid, 40 mm stability margin and 70 mm usable COP radius. Preserve all inherited kinematic and structural limits.

- Reproduce the frozen baseline before candidate scoring.
- Require every one of the original 1,080 nominal and 5,400 contingency scenarios to pass, matched by physical swing leg, lost leg, gait position, COM corner and gravity direction.
- Require complete sampled transition coverage, valid joints, clearance, velocity and periodic continuity. New phases/supports require additional coverage; never remove original scenarios to improve the score.
- Preserve geometric, insufficient-normal-cap, zero-friction and near-zero-torque negative controls. Add the friction-convention counterexample and false-contact fixture when testing an imported formulation.
- Record rescued and regressed scenarios, minimum margins, peak normal/torque utilization, runtime, solver status and independent witness residuals.
- Freeze an additional boundary-focused validation set before candidate selection. Passing either finite set establishes sampled static feasibility only.

**Stop condition:** reject an individual pose on a proven necessary-condition contradiction. Close a bounded candidate family only when its specified search or valid analytical bound warrants that conclusion. Do not infer arbitrary-redesign impossibility from this review.

## Work status

**Completed:** primary-source discovery, eight GitHub revision pins, inspection of selected constraint/control/mechanical documentation, two Hugging Face model-card reviews, and mapping to the existing Weevil failures.

**Not established:** any externally sourced design that meets Weevil's complete contingency requirement; any validated support-loss detector; any dynamic recovery or lunar-soil performance.

**Unexecuted:** all newly proposed COM-region searches, foothold/body-path searches, external controller/model builds, policy rollouts, dynamic simulation, physical testing and mechanism changes. The earlier support-loss experiment results remain frozen and unchanged.

This is a targeted research selection, not an exhaustive catalogue. Source availability and a repository-level license do not by themselves establish permission to reuse every asset; inspect the applicable file/asset terms before copying.
