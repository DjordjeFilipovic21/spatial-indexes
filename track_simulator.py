import matplotlib
from pyproj import Transformer
from matplotlib import pyplot as plt
import contextily as ctx
matplotlib.use('TkAgg')
import geopandas as gpd
from shapely.geometry import LineString
from shapely.ops import substring
from db import init_f1_duckdb


def scale_x_y_to_geo(telemetry_xy, track_gdf, lat_offset=-0.0057, lon_offset=-0.00025):
    # Skaliranje telemtrije i incidenata na osnovu GeoJson kordinata staze, offseti su zakucani za ovu stazu
    if isinstance(track_gdf, gpd.GeoDataFrame):
        track_line = track_gdf.iloc[0]['geometry']
        track_coords = list(track_line.coords)
    else:
        track_coords = track_gdf['geometry']['coordinates']

    ref_lon, ref_lat = track_coords[0]

    x_min, x_max = telemetry_xy['X'].min(), telemetry_xy['X'].max()
    y_min, y_max = telemetry_xy['Y'].min(), telemetry_xy['Y'].max()

    lats = [c[1] for c in track_coords]
    lons = [c[0] for c in track_coords]
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)

    telemetry_xy['Lon'] = ref_lon + (telemetry_xy['X'] - x_min) / (x_max - x_min) * lon_range + lon_offset
    telemetry_xy['Lat'] = ref_lat + (telemetry_xy['Y'] - y_min) / (y_max - y_min) * lat_range + lat_offset

    return telemetry_xy




def create_microsectors_duckdb(con, track_gdf, sector_length_m):
    # Geometrija staze
    if isinstance(track_gdf, gpd.GeoDataFrame):
        track_line = track_gdf.iloc[0]['geometry']
    else:
        track_line = LineString(track_gdf['geometry']['coordinates'])

    # Konverzija u metre
    track_length = track_line.length * 111320
    num_sectors = int(track_length / sector_length_m)

    sectors = []
    for i in range(num_sectors):
        start_dist = i * sector_length_m / track_length
        end_dist = (i + 1) * sector_length_m / track_length

        sector_geom = substring(track_line, start_dist, end_dist, normalized=True)

        sectors.append({
            'sector_id': i,
            'geometry': sector_geom,
            'start_distance_m': i * sector_length_m,
            'end_distance_m': (i + 1) * sector_length_m,
        })

    # GeoDataFrame mikrosektora od GeoJsona
    sectors_gdf = gpd.GeoDataFrame(sectors, crs='EPSG:4326')

    for s in sectors:
        wkt = s['geometry'].wkt
        con.execute("""
            INSERT INTO microsectors VALUES (?, ST_GeomFromText(?), ?, ?)
        """, [s['sector_id'], wkt, s['start_distance_m'], s['end_distance_m']])


    print(f"Kreirano: {num_sectors} mikrosektora!")
    return sectors_gdf



def finish_race():
    plt.ioff()
    plt.title(f"Ruta završena!")
    plt.show()


def calculate_danger_level(accidents):
    # Kroz svaki incident...
    danger_level = 1
    for accident_info in accidents:
        danger_level += 1
        if accident_info[6] is True:
            danger_level += 1

    if danger_level < 3:
            return "Mildly dangerous"
    elif danger_level < 6:
            return "Dangerous"
    else:
            return "Very dangerous"



