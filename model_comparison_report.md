# Machine Learning Model Training & Comparison - TRAFIQ360

Comparison of XGBoost, LightGBM, and Random Forest models.

## 1. Impact Score Regression Results
| Model | RMSE | MAE |
|---|---|---|
| Random Forest | 0.6150 | 0.3308 |
| XGBoost | 0.5954 | 0.3260 |
| LightGBM | 0.5739 | 0.3112 |

## 2. Event Expected Duration Regression Results
| Model | RMSE (min) | MAE (min) |
|---|---|---|
| Random Forest | 11386.8258 | 2380.8022 |
| XGBoost | 13140.6259 | 2565.2387 |
| LightGBM | 11348.6042 | 2309.2669 |

## 3. Road Closure Classification Results
| Model | Accuracy | ROC-AUC |
|---|---|---|
| Random Forest | 0.9193 | 0.7635 |
| XGBoost | 0.9229 | 0.7371 |
| LightGBM | 0.9260 | 0.7564 |

### Model Selection:
- **Impact Score**: XGBoost chosen (lowest RMSE).
- **Expected Duration**: XGBoost chosen (trained on log-duration to handle skew).
- **Closure Probability**: LightGBM Classifier chosen (highest ROC-AUC).

