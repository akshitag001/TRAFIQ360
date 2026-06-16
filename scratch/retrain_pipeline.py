"""
scratch/retrain_pipeline.py
Merges original dataset with approved feedback and retrains models.
"""
import os
import sys
import json
import uuid
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, roc_auc_score
import xgboost as xgb
import lightgbm as lgb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
FEEDBACK_XLSX = os.path.join(BASE_DIR, "data", "post_event_feedback.xlsx")
REGISTRY_PATH = os.path.join(MODEL_DIR, "model_registry.json")

CAUSE_SEV = {
    'public_event': 7.0, 'vip_movement': 8.0, 'protest': 7.5, 'procession': 6.5,
    'construction': 5.5, 'accident': 6.0, 'tree_fall': 5.5, 'water_logging': 5.0,
    'road_conditions': 4.5, 'congestion': 5.5, 'vehicle_breakdown': 3.0,
    'pot_holes': 3.5, 'Debris': 4.0, 'debris': 4.0, 'others': 3.0,
    'Fog / Low Visibility': 4.0, 'test_demo': 1.0
}


def load_registry():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH, "r") as f:
            return json.load(f)
    return {"versions": []}


def save_registry(reg):
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2)


def get_current_version(reg):
    if not reg["versions"]:
        return "v1.0"
    active = [v for v in reg["versions"] if v.get("is_active")]
    if active:
        ver = active[-1]["version"]
    else:
        ver = reg["versions"][-1]["version"]
    # Bump minor version
    parts = ver.lstrip("v").split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return "v" + ".".join(parts)


def _compute_impact(row):
    cause = row.get('event_cause', 'others')
    base = CAUSE_SEV.get(str(cause), 3.0)
    closure_add = 2.0 if str(row.get('requires_road_closure', '')).lower() == 'true' else 0.0
    priority_add = 1.0 if str(row.get('priority', '')).lower() == 'high' else 0.0
    h = int(row.get('hour', 12))
    pm = 1.3 if ((h >= 19) or (h <= 7)) else (1.15 if (7 <= h <= 10 or 17 <= h <= 19) else 1.0)
    dur = float(row.get('resolution_mins', 60))
    dur_factor = min(1.5, np.log10(dur + 1) * 0.3)
    return min(10.0, max(1.0, round((base + closure_add + priority_add) * pm + dur_factor, 1)))


