"""Check saved region certificates, raw force witnesses and exact scenario coverage."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import json
from pathlib import Path

import numpy as np

import support_loss_analysis as study
import support_regions as regions
import run_support_region_02 as runner
from run_support_loss_01 import check_coverage
from models.cots_support_audit import audit_allocation


def verify_region(a,b,out):
    x = np.array(out["center_body_translation_xy_m"])
    slack = out["signed_inradius_m"]
    if x.shape != (2,) or not np.isfinite([*x,slack]).all() or np.max(a @ x+slack-b) > 1e-8:
        raise ValueError("Invalid saved region primal witness")
    expected = "EMPTY" if slack < -1e-8 else ("BOUNDARY_UNRESOLVED" if slack <= 1e-8 else "NECESSARY_REGION_ONLY")
    if out["status"] != expected or out["hardware_motion_allowed"] is not False:
        raise ValueError("Invalid region status")
    if expected == "EMPTY":
        lam = np.zeros(len(a))
        seen = set()
        for term in out["empty_certificate"]["terms"]:
            i,weight = term["row"],term["weight"]
            if type(i) is not int or i not in range(len(a)) or i in seen or not np.isfinite(weight) or weight < 0:
                raise ValueError("Invalid certificate row or weight")
            seen.add(i)
            if not np.allclose(a[i],term["a"],rtol=0,atol=1e-12) or abs(b[i]-term["b"]) > 1e-12:
                raise ValueError("Certificate row differs from saved constraint")
            lam[i] = weight
        if abs(lam.sum()-1) > 1e-8 or np.linalg.norm(lam @ a) > 1e-8 or lam @ b >= -1e-8:
            raise ValueError("Invalid saved infeasibility certificate")


def check(output,compare_committed=False):
    spec,c = runner.frozen_inputs()
    report = json.loads((output/"results.json").read_text())
    if report.get("complete") is not True or report["spec_sha256"] != study.sha256(runner.SPEC):
        raise ValueError("Incomplete or changed experiment")
    if report["id"] != spec["id"] or report["frozen_inputs_sha256"] != spec["frozen_inputs_sha256"]:
        raise ValueError("Changed experiment identity or frozen inputs")
    if set(report["source_sha256"]) != {"verification/cots/run_support_region_02.py", "verification/cots/support_regions.py", "models/cots_support_audit.py"}:
        raise ValueError("Incomplete source registry")
    if set(report["artifact_sha256"]) != {"regions.json.gz", "replay.csv.gz"}:
        raise ValueError("Incomplete artifact registry")
    if not all(report["controls"].values()) or report["encoding_disagreements"] != 0:
        raise ValueError("Failed experiment controls")
    if any(report.get(key) is not False for key in runner.RELEASE):
        raise ValueError("Release flag changed")
    for name,digest in report["source_sha256"].items():
        if study.sha256(study.ROOT/name) != digest: raise ValueError(f"Changed source {name}")
    for name,digest in report["artifact_sha256"].items():
        if study.sha256(output/name) != digest: raise ValueError(f"Changed artifact {name}")
    cert = regions.mechanism_certificate(c)
    if (report["mechanism_certificate"]["closed"] != cert["closed"]
            or abs(report["mechanism_certificate"]["normal_lower_bound_n"]-cert["normal_lower_bound_n"]) > 1e-8):
        raise ValueError("Changed mechanism bound")
    poses = {(p,s):(sw,f,a) for p,s,sw,f,a in study.poses(c,{"id":"baseline"})}
    with gzip.open(output/"regions.json.gz","rt") as f: records = json.load(f)
    if len(records) != 30 or {(r["phase"],r["sample"]) for r in records} != set(poses):
        raise ValueError("Incomplete region coverage")
    for saved in records:
        swing,feet,active = poses[saved["phase"],saved["sample"]]
        if saved["swing_leg_1based"] != swing+1 or saved["active"] != list(active) or saved["feet_m"] != feet.tolist():
            raise ValueError("Changed region pose")
        a,b,tags = regions.region_constraints(c,feet,active)
        if (not np.allclose(a,saved["halfspaces_a"],atol=1e-12,rtol=0)
                or not np.allclose(b,saved["halfspaces_b"],atol=1e-12,rtol=0) or tags != saved["row_tags"]):
            raise ValueError("Changed region constraints")
        verify_region(a,b,saved["common"])
        if set(saved["per_loss"]) != {str(i+1) for i in active}: raise ValueError("Incomplete per-loss coverage")
        for lost,out in saved["per_loss"].items():
            mask = np.array([t["lost_leg_1based"] == int(lost) for t in tags])
            verify_region(a[mask],b[mask],out)
    summary = [{"phase":r["phase"],"sample":r["sample"],"common":r["common"],
                "per_loss_status":{k:v["status"] for k,v in r["per_loss"].items()}} for r in records]
    if summary != report["regions"] or dict(Counter(r["common"]["status"] for r in records)) != report["common_region_counts"]:
        raise ValueError("Misreported region summary")
    loads = {(sx,sy,gid):(com,g) for sx,sy,gid,_,_,com,g in study.load_cases(c)}
    expected = {}
    with gzip.open(study.SPEC.with_name("cases.csv.gz"),"rt") as f:
        for row in csv.DictReader(f):
            if row["variant"] == "baseline": expected[row["scenario"]] = int(row["accepted"])
    counts = Counter(nominal_cases=0,nominal_rejected=0,loss_cases=0,loss_rejected=0)
    keys, audited, phase_rejected = {}, 0, [0]*6
    with gzip.open(output/"replay.csv.gz","rt") as f:
        for row in csv.DictReader(f):
            p,s,sw,lost,sx,sy = (int(row[k]) for k in ("phase","sample","swing","lost","sx","sy"))
            gid = row["gravity"]
            swing,feet,active = poses[p,s]
            key = (sw,s,lost,sx,sy,gid)
            if sw != swing or (lost != -1 and lost not in active) or key in keys:
                raise ValueError("Invalid replay scenario")
            if row["scenario"] != "|".join(map(str,key)): raise ValueError("Mismatched scenario identity")
            keys[key] = True
            supports = active if lost == -1 else tuple(i for i in active if i != lost)
            com,g = loads[sx,sy,gid]
            allocation = json.loads(row["allocation_json"])
            audit = audit_allocation(c,feet,supports,com,g,allocation)
            if int(audit["accepted"]) != expected[row["scenario"]] or int(row["audit_accepted"]) != int(audit["accepted"]):
                raise ValueError("Saved force witness or decision changed")
            if int(row["original_accepted"]) != expected[row["scenario"]] or row["audit_reasons"] != ";".join(audit["reasons"]):
                raise ValueError("Misreported audit decision")
            audited += int(allocation["feasible"])
            family = "nominal" if lost == -1 else "loss"
            counts[family+"_cases"] += 1
            counts[family+"_rejected"] += int(not audit["accepted"])
            if lost != -1: phase_rejected[p] += int(not audit["accepted"])
    check_coverage(keys)
    if dict(counts) != report["reference_counts"] or audited != report["raw_force_witnesses_audited"]:
        raise ValueError("Misreported replay counts")
    if phase_rejected != report["phase_contingency_rejections"]:
        raise ValueError("Misreported phase counts")
    if (report["candidate_search"]["executed"] or report["complete_sampled_static_candidate_pass"]
            or report["candidate_search"]["candidate_configurations_scored"] != 0):
        raise ValueError("Unexecuted candidate promoted")
    if compare_committed:
        committed = json.loads(runner.SPEC.with_name("results.json").read_text())
        for key in ("reference_counts","phase_contingency_rejections","common_region_counts","candidate_search","raw_force_witnesses_audited"):
            if report[key] != committed[key]: raise ValueError(f"Reproduction mismatch: {key}")
        for new,old in zip(report["regions"],committed["regions"]):
            if (new["common"]["status"] != old["common"]["status"]
                    or abs(new["common"]["signed_inradius_m"]-old["common"]["signed_inradius_m"]) > 1e-8
                    or new["per_loss_status"] != old["per_loss_status"]):
                raise ValueError("Region reproduction mismatch")
    return {"verified_cases":len(keys),"verified_raw_force_witnesses":audited,"verified_regions":len(records),
            "spec":spec["id"],"hardware_motion_allowed":False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir",type=Path,required=True)
    parser.add_argument("--compare-committed",action="store_true")
    args = parser.parse_args()
    print(json.dumps(check(args.results_dir,args.compare_committed),indent=2))
