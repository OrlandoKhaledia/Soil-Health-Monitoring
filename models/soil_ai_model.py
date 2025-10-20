import numpy as np

def predict_soil_health(ndvi_series):
    """
    Simple AI placeholder for soil health prediction.
    Returns a string based on NDVI trend.
    
    ndvi_series: list of NDVI float values (0.0 - 1.0)
    """
    if not ndvi_series or len(ndvi_series) == 0:
        return "No data"

    trend = np.polyfit(range(len(ndvi_series)), ndvi_series, 1)[0]

    if trend < -0.05:
        return "Soil degrading"
    elif trend < 0.05:
        return "Soil stable"
    else:
        return "Soil improving"
