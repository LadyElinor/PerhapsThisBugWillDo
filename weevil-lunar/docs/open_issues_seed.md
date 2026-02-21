# Seed Issues for External Contributors

## good first issue
1. Add tighter unit tests for contact force edge cases (negative input guards).
2. Add JSON schema constraints for all ICD fields (types/enums/ranges).
3. Improve README screenshots/diagrams for setup clarity.

## validation tasks
1. Extend parameter sweep to include density and particle-size proxy.
2. Add explicit benchmark implementation for Bekker pressure-sinkage equation.
3. Add Wong-Reece wheel baseline script with source-linked coefficients.

## roadmap items
1. Multi-leg gait planner from placeholder to executable policy.
2. Dynamic-regime simulation layer with clear assumptions.
3. Hardware-in-the-loop traceability hooks for bench datasets.

## external credibility tasks
1. feat: add Studica resource crosswalk for Earth-analog hardware prototyping (`docs/external_resources/studica.md`).
2. feat: add RobotMarketplace mechanical crosswalk for Earth-analog drivetrain prototyping (`docs/external_resources/robotmarketplace.md`).
3. docs: add evidence-tier table separating integration evidence vs physics evidence in verification reports.
4. test: create COTS bench protocol using actuator/sensor stack for controller + telemetry de-risking (explicitly non-lunar-physics evidence).
5. verification: add chain/sprocket reliability checklist with connecting-link derating and safety-factor assumptions.
