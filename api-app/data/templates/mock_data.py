content_gen_input = {
    "region": "Name_ABALOU Abla -Autre parcelle",
    "outputs": {
        "2024-12-23": {
            "curve-number": 70.89308553051583,
            "ndvi": 0.3311726052982869,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.026419354124047587,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.8305334428763211
        },
        "2025-01-02": {
            "curve-number": 65.86901523912354,
            "ndvi": 0.4257457384621265,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.13903182820553625,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.8609681717944638
        },
        "2025-01-07": {
            "curve-number": 65.98525540338092,
            "ndvi": 0.4150797399130213,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.1663068799497779,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.8336931200502222
        },
        "2025-01-12": {
            "curve-number": 78.69785637225098,
            "ndvi": 0.2915896498347248,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.029631506666680928,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.9236949533177709
        },
        "2025-01-17": {
            "curve-number": 66.74481216482332,
            "ndvi": 0.35783109319451545,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.07423941626975653,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.9247911147526104
        },
        "2025-01-22": {
            "curve-number": 70.05433968377068,
            "ndvi": 0.35347229084993753,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.172756845036906,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.8075661699964561
        },
        "2025-01-27": {
            "curve-number": 71.94932288563587,
            "ndvi": 0.34504334964796574,
            "precipitation": 1.1920928955078125e-10,
            "soil-fraction": 0.21028195963685203,
            "temperature": 29.295709228515648,
            "vegetation-fraction": 0.7823688578321615
        }
    }
}

