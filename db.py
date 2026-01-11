import duckdb

con = duckdb.connect(':memory:')


def init_f1_duckdb():

    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")

    con.execute("DROP TABLE IF EXISTS microsectors;")
    con.execute("""
CREATE TABLE microsectors (
  sector_id        INTEGER PRIMARY KEY,
  geom             GEOMETRY,
  start_distance_m REAL,
  end_distance_m   REAL,
  CONSTRAINT chk_geom_type        CHECK (ST_GeometryType(geom) = 'LINESTRING')
);

                    
                """)

    con.execute("DROP TABLE IF EXISTS accidents;")

    con.execute("""
                CREATE TABLE accidents
                (
                    accident_id   INTEGER PRIMARY KEY,
                    race_year     INTEGER,
                    driver_id    INTEGER,
                    lap_number    INTEGER,
                    latitude      REAL,
                    longitude     REAL,
                    multi_car BOOLEAN, --multicar ili singlecar
                    timestamp     VARCHAR
                )
                """)

    return con


def add_accidents(accidents_scaled):
    con.register('accidents_scaled', accidents_scaled)
    con.execute("""
                INSERT INTO accidents (accident_id, race_year, driver_id, lap_number, latitude, longitude,
                                       multi_car, timestamp)
                SELECT ROW_NUMBER() OVER (ORDER BY year, driver, lap_number) as accident_id,
                       year,
                       driver,
                       lap_number,
                       Lon,
                       Lat,
                       multi_car,
               timestamp
        FROM accidents_scaled
                """)
    num_acc = len(accidents_scaled)
    print(f"Importovano: {num_acc} incidenata!")

    #hilbert
    con.execute("ALTER TABLE accidents ADD COLUMN hilbert_value UINTEGER;")
    con.execute("UPDATE accidents SET hilbert_value = ST_Hilbert(ST_Point(longitude, latitude));")
    con.execute("CREATE INDEX accidents_hilbert_idx ON accidents(hilbert_value);")