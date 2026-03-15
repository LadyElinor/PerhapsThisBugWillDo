PYTHON ?= python

.PHONY: bringup run_matrix report burrow_process bench_ingest bench_calibrate reasoning_rigor copilot gate

bringup:
	@echo "[bringup] validate run schema + COTS map"
	$(PYTHON) bench/validate_run_config.py bench/example_runs/v0.2_smoke.yaml
	$(PYTHON) verification/check_cots_interface_map.py
	@echo "[bringup] done"

run_matrix:
	@echo "[run_matrix] validate experiment matrix exists"
	$(PYTHON) -c "import pathlib; p=pathlib.Path('experiments/v0.2_alpha_matrix.yaml'); print('OK' if p.exists() else 'MISSING')"
	@echo "[run_matrix] (placeholder) execute bench runner here"

report:
	@echo "[report] regenerate export receipt + checks"
	$(PYTHON) cad/scripts/generate_export_receipt.py --interface-version v0.4 --cots-profile-id rm-v1 --notes "v0.2 report regeneration"
	$(PYTHON) verification/check_export_receipt.py --receipt cad/exports/latest/export_receipt_v0.4.json --max-age-days 30
	$(PYTHON) verification/check_cots_interface_map.py
	@echo "[report] done"

burrow_process:
	@echo "[burrow_process] schema + sweep + retrieval + eval + selection"
	$(PYTHON) verification/scripts/validate_regolith_burrow_variants.py
	$(PYTHON) verification/scripts/sweep_regolith_burrow_thresholds.py
	$(PYTHON) verification/scripts/retrieve_regolith_variant.py
	$(PYTHON) verification/scripts/evaluate_regolith_burrow_variants.py
	$(PYTHON) verification/scripts/select_regolith_variant.py --mission-intent adaptive --runtime-energy-reserve 0.30 --runtime-component-temp-c 62
	@echo "[burrow_process] done"

bench_ingest:
	@echo "[bench_ingest] ingest minimal hardware trial template"
	$(PYTHON) verification/scripts/ingest_minimal_hardware_trials.py
	@echo "[bench_ingest] done"

bench_calibrate:
	@echo "[bench_calibrate] fit bench-to-model parameters + error/trend/tuning artifacts"
	$(PYTHON) verification/calibration/fit_bench_to_model.py
	$(PYTHON) verification/calibration/check_bench_model_error.py
	$(PYTHON) verification/calibration/trend_bench_model_error.py
	$(PYTHON) verification/calibration/suggest_threshold_tuning.py
	@echo "[bench_calibrate] done"

reasoning_rigor:
	@echo "[reasoning_rigor] run competing hypotheses + uncertainty checks"
	$(PYTHON) verification/scripts/check_competing_hypotheses.py
	$(PYTHON) verification/scripts/check_uncertainty_ledger.py
	@echo "[reasoning_rigor] done"

copilot:
	@echo "[copilot] run verification copilot scan + trend update"
	$(PYTHON) verification/copilot/run_copilot.py --stale-days 14 --max-weighted-score 10 --suppressions verification/copilot/suppressions.yaml
	$(PYTHON) verification/copilot/update_trend.py
	$(PYTHON) verification/copilot/check_trend.py
	@echo "[copilot] done"

gate: burrow_process bench_ingest bench_calibrate reasoning_rigor copilot
	@echo "[gate] integrated gate check"
	$(PYTHON) verification/check_traceability_namespace.py
	$(PYTHON) verification/run_gate_check.py
	@echo "[gate] done"
