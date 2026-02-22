import argparse
import pandas as pd

REQUIRED_CANDIDATES = ["CLEAT-C1", "CLEAT-C2"]
REQUIRED_SLOPES = [35, 45]
MIN_REPEATS = 3


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["candidate_id"] = out["candidate_id"].astype(str).str.strip().str.upper()
    out["slope_deg"] = pd.to_numeric(out["slope_deg"], errors="coerce")
    return out


def main():
    ap = argparse.ArgumentParser(description="Check validation matrix completeness")
    ap.add_argument("csv_path")
    args = ap.parse_args()

    df = pd.read_csv(args.csv_path)
    df = normalize(df)

    print("=== Matrix completeness ===")
    ok = True
    for c in REQUIRED_CANDIDATES:
        for s in REQUIRED_SLOPES:
            n = len(df[(df["candidate_id"] == c) & (df["slope_deg"] == s)])
            status = "OK" if n >= MIN_REPEATS else "MISSING"
            if n < MIN_REPEATS:
                ok = False
            print(f"{c} @ {int(s)}°: {n} runs ({status})")

    missing_cols = []
    must_have = [
        "run_id",
        "candidate_id",
        "slope_deg",
        "commanded_distance_mm",
        "progress_distance_mm",
        "mean_current_a",
        "peak_current_a",
        "input_energy_wh",
        "damage_flag",
    ]
    for col in must_have:
        if col not in df.columns:
            missing_cols.append(col)

    if missing_cols:
        ok = False
        print("\nMissing required columns:", ", ".join(missing_cols))

    if ok:
        print("\nRESULT: MATRIX_READY")
    else:
        print("\nRESULT: NOT_READY")


if __name__ == "__main__":
    main()
