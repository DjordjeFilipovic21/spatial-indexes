import fastf1
import pandas as pd



def export_bahrain_accidents(start_year, end_year):
    all_accidents = []

    for year in range(start_year, end_year + 1):
        try:
            # FastF1 api Bahrain sesija
            session = fastf1.get_session(year, 'Bahrain', 'R')
            session.load()

            # Krugovi
            laps = session.laps

            # Krugovi za svakog vozaca incidenti
            for driver in session.drivers:
                driver_laps = laps.pick_driver(driver)

                for idx, lap in driver_laps.iterrows():
                    # Krug nije zavrsen normalno
                    if pd.isna(lap['Time']) or lap['IsAccurate'] == False:
                        try:
                            telemetry = lap.get_telemetry()

                            if len(telemetry) > 0:
                                # Pozicija gde se inc desio
                                last_pos = telemetry.iloc[-1]

                                # Proverava da li su ostali vozaci imali nezgodu na istoj lokaciji
                                is_multi_car = check_multi_car_incident(
                                    session, lap['LapNumber']
                                )

                                accident_data = {
                                    'year': year,
                                    'timestamp': last_pos['Time'],
                                    'x': last_pos['X'],
                                    'y': last_pos['Y'],
                                    'lap_number': lap['LapNumber'],
                                    'driver': driver,
                                    'multi_car': is_multi_car
                                }

                                all_accidents.append(accident_data)

                        except Exception as e:
                            print(f"Error processing lap {lap['LapNumber']} for driver {driver}: {e}")

        except Exception as e:
            print(f"Error processing year {year}: {e}")
            continue

    # Create DataFrame and export
    df = pd.DataFrame(all_accidents)
    df.to_csv(f'bahrain_accidents_{start_year}_{end_year}.csv', index=False)
    print(f"Exported {len(all_accidents)} accidents to CSV")

    return df


def check_multi_car_incident(session, lap_number, time_threshold=5):
    # Proverava da li su ostali vozaci imali nezgodu na istoj lokaciji

    incidents_on_lap = 0

    for driver in session.drivers:
        try:
            driver_laps = session.laps.pick_driver(driver)
            lap = driver_laps[driver_laps['LapNumber'] == lap_number]

            if len(lap) > 0:
                lap_data = lap.iloc[0]
                if pd.isna(lap_data['Time']) or lap_data['IsAccurate'] == False:
                    incidents_on_lap += 1

        except Exception:
            continue

    return incidents_on_lap > 1



