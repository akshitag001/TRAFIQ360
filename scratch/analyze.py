import pandas as pd
import numpy as np
import json
import os

csv_path = r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"

print("Loading dataset...")
df = pd.read_csv(csv_path)

print(f"Total rows: {len(df)}")
print("\nColumns:")
print(df.columns.tolist())

# Event Cause Counts
print("\nTop 15 Event Causes:")
cause_counts = df['event_cause'].value_counts(dropna=False)
print(cause_counts.head(15))

# Event Type Counts
print("\nEvent Types:")
type_counts = df['event_type'].value_counts(dropna=False)
print(type_counts)

# Corridor Counts
print("\nTop 15 Corridors:")
corridor_counts = df['corridor'].value_counts(dropna=False)
print(corridor_counts.head(15))

# Parse datetimes
df['start_datetime'] = pd.to_datetime(df['start_datetime'], errors='coerce')
df['closed_datetime'] = pd.to_datetime(df['closed_datetime'], errors='coerce')
df['resolved_datetime'] = pd.to_datetime(df['resolved_datetime'], errors='coerce')

df['hour'] = df['start_datetime'].dt.hour
df['dow'] = df['start_datetime'].dt.dayofweek

# Hourly counts
print("\nEvents by Hour of Day:")
print(df['hour'].value_counts().sort_index())

# Check how duration is distributed
# Use resolved_datetime or closed_datetime minus start_datetime
df['resolution_mins'] = (df['closed_datetime'] - df['start_datetime']).dt.total_seconds() / 60.0
# If closed is null, try resolved
df.loc[df['resolution_mins'].isna(), 'resolution_mins'] = (df['resolved_datetime'] - df['start_datetime']).dt.total_seconds() / 60.0

print("\nResolution Time Stats (minutes):")
print(df['resolution_mins'].describe())

# Median resolution time by cause
print("\nMedian Resolution Time (minutes) by Cause:")
print(df.groupby('event_cause')['resolution_mins'].median().sort_values(ascending=False))

# Road closure rate by cause
print("\nRoad Closure Rate by Cause:")
df['requires_road_closure_bool'] = df['requires_road_closure'].astype(str).str.lower().str.strip() == 'true'
print(df.groupby('event_cause')['requires_road_closure_bool'].mean().sort_values(ascending=False))

# Junction hotspots
print("\nTop 15 Junctions:")
print(df['junction'].value_counts().head(15))

# Zone distribution
print("\nZone Distribution:")
print(df['zone'].value_counts())

# Check coordinates
print("\nCoordinate Stats:")
print(df[['latitude', 'longitude']].describe())
