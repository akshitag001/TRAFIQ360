import pandas as pd
import numpy as np
import os

csv_path = r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
output_report_path = r"C:\Users\Akshit aggarwal\.gemini\antigravity-ide\brain\ecc1739f-3df3-4ee0-9068-c356b4b61b90\eda_report.md"

print("Loading dataset for deep EDA...")
df = pd.read_csv(csv_path)

# Prepare dates
df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
df['closed_datetime'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
df['resolved_datetime'] = pd.to_datetime(df['resolved_datetime'], errors='coerce')

# Parse hours and day of week
df['hour'] = df['start_datetime'].dt.hour
df['dow'] = df['start_datetime'].dt.dayofweek
df['is_weekend'] = df['dow'].isin([5, 6]).astype(int)

# Peak hour classification
# Peak: 19:00-22:00 (7-10 PM) and 05:00-07:00 (5-7 AM)
def get_peak_class(h):
    if (h >= 19 and h <= 22) or (h >= 4 and h <= 7):
        return 'Peak'
    elif (h >= 7 and h <= 10) or (h >= 17 and h <= 19):
        return 'Semi-Peak'
    else:
        return 'Off-Peak'
df['peak_period'] = df['hour'].apply(get_peak_class)

# Calculate duration
df['resolution_mins'] = (df['closed_datetime'] - df['start_datetime']).dt.total_seconds() / 60.0
df.loc[df['resolution_mins'].isna(), 'resolution_mins'] = (df['resolved_datetime'] - df['start_datetime']).dt.total_seconds() / 60.0
# Clean durations (replace negative and extremely small values with median or small positive numbers, clip outliers)
df.loc[df['resolution_mins'] < 0, 'resolution_mins'] = np.nan
median_dur = df['resolution_mins'].median()
df['resolution_mins'] = df['resolution_mins'].fillna(median_dur)

# Calculate Composite Impact Score
# Base severity for causes
CAUSE_SEV = {
    'public_event': 7.0, 'vip_movement': 8.0, 'protest': 7.5, 'procession': 6.5,
    'construction': 5.5, 'accident': 6.0, 'tree_fall': 5.5, 'water_logging': 5.0,
    'road_conditions': 4.5, 'congestion': 5.5, 'vehicle_breakdown': 3.0, 'pot_holes': 3.5,
    'Debris': 4.0, 'debris': 4.0, 'others': 3.0, 'Fog / Low Visibility': 4.0, 'test_demo': 1.0
}

# Calculate base impact score
df['requires_road_closure_bool'] = df['requires_road_closure'].astype(str).str.lower().str.strip() == 'true'
df['priority_high_bool'] = df['priority'].astype(str).str.lower().str.strip() == 'high'

def compute_row_impact(row):
    cause = row['event_cause']
    base = CAUSE_SEV.get(cause, 3.0)
    
    # Modifiers
    closure_add = 2.0 if row['requires_road_closure_bool'] else 0.0
    priority_add = 1.0 if row['priority_high_bool'] else 0.0
    
    # Peak hour multiplier
    h = row['hour']
    pm = 1.3 if ((h >= 19 and h <= 22) or (h >= 4 and h <= 7)) else (1.15 if ((h >= 7 and h <= 10) or (h >= 17 and h <= 19)) else 1.0)
    
    # Duration factor log-scaled
    dur = row['resolution_mins']
    dur_factor = min(1.5, np.log10(dur + 1) * 0.3)
    
    score = (base + closure_add + priority_add) * pm + dur_factor
    return min(10.0, max(1.0, round(score, 1)))

df['calculated_impact_score'] = df.apply(compute_row_impact, axis=1)

# Generate detailed EDA statistics
total_events = len(df)
missing_counts = df.isna().sum()
missing_pcts = (missing_counts / total_events) * 100

# Top corridors
corridor_stats = df.groupby('corridor').agg(
    count=('id', 'count'),
    avg_impact=('calculated_impact_score', 'mean'),
    closure_rate=('requires_road_closure_bool', 'mean'),
    median_duration=('resolution_mins', 'median')
).reset_index().sort_values(by='count', ascending=False)

# Top causes
cause_stats = df.groupby('event_cause').agg(
    count=('id', 'count'),
    avg_impact=('calculated_impact_score', 'mean'),
    closure_rate=('requires_road_closure_bool', 'mean'),
    median_duration=('resolution_mins', 'median')
).reset_index().sort_values(by='count', ascending=False)

# Top hotspots (junctions)
junction_stats = df[df['junction'].notna()].groupby('junction').agg(
    count=('id', 'count'),
    avg_impact=('calculated_impact_score', 'mean'),
    closure_rate=('requires_road_closure_bool', 'mean'),
    latitude=('latitude', 'mean'),
    longitude=('longitude', 'mean')
).reset_index().sort_values(by='count', ascending=False).head(30)

# Temporal patterns
hourly_stats = df.groupby('hour').agg(
    count=('id', 'count'),
    avg_impact=('calculated_impact_score', 'mean')
).reset_index()

dow_stats = df.groupby('dow').agg(
    count=('id', 'count'),
    avg_impact=('calculated_impact_score', 'mean')
).reset_index()

# Zone statistics
zone_stats = df[df['zone'].notna()].groupby('zone').agg(
    count=('id', 'count'),
    avg_impact=('calculated_impact_score', 'mean'),
    closure_rate=('requires_road_closure_bool', 'mean')
).reset_index().sort_values(by='count', ascending=False)

# Write report
with open(output_report_path, 'w', encoding='utf-8') as f:
    f.write("# Exploratory Data Analysis (EDA) Report - TRAFIQ360\n\n")
    f.write("Generated for the Event-Driven Congestion Command Hackathon.\n\n")
    
    f.write("## 1. Dataset Overview\n")
    f.write(f"- **Total Records**: {total_events}\n")
    f.write(f"- **Planned Events**: {len(df[df['event_type'] == 'planned'])} ({len(df[df['event_type'] == 'planned'])/total_events*100:.2f}%)\n")
    f.write(f"- **Unplanned Events**: {len(df[df['event_type'] == 'unplanned'])} ({len(df[df['event_type'] == 'unplanned'])/total_events*100:.2f}%)\n")
    f.write(f"- **Requires Road Closure**: {len(df[df['requires_road_closure_bool'] == True])} ({len(df[df['requires_road_closure_bool'] == True])/total_events*100:.2f}%)\n")
    f.write(f"- **High Priority Events**: {len(df[df['priority_high_bool'] == True])} ({len(df[df['priority_high_bool'] == True])/total_events*100:.2f}%)\n\n")
    
    f.write("## 2. Missing Values Analysis\n")
    f.write("| Column | Missing Count | Missing Percentage |\n")
    f.write("|---|---|---|\n")
    for col in df.columns:
        if missing_counts[col] > 0:
            f.write(f"| {col} | {missing_counts[col]} | {missing_pcts[col]:.2f}% |\n")
    f.write("\n")
    
    f.write("## 3. Event Cause Breakdown\n")
    f.write("| Cause | Count | Percentage | Avg Impact | Closure Rate | Median Duration (min) |\n")
    f.write("|---|---|---|---|---|---|\n")
    for _, row in cause_stats.iterrows():
        pct = (row['count'] / total_events) * 100
        f.write(f"| {row['event_cause']} | {row['count']} | {pct:.2f}% | {row['avg_impact']:.2f} | {row['closure_rate']*100:.1f}% | {row['median_duration']:.1f} |\n")
    f.write("\n")
    
    f.write("## 4. Corridor Congestion Analysis\n")
    f.write("| Corridor | Count | Percentage | Avg Impact | Closure Rate | Median Duration (min) |\n")
    f.write("|---|---|---|---|---|---|\n")
    for _, row in corridor_stats.iterrows():
        pct = (row['count'] / total_events) * 100
        f.write(f"| {row['corridor']} | {row['count']} | {pct:.2f}% | {row['avg_impact']:.2f} | {row['closure_rate']*100:.1f}% | {row['median_duration']:.1f} |\n")
    f.write("\n")
    
    f.write("## 5. Temporal Patterns\n")
    f.write("### Hourly Event Distribution\n")
    f.write("| Hour | Count | Percentage | Avg Impact |\n")
    f.write("|---|---|---|---|\n")
    for _, row in hourly_stats.iterrows():
        pct = (row['count'] / total_events) * 100
        f.write(f"| {int(row['hour']):02d}h | {row['count']} | {pct:.2f}% | {row['avg_impact']:.2f} |\n")
    f.write("\n")
    
    f.write("### Day of Week Event Distribution\n")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    f.write("| Day | Count | Percentage | Avg Impact |\n")
    f.write("|---|---|---|---|\n")
    for _, row in dow_stats.iterrows():
        pct = (row['count'] / total_events) * 100
        f.write(f"| {days[int(row['dow'])]} | {row['count']} | {pct:.2f}% | {row['avg_impact']:.2f} |\n")
    f.write("\n")
    
    f.write("## 6. Hotspot Junctions (Top 30)\n")
    f.write("| Junction | Count | Avg Impact | Closure Rate | Latitude | Longitude |\n")
    f.write("|---|---|---|---|---|---|\n")
    for _, row in junction_stats.iterrows():
        f.write(f"| {row['junction']} | {row['count']} | {row['avg_impact']:.2f} | {row['closure_rate']*100:.1f}% | {row['latitude']:.6f} | {row['longitude']:.6f} |\n")
    f.write("\n")

    f.write("## 7. Zone Distribution\n")
    f.write("| Zone | Count | Avg Impact | Closure Rate |\n")
    f.write("|---|---|---|---|\n")
    for _, row in zone_stats.iterrows():
        f.write(f"| {row['zone']} | {row['count']} | {row['avg_impact']:.2f} | {row['closure_rate']*100:.1f}% |\n")
    f.write("\n")

print("EDA analysis completed. Report saved to eda_report.md.")
