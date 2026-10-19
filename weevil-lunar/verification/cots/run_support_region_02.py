"""Execute the preregistered support-region study in a new output directory."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import gzip
import io
import json
from pathlib import Path
import platform

import numpy as np
import scipy

import support_loss_analysis as study
import support_regions as regions
from run_support_loss_01 import check_coverage
from models.cots_support_audit import ContactEvidence, assess_support_evidence, audit_allocation

SPEC = Path(__file__).with_name("support_region_02") / "spec.json"
RELEASE = {"hardware_motion_allowed": False, "fabrication_released": False,
           "dynamic_recovery_proven": False, "automatic_recovery_allowed": False}


def frozen_inputs():
    spec = json.loads(SPEC.read_text())
    for name, expected in spec["frozen_inputs_sha256"].items():
        if study.sha256(study.ROOT / name) != expected:
            raise ValueError(f"Frozen input changed: {name}")
    return spec, study.frozen_inputs()[1]


def write_gzip(path, value):
    with path.open("wb") as raw, gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0) as gz:
        gz.write((json.dumps(value,separators=(",",":"),allow_nan=False)+"\n").encode())


def controls(c):
    a = np.array([[1.,0.],[-1.,0.],[0.,1.],[0.,-1.]])
    first, second = np.array([-.2,1.,1.,1.]), np.array([1.,-.2,1.,1.])
    common = regions.solve_region(np.vstack([a,a]),np.r_[first,second])
    obs = [ContactEvidence(True,True,False,0.)]*6
    contact_ok = assess_support_evidence(c,tuple(range(6)),obs)
    obs[0] = ContactEvidence(True,False,False,0.)
    contact_bad = assess_support_evidence(c,tuple(range(6)),obs)
    import copy
    relaxed = copy.deepcopy(c)
    relaxed["com_uncertainty_xy_m"] = [0.,0.]
    checks = {
        "positive_region": regions.solve_region(a,np.ones(4))["status"] == "NECESSARY_REGION_ONLY",
        "per_loss_nonempty_but_common_empty": all(regions.solve_region(a,b)["status"] == "NECESSARY_REGION_ONLY" for b in (first,second)) and common["status"] == "EMPTY",
        "checked_empty_region_dual": common["empty_certificate"]["combined_rhs_m"] < 0,
        "relaxed_flat_mechanism_not_falsely_closed": not regions.mechanism_certificate(relaxed,0.)["closed"],
        "fresh_synthetic_contact_positive": contact_ok["evidence_sufficient_for_offline_analysis"],
        "unconfirmed_touchdown_denied": not contact_bad["evidence_sufficient_for_offline_analysis"],
        "no_hardware_release": not contact_ok["hardware_motion_allowed"],
    }
    checks.update(study.controls(c))
    if not all(checks.values()):
        raise ValueError(f"Failed controls: {checks}")
    return checks


def run(output):
    if output.exists():
        raise ValueError("Refusing existing output directory")
    spec, c = frozen_inputs()
    check = controls(c)
    certificate = regions.mechanism_certificate(c)
    output.mkdir(parents=True)
    sources = [Path(__file__), Path(regions.__file__), study.ROOT / "models/cots_support_audit.py"]
    report = {"id": spec["id"], "complete": False, "spec_sha256": study.sha256(SPEC),
              "frozen_inputs_sha256": spec["frozen_inputs_sha256"],
              "source_sha256": {str(p.relative_to(study.ROOT)):study.sha256(p) for p in sources},
              "runtime": {"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__},
              "controls":check, "mechanism_certificate":certificate, **RELEASE}
    (output / "checkpoint.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print("mechanism bound",certificate["normal_lower_bound_n"],"N; closed",certificate["closed"],flush=True)
    region_records = []
    poses = list(study.poses(c,{"id":"baseline"}))
    for phase,sample,swing,feet,active in poses:
        a,b,tags = regions.region_constraints(c,feet,active)
        common = regions.solve_region(a,b,tags)
        separate = {}
        for lost in active:
            mask = np.array([t["lost_leg_1based"] == lost+1 for t in tags])
            separate[str(lost+1)] = regions.solve_region(a[mask],b[mask],[t for t,keep in zip(tags,mask) if keep])
        region_records.append({"phase":phase,"sample":sample,"swing_leg_1based":swing+1,
            "feet_m":feet.tolist(),"active":list(active),"common":common,"per_loss":separate,
            "halfspaces_a":a.tolist(),"halfspaces_b":b.tolist(),"row_tags":tags})
        if sample == 4:
            print("common regions phase",phase,"complete",flush=True)
    write_gzip(output / "regions.json.gz",region_records)
    report["regions"] = [{"phase":r["phase"],"sample":r["sample"],"common":r["common"],
                          "per_loss_status":{k:v["status"] for k,v in r["per_loss"].items()}} for r in region_records]
    expected = {}
    with gzip.open(study.SPEC.with_name("cases.csv.gz"),"rt") as f:
        for row in csv.DictReader(f):
            if row["variant"] == "baseline": expected[row["scenario"]] = bool(int(row["accepted"]))
    counts = Counter(nominal_cases=0,nominal_rejected=0,loss_cases=0,loss_rejected=0)
    phase_rejected = [0]*6
    audited_witnesses, keys, disagreements = 0, {}, 0
    fields = ["scenario","phase","sample","swing","lost","sx","sy","gravity","original_accepted","audit_accepted","audit_reasons","allocation_json"]
    with (output / "replay.csv.gz").open("wb") as raw, gzip.GzipFile(filename="",mode="wb",fileobj=raw,mtime=0) as gz:
        with io.TextIOWrapper(gz,encoding="utf-8",newline="") as handle:
            writer = csv.DictWriter(handle,fieldnames=fields,lineterminator="\n")
            writer.writeheader()
            for phase,sample,swing,feet,active in poses:
                for lost in (-1,*active):
                    supports = active if lost == -1 else tuple(i for i in active if i != lost)
                    for sx,sy,gid,_,_,com,gravity in study.load_cases(c):
                        key = (swing,sample,lost,sx,sy,gid)
                        scenario = "|".join(map(str,key))
                        if key in keys: raise ValueError("Duplicate replay scenario")
                        out = study.case_result(c,feet,supports,com,gravity)
                        allocation = out["allocation"]
                        audit = audit_allocation(c,feet,supports,com,gravity,allocation)
                        if out["accepted"] != expected[scenario] or audit["accepted"] != out["accepted"]:
                            disagreements += 1
                            raise ValueError(f"Frozen baseline/auditor disagreement: {scenario}: {audit}")
                        audited_witnesses += int(allocation["feasible"])
                        family = "nominal" if lost == -1 else "loss"
                        counts[family+"_cases"] += 1
                        counts[family+"_rejected"] += int(not audit["accepted"])
                        if lost != -1: phase_rejected[phase] += int(not audit["accepted"])
                        keys[key] = True
                        writer.writerow({"scenario":scenario,"phase":phase,"sample":sample,"swing":swing,"lost":lost,
                            "sx":sx,"sy":sy,"gravity":gid,"original_accepted":int(out["accepted"]),
                            "audit_accepted":int(audit["accepted"]),"audit_reasons":";".join(audit["reasons"]),
                            "allocation_json":json.dumps(allocation,separators=(",",":"),allow_nan=False)})
                if sample == 4: print("reference replay phase",phase,"complete",flush=True)
    check_coverage(keys)
    if (counts != {"nominal_cases":1080,"nominal_rejected":0,"loss_cases":5400,"loss_rejected":2925}
            or phase_rejected != spec["stage_c"]["expected_phase_rejections"]):
        raise ValueError("Reference counts changed")
    report.update(reference_counts=dict(counts),phase_contingency_rejections=phase_rejected,
                  raw_force_witnesses_audited=audited_witnesses,encoding_disagreements=disagreements,
                  common_region_counts=dict(Counter(r["common"]["status"] for r in region_records)))
    report["candidate_search"] = {"executed":False,"candidate_configurations_scored":0,
        "status":"UNEXECUTED_BY_NECESSARY_GATE" if certificate["closed"] else "UNEXECUTED_NO_CANDIDATE_REGISTRY",
        "reason":"No eligible foot placement within the fixed-height/orientation family can meet the cap" if certificate["closed"] else "Necessary gate alone does not specify a candidate search"}
    report["unexecuted_scope"] = spec["unexecuted_scope"]
    report["complete_sampled_static_candidate_pass"] = False
    report["complete"] = True
    report["artifact_sha256"] = {p.name:study.sha256(p) for p in (output/"regions.json.gz",output/"replay.csv.gz")}
    (output / "results.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (output / "checkpoint.json").unlink()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    run(parser.parse_args().output)