report_data = {   'action_plan': [   'Implement efficient irrigation practices to address the lack of rainfall and ensure adequate '
                       'water supply for vegetation.',
                       'Monitor soil moisture levels regularly and adjust irrigation strategies as needed.',
                       'Consider implementing soil conservation measures to minimize runoff potential and improve '
                       'water infiltration.',
                       'Select drought-resistant vegetation species for future plantings to reduce water demand.',
                       'Conduct further investigation into the factors causing NDVI fluctuation and the runoff '
                       'potential change.'],
    'key_insights': [   {   'detail': 'NDVI values indicate moderate vegetation density with a slight fluctuation '
                                      'observed over the period.',
                            'title': 'Moderate Vegetation Health'},
                        {   'detail': 'Precipitation remained virtually zero throughout the reporting period, which '
                                      'might stress the vegetation.',
                            'title': 'Negligible Rainfall'},
                        {   'detail': 'Temperature remained relatively constant, which can be good for stable crop '
                                      'developement if water demand is satisfied.',
                            'title': 'Stable Temperature'},
                        {   'detail': 'Vegetation fraction is high (above 0.75) suggesting dense vegetation cover',
                            'title': 'High vegetation cover fraction'}],
    'location': 'Name_ABALOU Abla - Autre parcelle',
    'metrics': [   {   'description': 'Normalized difference vegitation index - The greenness and density of vegetation from 0 to 1.',
                       'id': 'ndvi',
                       'mean_value': 0.36,
                       'selected': True,
                       'series': [   {'timestamp': '2024-12-23', 'value': 0.3311726052982869},
                                     {'timestamp': '2025-01-02', 'value': 0.4257457384621265},
                                     {'timestamp': '2025-01-07', 'value': 0.4150797399130213},
                                     {'timestamp': '2025-01-12', 'value': 0.2915896498347248},
                                     {'timestamp': '2025-01-17', 'value': 0.35783109319451545},
                                     {'timestamp': '2025-01-22', 'value': 0.35347229084993753},
                                     {'timestamp': '2025-01-27', 'value': 0.34504334964796574}],
                       'time_insight': 'NDVI values fluctuated between 0.29 and 0.43 during the reporting period. '
                                       'There was an increase in NDVI in early January, followed by a gradual decline '
                                       'towards the end of January, suggesting a potential response to environmental '
                                       'conditions or management practices.',
                       'title': 'NDVI',
                       'graph_image_path': 'assets/images/metric.png',
                        'trend': {
                           "percent": 60.0,
                           "uptrend": True
                       }
                    },

                   {   'description': 'Proportion of ground covered by vegetation.',
                       'id': 'vegetation_fraction',
                       'mean_value': 0.85,
                       'selected': True,
                       'series': [   {'timestamp': '2024-12-23', 'value': 0.8305334428763211},
                                     {'timestamp': '2025-01-02', 'value': 0.8609681717944638},
                                     {'timestamp': '2025-01-07', 'value': 0.8336931200502222},
                                     {'timestamp': '2025-01-12', 'value': 0.9236949533177709},
                                     {'timestamp': '2025-01-17', 'value': 0.9247911147526104},
                                     {'timestamp': '2025-01-22', 'value': 0.8075661699964561},
                                     {'timestamp': '2025-01-27', 'value': 0.7823688578321615}],
                       'time_insight': 'Vegetation fraction remained high throughout the period, ranging from 0.78 to '
                                       '0.92. There was a peak in mid-January, indicating a period of high vegetation '
                                       'cover, followed by a slight decrease towards the end of the month.',
                       'title': 'VEGETATION FRACTION',
                       'graph_image_path': 'assets/images/metric.png',
                                              'trend': {
                           "percent": 60.0,
                           "uptrend": True
                       }
                    },
                   {   'description': 'Volumetric water content in the soil.',
                       'id': 'soil_fraction',
                       'mean_value': 0.11,
                       'selected': True,
                       'series': [   {'timestamp': '2024-12-23', 'value': 0.026419354124047587},
                                     {'timestamp': '2025-01-02', 'value': 0.13903182820553625},
                                     {'timestamp': '2025-01-07', 'value': 0.1663068799497779},
                                     {'timestamp': '2025-01-12', 'value': 0.029631506666680928},
                                     {'timestamp': '2025-01-17', 'value': 0.07423941626975653},
                                     {'timestamp': '2025-01-22', 'value': 0.172756845036906},
                                     {'timestamp': '2025-01-27', 'value': 0.21028195963685203}],
                       'time_insight': 'Soil fraction values fluctuated throughout the period, ranging from '
                                       'approximately 0.03 to 0.21. The soil fraction was relatively low at the '
                                       'beginning of the period, showed a general increase towards the end of the '
                                       'period, indicating a slow gain in the water content. Further monitoring would '
                                       'be needed.',
                       'title': 'SOIL FRACTION',
                       'graph_image_path': 'assets/images/metric.png',
                        'trend': {
                           "percent": 60.0,
                           "uptrend": True
                       }
                    },
                   {   'description': 'Amount of rainfall in millimeters.',
                       'id': 'precipitation',
                       'mean_value': 0.0,
                       'selected': True,
                       'series': [   {'timestamp': '2024-12-23', 'value': 1.1920928955078125e-10},
                                     {'timestamp': '2025-01-02', 'value': 1.1920928955078125e-10},
                                     {'timestamp': '2025-01-07', 'value': 1.1920928955078125e-10},
                                     {'timestamp': '2025-01-12', 'value': 1.1920928955078125e-10},
                                     {'timestamp': '2025-01-17', 'value': 1.1920928955078125e-10},
                                     {'timestamp': '2025-01-22', 'value': 1.1920928955078125e-10},
                                     {'timestamp': '2025-01-27', 'value': 1.1920928955078125e-10}],
                       'time_insight': 'Precipitation remained negligible (close to zero) throughout the entire '
                                       'reporting period, indicating very dry conditions. Irrigation strategies might '
                                       'be necessary to sustain vegetation.',
                       'title': 'PRECIPITATION',
                       'graph_image_path': 'assets/images/metric.png',
                        'trend': {
                           "percent": 60.0,
                           "uptrend": True
                       }
                    },
                   {   'description': 'Average surface temperature in degrees Celsius.',
                       'id': 'temperature',
                       'mean_value': 29.3,
                       'selected': True,
                       'series': [   {'timestamp': '2024-12-23', 'value': 29.295709228515648},
                                     {'timestamp': '2025-01-02', 'value': 29.295709228515648},
                                     {'timestamp': '2025-01-07', 'value': 29.295709228515648},
                                     {'timestamp': '2025-01-12', 'value': 29.295709228515648},
                                     {'timestamp': '2025-01-17', 'value': 29.295709228515648},
                                     {'timestamp': '2025-01-22', 'value': 29.295709228515648},
                                     {'timestamp': '2025-01-27', 'value': 29.295709228515648}],
                       'time_insight': 'Temperature remained consistently around 29.30°C throughout the reporting '
                                       'period. This stable and warm temperature may be suitable for vegetation if '
                                       'water requirements are met.',
                       'title': 'TEMPERATURE',
                       'graph_image_path': 'assets/images/metric.png',
                       'trend': {
                           "percent": 60.0,
                           "uptrend": False
                       }
                    },
                   {   'description': 'Runoff potential.',
                       'id': 'curve_number',
                       'mean_value': 70.03,
                       'selected': True,
                       'series': [   {'timestamp': '2024-12-23', 'value': 70.89308553051583},
                                     {'timestamp': '2025-01-02', 'value': 65.86901523912354},
                                     {'timestamp': '2025-01-07', 'value': 65.98525540338092},
                                     {'timestamp': '2025-01-12', 'value': 78.69785637225098},
                                     {'timestamp': '2025-01-17', 'value': 66.74481216482332},
                                     {'timestamp': '2025-01-22', 'value': 70.05433968377068},
                                     {'timestamp': '2025-01-27', 'value': 71.94932288563587}],
                       'time_insight': 'Curve number values fluctuated throughout the period, ranging from '
                                       'approximately 65.87 to 78.70. The variation suggests differences in runoff '
                                       'potential depending on short-term changes.',
                       'title': 'CURVE NUMBER',
                       'graph_image_path': 'assets/images/metric.png',
                       'trend': {
                           "percent": 60.0,
                           "uptrend": True
                       }
                    }],
    'overview': 'This report analyzes environmental conditions in Name_ABALOU Abla - Autre parcelle from December 23, '
                '2024, to January 27, 2025. The analysis includes NDVI, vegetation fraction, soil fraction, '
                'precipitation, temperature, and curve number. The data indicates moderate vegetation health with '
                'negligible rainfall and stable temperature, suggesting a need for water management strategies and '
                'soil conservation practices.',
    'time_period': '23 DEC 2024 - 27 JAN 2025',
    'region_screenshot_path': 'assets/images/region_screenshot.png'
    }

