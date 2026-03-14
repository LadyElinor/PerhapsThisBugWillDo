PYTHON ?= python

.PHONY: bringup run_matrix report burrow_process gate

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
	@echo "[burrow_process] schema validation + threshold sweep + retrieval"
	$(PYTHON) verification/scripts/validate_regolith_burrow_variants.py
	$(PYTHON) verification/scripts/sweep_regolith_burrow_thresholds.py
	$(PYTHON) verification/scripts/retrieve_regolith_variant.py
	@echo "[burrow_process] done"

gate: burrow_process
	@echo "[gate] integrated gate check"
	$(PYTHON) verification/run_gate_check.py
	@echo "[gate] done"
