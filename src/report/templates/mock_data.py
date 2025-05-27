# report_data = {
#     "location": "DISTRICT 7 - HO CHI MINH",
#     "time_period": "10 APR - 35 MAY 2025",
#     "overview": "This report provides a comprehensive assessment of six key environmental metrics—NDVI, Vegetation Fraction, Soil Moisture, Precipitation, Temperature, and Curve Number— for a selected geographic area over the course of 2024. The objective is to deliver intuitive insights into the region’s vegetation health, water balance, and climate dynamics, enabling both technical and non-technical stakeholders to make informed decisions.",
#     "key_insights": [
#         (
#             "Healthy but Moderate Vegetation",
#             "Vegetation indicators (NDVI and Vegetation Fraction) remained consistently moderate, peaking during spring and early summer, with no abrupt degradation observed throughout the year."
#         ),
#         (
#             "Adequate Soil Moisture, No Drought Signals",
#             "Soil moisture levels were stable and adequate throughout the year, supporting consistent plant growth."
#         ),
#         (
#             "Seasonal Rainfall Distribution",
#               "Precipitation followed a clear seasonal pattern, with wetter periods in early autumn and late summer, and noticeably drier months during mid-year."
#         ),
#         (
#             "Temperate Climate Patterns",
#             "Average temperature hovered around 22 °C with warm peaks early in the year and cooling mid-year, consistent with subtropical seasonal cycles."
#         ),
#         (
#             "Moderate Runoff Risk",
#             "Curve Number values indicate the area has mixed surface permeability—neither highly absorbent nor heavily sealed—suggesting that urban or agricultural expansion should consider localized flood mitigation strategies."
#         )
#     ],
#     "metrics": [
#         {
#             "id": "ndvi",
#             "selected": True,
#             "title": "NORMALIZED DIFFERENCE VEGETATION INDEX",
#             "description": "Indicates vegetation health from 0 to 1.",
#             "mean_value": 0.53,
#             "mean_insight": "A moderately healthy vegetation level. Represent grassy or mixed vegetation cover",
#             "time_insight": "Gradual increase from January to a peak in May–June, followed by a slight decline. Indicates seasonal vegetation growth aligning with spring.",
#             "series": [
#                 ("Jan", 0.45), ("Feb", 0.48), ("Mar", 0.52), ("Apr", 0.55), ("May", 0.65), ("Jun", 0.67),
#                 ("Jul", 0.64), ("Aug", 0.60), ("Sep", 0.58), ("Oct", 0.55), ("Nov", 0.53), ("Dec", 0.50)
#             ]
#         },
#         {
#             "id": "vegetation_fraction",
#             "selected": True,
#             "title": "VEGETATION FRACTION",
#             "description": "Proportion of ground covered by vegetation.",
#             "mean_value": 0.59,
#             "mean_insight": "Fair but not dense vegetative coverage.",
#             "time_insight": "Noticeable growth in early months, slight drop during dry mid-year months (July–August), then slight recovery towards December.",
#             "series": [
#                 ("Jan", 0.45), ("Feb", 0.55), ("Mar", 0.65), ("Apr", 0.75), ("May", 0.80), ("Jun", 0.75),
#                 ("Jul", 0.60), ("Aug", 0.50), ("Sep", 0.55), ("Oct", 0.60), ("Nov", 0.55), ("Dec", 0.50)
#             ]
#         },
#         {
#             "id": "soil_moisture",
#             "selected": True,
#             "title": "SOIL MOISTURE",
#             "description": "Volumetric water content in the soil.",
#             "mean_value": 0.24,
#             "mean_insight": "Fair but not dense vegetative coverage.",
#             "time_insight": "Fairly stable throughout the year, with mild dips in mid-year, aligning with reduced rainfall.",
#             "series": [
#                 ("Jan", 0.25), ("Feb", 0.27), ("Mar", 0.30), ("Apr", 0.32), ("May", 0.29), ("Jun", 0.25),
#                 ("Jul", 0.20), ("Aug", 0.18), ("Sep", 0.22), ("Oct", 0.25), ("Nov", 0.26), ("Dec", 0.25)
#             ]
#         },
#         {
#             "id": "precipitation",
#             "selected": True,
#             "title": "PRECIPITATION",
#             "description": "Amount of rainfall in millimeters.",
#             "mean_value": 78.5,
#             "mean_insight": "Fair but not dense vegetative coverage.",
#             "time_insight": "Peaks observed around March and October, with noticeable dips in June–July, indicating a bimodal rainfall pattern.",
#             "series": [
#                 ("Jan", 65), ("Feb", 80), ("Mar", 100), ("Apr", 90), ("May", 75), ("Jun", 45),
#                 ("Jul", 40), ("Aug", 60), ("Sep", 85), ("Oct", 105), ("Nov", 85), ("Dec", 70)
#             ]
#         },
#         {
#             "id": "temperature",
#             "selected": True,
#             "title": "TEMPERATURE",
#             "description": "Average surface temperature in degrees Celsius.",
#             "mean_value": 22.3,
#             "mean_insight": "Fair but not dense vegetative coverage.",
#             "time_insight": "Highest temperatures between January and March (~27°C), lowest in July (~17°C), consistent with Southern Hemisphere seasonality.",
#             "series": [
#                 ("Jan", 27), ("Feb", 26), ("Mar", 27), ("Apr", 24), ("May", 21), ("Jun", 19),
#                 ("Jul", 17), ("Aug", 18), ("Sep", 20), ("Oct", 22), ("Nov", 24), ("Dec", 25)
#             ]
#         },
#         {
#             "id": "curve_number",
#             "selected": True,
#             "title": "CURVE NUMBER",
#             "description": "Runoff potential.",
#             "mean_value": 75.2,
#             "mean_insight": "Fair but not dense vegetative coverage.",
#             "time_insight": "Slight increase during dry months likely due to reduced infiltration, which increases runoff potential. Most stable of all metrics.",
#             "series": [
#                 ("Jan", 72), ("Feb", 71), ("Mar", 70), ("Apr", 72), ("May", 74), ("Jun", 76),
#                 ("Jul", 80), ("Aug", 81), ("Sep", 78), ("Oct", 75), ("Nov", 74), ("Dec", 73)
#             ]
#         }
#     ],
#     "action_plan": [
#         "Continue monitoring NDVI and vegetation fraction to detect degradation early.",
#         "Enhance soil moisture retention using mulching or ground cover.",
#         "Design drainage systems considering the runoff curve number to reduce flooding.",
#         "Plan irrigation during dry months based on rainfall trends.",
#         "Promote afforestation in low vegetation zones to improve NDVI and ecosystem health."
#     ]
# }