class TrackSimulator:
    def __init__(self, track_geojson_path, sector_length_m):
        self.track_gdf = gpd.read_file(track_geojson_path)
        self.db = init_f1_duckdb()


        # Konverzija za prikaz mapi u espg3857
        track_web = self.track_gdf.to_crs(epsg=3857)

        self.microsectors = create_microsectors_duckdb(
            self.db,
            self.track_gdf,
            sector_length_m
        )
        # Konverzija za prikaz na mapi
        microsectors_web = self.microsectors.to_crs(epsg=3857)


        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.fig.subplots_adjust(top=0.90)

        # Granice staze
        bounds = track_web.total_bounds
        self.ax.set_xlim(bounds[0], bounds[2])
        self.ax.set_ylim(bounds[1], bounds[3])

        # Mapa kao background
        try:
            ctx.add_basemap(self.ax,
                            source=ctx.providers.OpenStreetMap.Mapnik,
                            zoom=16,
                            alpha=0.7)
        except Exception as e:
            print(f"Warning: Could not add basemap: {e}")

        # NOW plot track and sectors on top of basemap
        track_web.plot(ax=self.ax, color='black', linewidth=2,
                       alpha=0.7, label='Track', zorder=2)

        # Tacke koje obelezavaju pocetak i kraj sektora
        sector_points = []
        for idx, sector in microsectors_web.iterrows():
            coords = list(sector.geometry.coords)
            sector_points.extend([coords[0], coords[-1]])

        if sector_points:
            xs, ys = zip(*sector_points)
            self.ax.scatter(xs, ys, c='white', s=1, alpha=0.8,
                           label='Sector Points', zorder=3)

        self.ax.set_aspect('equal')
        self.ax.legend()
        plt.ion()

        self.car_markers = {}
        self.car_info_texts = {}
        self.car_current_sectors = {}
        self.danger_level = {}

    def query_sector_at_position(self, lat, lon, tol_deg=0.001):
        sql = """
              SELECT sector_id, start_distance_m, end_distance_m
              FROM microsectors
              WHERE ST_DWithin(geom, ST_Point(?, ?), ?)
              LIMIT 1; \
              """
        params = [lon, lat, float(tol_deg)]

        row = self.db.execute(sql, params).fetchone()
        if not row:
            return None
        return {
            'sector_id': row[0],
            'start_distance_m': row[1],
            'end_distance_m': row[2],
        }

    def query_accidents_at_sector(self, sector_id):
        sql = """
              SELECT a.*
              FROM accidents a
              JOIN microsectors m
                ON ST_DWithin( ST_Point(a.latitude, a.longitude), m.geom, 0.001)
              WHERE m.sector_id = ?
              ;
              """
        params = [sector_id]
        rows = self.db.execute(sql, params).fetchall()
        if not rows:
            return None
        return rows


    def update_car_position(self, car_id, lat, lon, speed, timestamp):
        if car_id not in self.car_markers:
            self.add_car(car_id)

        # Konverzija za prikaz na mapi
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x_web, y_web = transformer.transform(lon, lat)

        # Update
        self.car_markers[car_id].set_data([x_web], [y_web])

        # Koji je sektor u pitanju na osnovu pozicije bolida
        sector_info = self.query_sector_at_position(lat, lon)


        if sector_info:

            current_sector = sector_info["sector_id"]
            previous_sector = self.car_current_sectors.get(car_id)

            # Samo ako se sektor promenio gledamo incidente
            if current_sector != previous_sector:
                accidents = self.query_accidents_at_sector(current_sector)
                if accidents:
                    self.car_current_sectors[car_id] = current_sector
                    self.danger_level[car_id] = calculate_danger_level(accidents)
                else:
                    self.danger_level[car_id] = "Not dangerous"

            # Labeli zakucani gore levo..
            if car_id in self.car_info_texts:
                self.car_info_texts[car_id].remove()

            # Labeli zakucani gore levo..
            car_ids = sorted(self.car_markers.keys())
            car_index = car_ids.index(car_id)
            y_position = 0.95 - car_index * 0.04

            # Labeli zakucani gore levo..
            text_obj = self.fig.text(
                0.02, y_position,
                f"Car {car_id} | Sector: {sector_info['sector_id']} | Speed: {speed:.1f} km/h | Time: {timestamp:.2f}s | Danger: {self.danger_level.get(car_id, 0)}",
                fontsize=10,
                ha='left',
                va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black')
            )
            self.car_info_texts[car_id] = text_obj

        plt.draw()
        plt.pause(0.01)

    def add_car(self, car_id, color='red'):
        marker, = self.ax.plot([], [], 'o', color=color, markersize=10,
                               label=f'Car {car_id}', zorder=3)  # High zorder = on top
        self.car_markers[car_id] = marker
        self.ax.legend()

    def test_telemetry_alignment(self, telemetry_df, label='Telemetry', color='blue'):
        self.ax.plot(telemetry_df['Lon'], telemetry_df['Lat'],
                     color=color, linewidth=1, alpha=0.7,
                     label=label, linestyle='--')
        self.ax.legend()
        plt.draw()
        plt.pause(0.001)




