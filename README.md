# Prostorni Indeksi (Spatial Indexes) - F1 telemetry & track simulator

A small Python project to visualize F1 telemetry on a real track, split the track into microsectors (using DuckDB spatial), and evaluate incident danger levels. The simulator scales local telemetry coordinates to track GeoJSON coordinates and animates car positions on an interactive Matplotlib map (TkAgg) with a basemap from `contextily`.

## Features
- Load and scale telemetry and accident datasets to a GeoJSON track.
- Create microsectors along the track and store geometry in an in-memory `duckdb` spatial table.
- Animate car positions in real time and show per-sector danger levels based on nearby accidents.
- Dynamically change the number of sectors that will look up for accidents.
- Test alignment of telemetry against the track.
- Telemety data is generated through FastF1 API.
- **This is a rough representation of a simulation, and interpolation is far from perfect.**

![spatial_index](https://github.com/user-attachments/assets/60902127-492d-4abb-b490-0ff4cf0eb52f)
