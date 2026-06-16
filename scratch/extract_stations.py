import pandas as pd
import json

csv_path = r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360\Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
df = pd.read_csv(csv_path)

if 'police_station' in df.columns:
    print("Found 'police_station' column!")
    # Group by police_station and get mean lat/lon
    grouped = df.groupby('police_station').agg({
        'latitude': 'mean',
        'longitude': 'mean',
        'event_type': 'count'
    }).reset_index()
    # Filter out entries without valid coords
    grouped = grouped.dropna(subset=['latitude', 'longitude'])
    # Sort by event count descending
    grouped = grouped.sort_values(by='event_type', ascending=False)
    
    stations = []
    for idx, row in grouped.head(15).iterrows():
        stations.append({
            'name': row['police_station'],
            'lat': round(row['latitude'], 6),
            'lon': round(row['longitude'], 6),
            'count': int(row['event_type'])
        })
    print(json.dumps(stations, indent=2))
else:
    print("Columns available:", list(df.columns))
