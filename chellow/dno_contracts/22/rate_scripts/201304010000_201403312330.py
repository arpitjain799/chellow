def lafs():
    return {
        'lv-net': {
            'winter-weekday-peak': 1.087,
            'winter-weekday-day': 1.080,
            'night': 1.071,
            'other': 1.074},
        'lv-sub': {
            'winter-weekday-peak': 1.078,
            'winter-weekday-day': 1.072,
            'night': 1.064,
            'other': 1.067},
        'hv-net': {
            'winter-weekday-peak': 1.065,
            'winter-weekday-day': 1.058,
            'night': 1.044,
            'other': 1.050}}


def tariffs():
    return {
        '110': {
            'description': 'Small Non Domestic Unrestricted',
            'gbp-per-mpan-per-day': 0.0659,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': 0.02541,
            'amber-gbp-per-kwh': 0.02541,
            'green-gbp-per-kwh': 0.02541,
            'gbp-per-kvarh': 0},
        '510': {
            'description': 'High Voltage HH Metered',
            'gbp-per-mpan-per-day': 0.7295,
            'gbp-per-kva-per-day': 0.0222,
            'excess-gbp-per-kva-per-day': 0.0222,
            'red-gbp-per-kwh': 0.18909,
            'amber-gbp-per-kwh': 0.00072,
            'green-gbp-per-kwh': 0.00071,
            'gbp-per-kvarh': 0.00250},
        '521': {
            'description': 'HV Generation Intermittent',
            'gbp-per-mpan-per-day': 0.3136,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.00368,
            'amber-gbp-per-kwh': -0.00368,
            'green-gbp-per-kwh': -0.00368,
            'gbp-per-kvarh': 0.00092},
        '523': {
            'description': 'HV Sub Generation Intermittent',
            'gbp-per-mpan-per-day': 0.2921,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.0324,
            'amber-gbp-per-kwh': -0.0324,
            'green-gbp-per-kwh': -0.0324,
            'gbp-per-kvarh': 0.00063},
        '524': {
            'description': 'HV Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.3136,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.04834,
            'amber-gbp-per-kwh': -0.00096,
            'green-gbp-per-kwh': -0.00077,
            'gbp-per-kvarh': 0.00092},
        '525': {
            'description': 'HV Sub Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0.2921,
            'gbp-per-kva-per-day': 0.00,
            'excess-gbp-per-kva-per-day': 0.00,
            'red-gbp-per-kwh': -0.04396,
            'amber-gbp-per-kwh': -0.00066,
            'green-gbp-per-kwh': -0.00067,
            'gbp-per-kvarh': 0.00063},
        '526': {
            'description': 'LV Sub Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.07008,
            'amber-gbp-per-kwh': -0.00262,
            'green-gbp-per-kwh': -0.00142,
            'gbp-per-kvarh': 0.00126},
        '527': {
            'description': 'LV Generation Non-Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.07478,
            'amber-gbp-per-kwh': -0.003,
            'green-gbp-per-kwh': -0.00157,
            'gbp-per-kvarh': 0.00147},
        '540': {
            'description': 'Low Voltage Sub HH Metered',
            'gbp-per-mpan-per-day': 0.0654,
            'gbp-per-kva-per-day': 0.0287,
            'excess-gbp-per-kva-per-day': 0.0287,
            'red-gbp-per-kwh': 0.22433,
            'amber-gbp-per-kwh': 0.00170,
            'green-gbp-per-kwh': 0.00115,
            'gbp-per-kvarh': 0.00318},
        '551': {
            'description': 'LV Sub Generation Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.00598,
            'amber-gbp-per-kwh': -0.00598,
            'green-gbp-per-kwh': -0.00598,
            'gbp-per-kvarh': 0.00126},
        '570': {
            'description': 'Low Voltage HH Metered',
            'gbp-per-mpan-per-day': 0.0905,
            'gbp-per-kva-per-day': 0.0260,
            'excess-gbp-per-kva-per-day': 0.0260,
            'red-gbp-per-kwh': 0.24410,
            'amber-gbp-per-kwh': 0.00287,
            'green-gbp-per-kwh': 0.00161,
            'gbp-per-kvarh': 0.00382},
        '581': {
            'description': 'LV Generation Intermittent',
            'gbp-per-mpan-per-day': 0,
            'gbp-per-kva-per-day': 0,
            'excess-gbp-per-kva-per-day': 0,
            'red-gbp-per-kwh': -0.00649,
            'amber-gbp-per-kwh': -0.00649,
            'green-gbp-per-kwh': -0.00649,
            'gbp-per-kvarh': 0.00147}}
