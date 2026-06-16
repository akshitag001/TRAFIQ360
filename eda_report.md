# Exploratory Data Analysis (EDA) Report - TRAFIQ360

Generated for the Event-Driven Congestion Command Hackathon.

## 1. Dataset Overview
- **Total Records**: 8173
- **Planned Events**: 467 (5.71%)
- **Unplanned Events**: 7706 (94.29%)
- **Requires Road Closure**: 676 (8.27%)
- **High Priority Events**: 5030 (61.54%)

## 2. Missing Values Analysis
| Column | Missing Count | Missing Percentage |
|---|---|---|
| endlatitude | 169 | 2.07% |
| endlongitude | 169 | 2.07% |
| address | 3 | 0.04% |
| end_address | 7486 | 91.59% |
| start_datetime | 116 | 1.42% |
| end_datetime | 7683 | 94.00% |
| map_file | 8173 | 100.00% |
| direction | 8130 | 99.47% |
| description | 1360 | 16.64% |
| veh_type | 3286 | 40.21% |
| veh_no | 3287 | 40.22% |
| corridor | 20 | 0.24% |
| priority | 2 | 0.02% |
| cargo_material | 7897 | 96.62% |
| reason_breakdown | 7897 | 96.62% |
| age_of_truck | 7897 | 96.62% |
| route_path | 8036 | 98.32% |
| created_by_id | 2 | 0.02% |
| last_modified_by_id | 3 | 0.04% |
| assigned_to_police_id | 8045 | 98.43% |
| citizen_accident_id | 8045 | 98.43% |
| comment | 8173 | 100.00% |
| meta_data | 8173 | 100.00% |
| kgid | 259 | 3.17% |
| resolved_at_address | 8099 | 99.09% |
| resolved_at_latitude | 8099 | 99.09% |
| resolved_at_longitude | 8099 | 99.09% |
| closed_by_id | 5032 | 61.57% |
| closed_datetime | 5032 | 61.57% |
| resolved_by_id | 8099 | 99.09% |
| resolved_datetime | 8099 | 99.09% |
| gba_identifier | 4729 | 57.86% |
| zone | 4729 | 57.86% |
| junction | 5663 | 69.29% |
| hour | 116 | 1.42% |
| dow | 116 | 1.42% |

## 3. Event Cause Breakdown
| Cause | Count | Percentage | Avg Impact | Closure Rate | Median Duration (min) |
|---|---|---|---|---|---|
| vehicle_breakdown | 4896 | 59.90% | 4.97 | 4.3% | 64.4 |
| others | 638 | 7.81% | 5.23 | 8.6% | 64.4 |
| pot_holes | 537 | 6.57% | 5.74 | 2.4% | 64.4 |
| construction | 480 | 5.87% | 8.40 | 26.5% | 64.4 |
| water_logging | 458 | 5.60% | 7.94 | 8.5% | 64.4 |
| accident | 365 | 4.47% | 7.92 | 3.0% | 64.4 |
| tree_fall | 284 | 3.47% | 8.68 | 39.4% | 64.4 |
| road_conditions | 170 | 2.08% | 7.28 | 12.4% | 64.4 |
| congestion | 136 | 1.66% | 8.21 | 4.4% | 64.4 |
| public_event | 84 | 1.03% | 9.30 | 46.4% | 64.4 |
| procession | 72 | 0.88% | 8.86 | 26.4% | 64.4 |
| vip_movement | 20 | 0.24% | 9.93 | 80.0% | 64.4 |
| protest | 15 | 0.18% | 9.67 | 40.0% | 64.4 |
| Debris | 12 | 0.15% | 6.96 | 8.3% | 64.4 |
| test_demo | 3 | 0.04% | 1.80 | 0.0% | 2.4 |
| Fog / Low Visibility | 2 | 0.02% | 6.00 | 0.0% | 64.4 |
| debris | 1 | 0.01% | 9.60 | 100.0% | 64.4 |

