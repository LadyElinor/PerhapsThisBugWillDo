PYTHON ?= python

.PHONY: bringup run_matrix report

bringup:
	@echo "[bringup] validate run schema + COTS map"
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