# content_gen_input = {
#     "region": "Distric 1 - Ho Chi Minh",
#     "outputs": {
#         "2024-12-23": {
#             "curve-number": 70.89308553051583,
#             "ndvi": 0.3311726052982869,
#             "precipitation": 1.1920928955078125e-10,
#             "soil-fraction": 0.026419354124047587,
#             "temperature": 29.295709228515648,
#             "vegetation-fraction": 0.8305334428763211
#         },
#         "2025-01-02": {
#             "curve-number": 65.86901523912354,
#             "ndvi": 0.4257457384621265,
#             "precipitation": 1.1920928955078125e-10,
#             "soil-fraction": 0.13903182820553625,
#             "temperature": 29.295709228515648,
#             "vegetation-fraction": 0.8609681717944638
#         },
#         "2025-01-07": {
#             "curve-number": 65.98525540338092,
#             "ndvi": 0.4150797399130213,
#             "precipitation": 1.1920928955078125e-10,
#             "soil-fraction": 0.1663068799497779,
#             "temperature": 29.295709228515648,
#             "vegetation-fraction": 0.8336931200502222
#         },
#         "2025-01-12": {
#             "curve-number": 78.69785637225098,
#             "ndvi": 0.2915896498347248,
#             "precipitation": 1.1920928955078125e-10,
#             "soil-fraction": 0.029631506666680928,
#             "temperature": 29.295709228515648,
#             "vegetation-fraction": 0.9236949533177709
#         },
#         "2025-01-17": {
#             "curve-number": 66.74481216482332,
#             "ndvi": 0.35783109319451545,
#             "precipitation": 1.1920928955078125e-10,
#             "soil-fraction": 0.07423941626975653,
#             "temperature": 29.295709228515648,
#             "vegetation-fraction": 0.9247911147526104
#         },
#         "2025-01-22": {
#             "curve-number": 70.05433968377068,
#             "ndvi": 0.35347229084993753,
#             "precipitation": 1.1920928955078125e-10,
#             "soil-fraction": 0.172756845036906,
#             "temperature": 29.295709228515648,
#             "vegetation-fraction": 0.8075661699964561
#         },
#         "2025-01-27": {
#             "curve-number": 71.94932288563587,
#             "ndvi": 0.34504334964796574,
#             "precipitation": 1.1920928955078125e-10,
#             "soil-fraction": 0.21028195963685203,
#             "temperature": 29.295709228515648,
#             "vegetation-fraction": 0.7823688578321615
#         }
#     }
# }

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
    'metrics': [   {   'description': 'Indicates vegetation health from 0 to 1.',
                       'id': 'ndvi',
                       'mean_insight': 'An average NDVI of 0.36 suggests moderate vegetation density for Name_ABALOU '
                                       'Abla - Autre parcelle, indicating some vegetative activity but potentially '
                                       'below optimal levels.',
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
                       'title': 'NORMALIZED DIFFERENCE VEGETATION INDEX'},
                   {   'description': 'Proportion of ground covered by vegetation.',
                       'id': 'vegetation_fraction',
                       'mean_insight': 'An average vegetation fraction of 0.85 indicates a high proportion of ground '
                                       'cover by vegetation in Name_ABALOU Abla - Autre parcelle, suggesting dense '
                                       'vegetation.',
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
                       'title': 'VEGETATION FRACTION'},
                   {   'description': 'Volumetric water content in the soil.',
                       'id': 'soil_fraction',
                       'mean_insight': 'The average soil fraction of 0.11 indicates low water content in the soil of '
                                       'Name_ABALOU Abla - Autre parcelle during the reporting period. This suggests '
                                       'relatively dry soil conditions.',
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
                       'title': 'SOIL FRACTION'},
                   {   'description': 'Amount of rainfall in millimeters.',
                       'id': 'precipitation',
                       'mean_insight': 'An average precipitation of 0 mm indicates virtually no rainfall in '
                                       'Name_ABALOU Abla - Autre parcelle during the reporting period, which may cause '
                                       'dry soil condition.',
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
                       'title': 'PRECIPITATION'},
                   {   'description': 'Average surface temperature in degrees Celsius.',
                       'id': 'temperature',
                       'mean_insight': 'An average temperature of 29.30°C suggests warm conditions in Name_ABALOU Abla '
                                       '- Autre parcelle during the reporting period, influencing vegetation growth '
                                       'and water demand.',
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
                       'title': 'TEMPERATURE'},
                   {   'description': 'Runoff potential.',
                       'id': 'curve_number',
                       'mean_insight': 'An average curve number of 70.03 indicates a moderate runoff potential in '
                                       'Name_ABALOU Abla - Autre parcelle. This suggests that a moderate amount of '
                                       'rainfall would result in surface runoff.',
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
                       'title': 'CURVE NUMBER'}],
    'overview': 'This report analyzes environmental conditions in Name_ABALOU Abla - Autre parcelle from December 23, '
                '2024, to January 27, 2025. The analysis includes NDVI, vegetation fraction, soil fraction, '
                'precipitation, temperature, and curve number. The data indicates moderate vegetation health with '
                'negligible rainfall and stable temperature, suggesting a need for water management strategies and '
                'soil conservation practices.',
    'time_period': '23 DEC 2024 - 27 JAN 2025'}

