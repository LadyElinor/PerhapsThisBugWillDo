import argparse
import pandas as pd


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'slip_distance_mm' not in df or df['slip_distance_mm'].isna().all():
        df['slip_distance_mm'] = df['commanded_distance_mm'] - df['progress_distance_mm']
    if 'slip_ratio_pct' not in df or df['slip_ratio_pct'].isna().all():
        df['slip_ratio_pct'] = (df['slip_distance_mm'] / df['commanded_distance_mm'].replace(0, pd.NA)) * 100.0
    if 'progress_eff_mm_per_wh' not in df or df['progress_eff_mm_per_wh'].isna().all():
        df['progress_eff_mm_per_wh'] = df['progress_distance_mm'] / df['input_energy_wh'].replace(0, pd.NA)
    return df


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    grp = (
        df.groupby(['candidate_id', 'slope_deg'], dropna=False)
        .agg(
            runs=('run_id', 'count'),
            mean_slip_pct=('slip_ratio_pct', 'mean'),
            mean_current_a=('mean_current_a', 'mean'),
            mean_eff_mm_per_wh=('progress_eff_mm_per_wh', 'mean'),
            damage_rate=('damage_flag', lambda s: (s.astype(str).str.upper() == 'Y').mean()),
            nonpositive_progress_rate=('progress_distance_mm', lambda s: (s <= 0).mean()),
        )
        .reset_index()
    )
    return grp


def pooled_metrics(df: pd.DataFrame) -> pd.DataFrame:
    pooled = (
        df.groupby('candidate_id', dropna=False)
        .agg(
            runs=('run_id', 'count'),
            pooled_mean_slip_pct=('slip_ratio_pct', 'mean'),
            pooled_mean_current_a=('mean_current_a', 'mean'),
            pooled_mean_eff_mm_per_wh=('progress_eff_mm_per_wh', 'mean'),
            damage_rate=('damage_flag', lambda s: (s.astype(str).str.upper() == 'Y').mean()),
            nonpositive_progress_count=('progress_distance_mm', lambda s: int((s <= 0).sum())),
        )
        .reset_index()
    )
    return pooled


def decision(pooled: pd.DataFrame) -> str:
    c1 = pooled[pooled['candidate_id'] == 'CLEAT-C1']
    c2 = pooled[pooled['candidate_id'] == 'CLEAT-C2']
    if c1.empty or c2.empty:
        return 'INSUFFICIENT_DATA: need both CLEAT-C1 and CLEAT-C2 runs.'

    c1 = c1.iloc[0]
    c2 = c2.iloc[0]

    slip_improvement_rel = (c2['pooled_mean_slip_pct'] - c1['pooled_mean_slip_pct']) / c2['pooled_mean_slip_pct'] if c2['pooled_mean_slip_pct'] else pd.NA
    current_delta_rel = (c1['pooled_mean_current_a'] - c2['pooled_mean_current_a']) / c2['pooled_mean_current_a'] if c2['pooled_mean_current_a'] else pd.NA
    eff_delta_rel = (c1['pooled_mean_eff_mm_per_wh'] - c2['pooled_mean_eff_mm_per_wh']) / c2['pooled_mean_eff_mm_per_wh'] if c2['pooled_mean_eff_mm_per_wh'] else pd.NA

    stop = (
        c1['nonpositive_progress_count'] >= 2 and c2['nonpositive_progress_count'] >= 2
    )
    if stop:
        return 'STOP: non-positive progress repeated across both candidates.'

    go = (
        c1['pooled_mean_slip_pct'] <= 25
        and pd.notna(slip_improvement_rel) and slip_improvement_rel >= 0.15
        and pd.notna(current_delta_rel) and current_delta_rel <= 0.10
        and pd.notna(eff_delta_rel) and eff_delta_rel >= 0.0
        and c1['damage_rate'] == 0
    )
    if go:
        return 'CONTINUE: keep CLEAT-C1 baseline.'

    return 'PIVOT: move to CLEAT-C2 baseline or retune + rerun.'


def main():
    parser = argparse.ArgumentParser(description='Quick validation analysis for CLEAT-C1 vs CLEAT-C2')
    parser.add_argument('input_csv', help='Path to filled logging CSV')
    parser.add_argument('--out-prefix', default='validation_summary', help='Output prefix for summary files')
    args = parser.parse_args()

    df = pd.read_csv(args.input_csv)
    df = add_derived(df)

    by_slope = summarize(df)
    pooled = pooled_metrics(df)

    by_slope_out = f"{args.out_prefix}_by_slope.csv"
    pooled_out = f"{args.out_prefix}_pooled.csv"

    by_slope.to_csv(by_slope_out, index=False)
    pooled.to_csv(pooled_out, index=False)

    print('\n=== By slope summary ===')
    print(by_slope.to_string(index=False))
    print('\n=== Pooled summary ===')
    print(pooled.to_string(index=False))

    print('\n=== Decision ===')
    print(decision(pooled))


if __name__ == '__main__':
    main()
