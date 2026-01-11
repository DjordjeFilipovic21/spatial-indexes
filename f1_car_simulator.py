class F1CarSimulator:
    def __init__(self, car_id, telemetry_df, track_simulator):
        self.car_id = car_id
        # Kolone: Time, Lat, Lon, Speed (skalirane)
        self.telemetry = telemetry_df.sort_values('Time').reset_index(drop=True)
        self.track_sim = track_simulator
        self.current_idx = 0

    def move(self, current_time):
        # Najblize trenutnom vremenu
        idx = self.telemetry['Time'].searchsorted(current_time)
        if idx >= len(self.telemetry):
            return None

        row = self.telemetry.iloc[idx]
        self.track_sim.update_car_position(
            self.car_id, row['Lat'], row['Lon'], row['Speed'], row['Time']
        )
        return row['Lat'], row['Lon']
