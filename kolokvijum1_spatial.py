from tkinter import TclError

import pandas as pd

import db
from f1_car_simulator import F1CarSimulator
from track_simulator import TrackSimulator, scale_x_y_to_geo, finish_race

if __name__ == "__main__":
    track_sim = TrackSimulator('bahrain_track.geojson', sector_length_m=500)

    telemetry_car1 = pd.read_csv('dataset/verstappen_bahrain.csv')
    telemetry_car2 = pd.read_csv('dataset/hamilton_bahrain.csv')

    accidents = pd.read_csv('dataset/bahrain_accidents_2020_2023.csv')

    accidents_scaled = scale_x_y_to_geo(
        accidents,
        track_sim.track_gdf
    )

    db.add_accidents(accidents_scaled)

    telemetry_scaled_1 = scale_x_y_to_geo(
        telemetry_car1,
        track_sim.track_gdf
    )

    telemetry_scaled_2 = scale_x_y_to_geo(
        telemetry_car2,
        track_sim.track_gdf
    )



    car1 = F1CarSimulator("Verstappen", telemetry_scaled_1, track_sim)
    car2 = F1CarSimulator("Hamilton", telemetry_scaled_2, track_sim)

    track_sim.add_car("Verstappen", color='blue')
    track_sim.add_car("Hamilton", color='red')

    start_time = 0
    try:
        while True:
            pos1 = car1.move(start_time)
            pos2 = car2.move(start_time)

            if pos1 is None or pos2 is None:
                break

            start_time += 0.1 # Prosecna razlika u vremenu izmedju dve telemtrije (ovo nije 100% tacno vec je uzeto otrpilike)
    except (KeyboardInterrupt, TclError):
        print("\n\n=== Simulacija prekinuta ===")


