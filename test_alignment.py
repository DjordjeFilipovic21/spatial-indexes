import pandas as pd
from matplotlib import pyplot as plt

from track_simulator import scale_x_y_to_geo, TrackSimulator

# Ovim programom sam testirao alignment izmedju pozicije vozaca/incidenata i staze
if __name__ == "__main__":
    track_sim = TrackSimulator('bahrain_track.geojson', sector_length_m=50)

    telemetry_car1 = pd.read_csv('dataset/verstappen_bahrain.csv')

    telemetry_scaled = scale_x_y_to_geo(
        telemetry_car1,
        track_sim.track_gdf
    )
    print(telemetry_scaled.head())

    track_sim.test_telemetry_alignment(telemetry_scaled,
                                       label='Verstappen',
                                       color='blue')

    plt.show(block=True)