## 4. Corridor Congestion Analysis
| Corridor | Count | Percentage | Avg Impact | Closure Rate | Median Duration (min) |
|---|---|---|---|---|---|
| Non-corridor | 3124 | 38.22% | 5.44 | 12.1% | 64.4 |
| Mysore Road | 743 | 9.09% | 5.98 | 11.0% | 64.4 |
| Bellary Road 1 | 610 | 7.46% | 5.87 | 5.4% | 64.4 |
| Tumkur Road | 458 | 5.60% | 5.54 | 2.6% | 64.4 |
| Bellary Road 2 | 379 | 4.64% | 6.10 | 3.2% | 64.4 |
| Hosur Road | 298 | 3.65% | 6.14 | 5.7% | 64.4 |
| ORR North 1 | 275 | 3.36% | 6.48 | 8.0% | 64.4 |
| Old Madras Road | 263 | 3.22% | 5.91 | 4.6% | 64.4 |
| Magadi Road | 245 | 3.00% | 5.90 | 4.1% | 64.4 |
| ORR East 1 | 244 | 2.99% | 6.16 | 7.4% | 64.4 |
| ORR North 2 | 235 | 2.88% | 6.29 | 4.3% | 64.4 |
| Bannerghata Road | 209 | 2.56% | 6.45 | 3.3% | 64.4 |
| ORR East 2 | 187 | 2.29% | 7.51 | 1.6% | 64.4 |
| West of Chord Road | 174 | 2.13% | 6.12 | 6.3% | 64.4 |
| ORR West 1 | 168 | 2.06% | 6.32 | 3.0% | 64.4 |
| CBD 2 | 104 | 1.27% | 6.39 | 6.7% | 64.4 |
| Hennur Main Road | 96 | 1.17% | 7.24 | 6.2% | 64.4 |
| IRR(Thanisandra road) | 95 | 1.16% | 6.51 | 6.3% | 64.4 |
| Varthur Road | 77 | 0.94% | 6.24 | 11.7% | 64.4 |
| Old Airport Road | 76 | 0.93% | 6.46 | 7.9% | 64.4 |
| Airport New South Road | 67 | 0.82% | 6.90 | 10.4% | 64.4 |
| CBD 1 | 26 | 0.32% | 6.45 | 11.5% | 64.4 |

## 5. Temporal Patterns
### Hourly Event Distribution
| Hour | Count | Percentage | Avg Impact |
|---|---|---|---|
| 00h | 418.0 | 5.11% | 4.88 |
| 01h | 381.0 | 4.66% | 4.67 |
| 02h | 387.0 | 4.74% | 4.77 |
| 03h | 372.0 | 4.55% | 4.77 |
| 04h | 558.0 | 6.83% | 6.26 |
| 05h | 661.0 | 8.09% | 6.36 |
| 06h | 660.0 | 8.08% | 6.43 |
| 07h | 480.0 | 5.87% | 6.54 |
| 08h | 327.0 | 4.00% | 5.75 |
| 09h | 160.0 | 1.96% | 5.58 |
| 10h | 68.0 | 0.83% | 6.09 |
| 11h | 68.0 | 0.83% | 5.84 |
| 12h | 63.0 | 0.77% | 5.87 |
| 13h | 33.0 | 0.40% | 6.04 |
| 14h | 13.0 | 0.16% | 4.54 |
| 15h | 9.0 | 0.11% | 5.72 |
| 16h | 9.0 | 0.11% | 6.74 |
| 17h | 34.0 | 0.42% | 5.76 |
| 18h | 228.0 | 2.79% | 5.58 |
| 19h | 578.0 | 7.07% | 6.07 |
| 20h | 681.0 | 8.33% | 6.21 |
| 21h | 810.0 | 9.91% | 6.28 |
| 22h | 564.0 | 6.90% | 6.09 |
| 23h | 495.0 | 6.06% | 5.02 |

### Day of Week Event Distribution
| Day | Count | Percentage | Avg Impact |
|---|---|---|---|
| Monday | 909.0 | 11.12% | 5.75 |
| Tuesday | 1245.0 | 15.23% | 5.89 |
| Wednesday | 1162.0 | 14.22% | 5.83 |
| Thursday | 1343.0 | 16.43% | 6.03 |
| Friday | 1245.0 | 15.23% | 5.93 |
| Saturday | 1223.0 | 14.96% | 5.82 |
| Sunday | 930.0 | 11.38% | 5.50 |