def retrain(progress_callback=None):
    """
    Main retraining function. Returns summary dict.
    progress_callback(pct, message) — optional progress reporter.
    """
    def progress(pct, msg):
        if progress_callback:
            progress_callback(pct, msg)
        print(f"[{pct}%] {msg}")

    progress(5, "Loading original dataset...")
    df_orig = pd.read_csv(CSV_PATH)
    orig_count = len(df_orig)

    # ── Preprocessing original ──────────────────────────────────────────────
    df_orig['start_datetime'] = pd.to_datetime(df_orig['start_datetime'], errors='coerce')
    df_orig['closed_datetime'] = pd.to_datetime(df_orig['closed_datetime'], errors='coerce')
    df_orig['resolved_datetime'] = pd.to_datetime(df_orig['resolved_datetime'], errors='coerce')
    df_orig['hour'] = df_orig['start_datetime'].dt.hour.fillna(12).astype(int)
    df_orig['dow'] = df_orig['start_datetime'].dt.dayofweek.fillna(0).astype(int)
    for col in ['event_cause', 'corridor', 'zone', 'junction', 'event_type', 'priority']:
        df_orig[col] = df_orig[col].fillna('Unknown')
    df_orig['resolution_mins'] = (df_orig['closed_datetime'] - df_orig['start_datetime']).dt.total_seconds() / 60.0
    median_dur = df_orig['resolution_mins'].median()
    df_orig['resolution_mins'] = df_orig['resolution_mins'].fillna(median_dur)
    df_orig.loc[df_orig['resolution_mins'] < 0, 'resolution_mins'] = median_dur
    df_orig['requires_road_closure_bool'] = df_orig['requires_road_closure'].astype(str).str.lower().str.strip() == 'true'
    df_orig['requires_road_closure'] = df_orig['requires_road_closure_bool'].astype(str)
    df_orig['calculated_impact_score'] = df_orig.apply(_compute_impact, axis=1)
    df_orig['requires_road_closure_target'] = df_orig['requires_road_closure_bool'].astype(int)
    cause_means = df_orig.groupby('event_cause')['calculated_impact_score'].mean().to_dict()
    df_orig['historical_severity'] = df_orig['event_cause'].map(cause_means)

    # ── Load approved feedback ───────────────────────────────────────────────
    feedback_count = 0
    df_combined = df_orig.copy()

    if os.path.exists(FEEDBACK_XLSX):
        import openpyxl
        progress(15, "Loading approved feedback records...")
        df_fb = pd.read_excel(FEEDBACK_XLSX)
        approved = df_fb[df_fb['approval_status'] == 'Approved'].copy()
        feedback_count = len(approved)

        if feedback_count > 0:
            # Build synthetic training rows from feedback
            fb_rows = []
            for _, row in approved.iterrows():
                fb_rows.append({
                    'event_cause': row.get('event_cause', 'others'),
                    'corridor': row.get('corridor', 'Unknown'),
                    'zone': 'Unknown',
                    'junction': row.get('junction', 'Unknown'),
                    'hour': 12,
                    'dow': 0,
                    'event_type': row.get('event_type', 'unplanned'),
                    'priority': 'High' if float(row.get('actual_impact', 5)) >= 7 else 'Low',
                    'historical_severity': float(row.get('actual_impact', 5)),
                    'resolution_mins': float(row.get('actual_duration', 60)),
                    'calculated_impact_score': float(row.get('actual_impact', 5)),
                    'requires_road_closure_target': 1 if row.get('road_closure_actual', False) else 0,
                })
            df_fb_rows = pd.DataFrame(fb_rows)
            df_combined = pd.concat([
                df_orig[list(df_fb_rows.columns)],
                df_fb_rows
            ], ignore_index=True)

    total_samples = len(df_combined)
    progress(25, f"Dataset merged: {orig_count} original + {feedback_count} feedback = {total_samples} total")

    # ── Encode features ──────────────────────────────────────────────────────
    progress(30, "Encoding categorical features...")
    categorical_cols = ['event_cause', 'corridor', 'zone', 'junction', 'event_type', 'priority']
    label_encoders = {}
    for col in categorical_cols:
        df_combined[col] = df_combined[col].astype(str).fillna('Unknown')
        le = LabelEncoder()
        df_combined[col] = le.fit_transform(df_combined[col])
        label_encoders[col] = le

    joblib.dump(label_encoders, os.path.join(MODEL_DIR, 'label_encoders.joblib'))
    joblib.dump(cause_means, os.path.join(MODEL_DIR, 'cause_means.joblib'))

    features = ['event_cause', 'corridor', 'zone', 'junction', 'hour', 'dow',
                'event_type', 'priority', 'historical_severity']
    X = df_combined[features]
    y_impact = df_combined['calculated_impact_score']
    y_dur = df_combined['resolution_mins']
    y_cls = df_combined['requires_road_closure_target']

    X_train, X_test, yi_train, yi_test = train_test_split(X, y_impact, test_size=0.2, random_state=42)
    _, _, yd_train, yd_test = train_test_split(X, y_dur, test_size=0.2, random_state=42)
    _, _, yc_train, yc_test = train_test_split(X, y_cls, test_size=0.2, random_state=42)

    # ── Train models ─────────────────────────────────────────────────────────
    progress(40, "Training Impact Score model (XGBoost)...")
    xgb_imp = xgb.XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
    xgb_imp.fit(X_train, yi_train)
    imp_rmse = float(np.sqrt(mean_squared_error(yi_test, xgb_imp.predict(X_test))))
    joblib.dump(xgb_imp, os.path.join(MODEL_DIR, 'best_impact_model.joblib'))

    progress(60, "Training Duration model (XGBoost)...")
    xgb_dur = xgb.XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
    xgb_dur.fit(X_train, np.log1p(yd_train))
    dur_rmse = float(np.sqrt(mean_squared_error(yd_test, np.expm1(xgb_dur.predict(X_test)))))
    joblib.dump(xgb_dur, os.path.join(MODEL_DIR, 'best_duration_model.joblib'))

    progress(80, "Training Closure model (LightGBM)...")
    lgb_cls = lgb.LGBMClassifier(n_estimators=100, random_state=42, verbose=-1)
    lgb_cls.fit(X_train, yc_train)
    try:
        cls_auc = float(roc_auc_score(yc_test, lgb_cls.predict_proba(X_test)[:, 1]))
    except Exception:
        cls_auc = 0.0
    joblib.dump(lgb_cls, os.path.join(MODEL_DIR, 'best_closure_model.joblib'))

    # ── Update model registry ─────────────────────────────────────────────────
    progress(90, "Updating model registry...")
    reg = load_registry()
    for v in reg["versions"]:
        v["is_active"] = False
    new_version = get_current_version(reg)
    reg["versions"].append({
        "version": new_version,
        "trained_at": datetime.now().isoformat(),
        "original_samples": orig_count,
        "feedback_samples": feedback_count,
        "total_samples": total_samples,
        "impact_rmse": round(imp_rmse, 4),
        "duration_rmse": round(dur_rmse, 4),
        "closure_auc": round(cls_auc, 4),
        "is_active": True,
    })
    save_registry(reg)

    progress(100, f"Retraining complete. New model: {new_version}")
    return {
        "success": True,
        "version": new_version,
        "original_samples": orig_count,
        "feedback_samples": feedback_count,
        "total_samples": total_samples,
        "impact_rmse": round(imp_rmse, 4),
        "duration_rmse": round(dur_rmse, 4),
        "closure_auc": round(cls_auc, 4),
    }


if __name__ == "__main__":
    result = retrain()
    print(json.dumps(result, indent=2))
