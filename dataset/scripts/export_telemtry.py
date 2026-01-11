import fastf1

fastf1.Cache.enable_cache(r'C:\Users\fdjor\Downloads')

# FastF1 api Bahrain sesija
race = fastf1.get_session(2023, 'Bahrain', 'R')
race.load()

# Krugovi
laps = race.laps.pick_driver('HAM')

# Najbrzi krug u trci
fastest_lap = laps.loc[laps['LapTime'].idxmin()]

telemetry = fastest_lap.get_telemetry()

# FastF1 time u sekunde konverzija
telemetry['Time'] = telemetry['Time'].dt.total_seconds()

# Cuvamo u csv
telemetry_df = telemetry[['Time', 'X', 'Y', 'Speed']]

telemetry_df.to_csv('hamilton_bahrain.csv', index=False)