## 6. Hotspot Junctions (Top 30)
| Junction | Count | Avg Impact | Closure Rate | Latitude | Longitude |
|---|---|---|---|---|---|
| MekhriCircle | 64 | 5.30 | 1.6% | 13.014602 | 77.583981 |
| AyyappaTempleJunc | 49 | 5.98 | 2.0% | 12.923716 | 77.618662 |
| SatteliteBusStandJunc | 43 | 5.23 | 2.3% | 12.954126 | 77.543464 |
| YeshwanthpuraCircle | 38 | 5.62 | 2.6% | 13.017761 | 77.556973 |
| YelhankaCircle | 34 | 6.34 | 0.0% | 13.094322 | 77.595927 |
| SilkBoardJunc | 33 | 6.02 | 12.1% | 12.917013 | 77.622874 |
| toll gate mysore road | 33 | 5.57 | 6.1% | 12.957494 | 77.551884 |
| Nagavara-ORR Junction | 32 | 6.36 | 6.2% | 13.039600 | 77.624190 |
| JalahalliCross(SM Circle) | 32 | 5.30 | 0.0% | 13.040089 | 77.518302 |
| K R Circle | 31 | 5.34 | 29.0% | 12.976696 | 77.586048 |
| KIMCO Junction | 31 | 5.85 | 6.5% | 12.951140 | 77.538003 |
| VeerannapalyaJunction(BEL,HO) | 30 | 7.61 | 23.3% | 13.041578 | 77.613660 |
| Devasandra(k r puram) | 30 | 4.88 | 13.3% | 13.009463 | 77.696157 |
| TownhallJunction | 30 | 5.40 | 6.7% | 12.963982 | 77.584377 |
| HesaraghattaJunction | 30 | 5.15 | 3.3% | 13.045216 | 77.507432 |
| KoramangalaWaterTankJunc | 29 | 6.22 | 0.0% | 12.927340 | 77.620973 |
| HebbalFlyoverJunc | 28 | 6.76 | 14.3% | 13.042259 | 77.590922 |
| GokuldasImagesJunc | 28 | 5.59 | 0.0% | 13.030656 | 77.536423 |
| BagalurCrossJunc | 27 | 5.50 | 3.7% | 13.122026 | 77.610863 |
| Bommanahalli | 26 | 6.00 | 0.0% | 12.906964 | 77.628165 |
| BigBazaarJunction(OldMadrasRd) | 26 | 5.72 | 3.8% | 12.991387 | 77.657421 |
| PoliceCornerJunc | 26 | 5.68 | 15.4% | 12.968715 | 77.587036 |
| SantheCircle | 25 | 6.63 | 20.0% | 13.097470 | 77.598195 |
| BEL Circle | 25 | 6.00 | 8.0% | 13.044357 | 77.555854 |
| KhodaysCircle(DV UrsCircle) | 23 | 4.37 | 4.3% | 12.980188 | 77.571559 |
| RajeshwariJunc | 22 | 6.12 | 18.2% | 12.936725 | 77.519071 |
| LeprosyhospitalJunc | 21 | 6.15 | 14.3% | 12.975538 | 77.564240 |
| GoruguntepalyaJunc | 20 | 5.42 | 5.0% | 13.029652 | 77.540355 |
| SRS Peenya Junc | 20 | 5.80 | 5.0% | 13.034509 | 77.529849 |
| CMP GateJunc | 20 | 6.68 | 15.0% | 12.957914 | 77.605855 |

## 7. Zone Distribution
| Zone | Count | Avg Impact | Closure Rate |
|---|---|---|---|
| Central Zone 2 | 623 | 5.34 | 8.7% |
| West Zone 1 | 433 | 5.49 | 6.7% |
| North Zone 2 | 413 | 5.62 | 5.3% |
| West Zone 2 | 358 | 5.54 | 4.5% |
| South Zone 2 | 354 | 5.89 | 5.1% |
| North Zone 1 | 318 | 6.35 | 10.1% |
| Central Zone 1 | 269 | 6.00 | 14.1% |
| East Zone 1 | 253 | 6.25 | 5.9% |
| South Zone 1 | 233 | 5.87 | 4.7% |
| East Zone 2 | 190 | 5.57 | 14.2% |

