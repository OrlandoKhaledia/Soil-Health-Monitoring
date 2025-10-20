import os
import datetime
import uuid
import json
from flask import Flask, request, jsonify, render_template, make_response
from supabase import create_client, Client
import numpy as np
from dotenv import load_dotenv
import ee
from models.soil_ai_model import predict_soil_health
from weasyprint import HTML
import folium

app = Flask(__name__, static_folder='static', template_folder='templates')
load_dotenv()

# ------------------------
# Inject current datetime into all templates (fixes {{ now() }})
# ------------------------
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now}

# ------------------------
# Environment variables
# ------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "REPLACE_ME")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "REPLACE_ME")
EE_SERVICE_ACCOUNT = os.getenv("EE_SERVICE_ACCOUNT", "")
EE_KEY_PATH = os.getenv("EE_KEY_PATH", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------
# Initialize Earth Engine
# ------------------------
ee_initialized = False
ee_init_error = None
try:
    if EE_SERVICE_ACCOUNT and EE_KEY_PATH and os.path.exists(EE_KEY_PATH):
        credentials = ee.ServiceAccountCredentials(EE_SERVICE_ACCOUNT, EE_KEY_PATH)
        ee.Initialize(credentials)
    else:
        ee.Initialize()
    ee_initialized = True
except Exception as e:
    ee_init_error = str(e)
    print("⚠️ Earth Engine init failed:", ee_init_error)

# ------------------------
# AI Recommendation Function
# ------------------------
def ai_recommendation(score):
    if score < 0.2:
        return "🚨 Severe degradation — consider reforestation, cover crops, and soil restoration."
    elif score < 0.4:
        return "⚠️ Moderate degradation — apply soil fertility improvement and erosion control."
    elif score < 0.6:
        return "🙂 Stable soil — maintain current land management."
    else:
        return "🌿 Healthy soil — continue sustainable farming practices."

# ------------------------
# Routes
# ------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    try:
        result = supabase.auth.sign_up({"email": email, "password": password})
        user = result.user
        if user:
            return jsonify({"message": "Signup successful", "user_id": user.id, "email": user.email})
        else:
            return jsonify({"error": "Signup failed"}), 500
    except Exception as e:
        return jsonify({"error": f"Signup failed: {e}"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(force=True)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    try:
        result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session = result.session
        user = result.user
        if not user:
            return jsonify({"error": "Login failed"}), 500
        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "email": user.email,
            "access_token": session.access_token
        })
    except Exception as e:
        return jsonify({"error": f"Login failed: {e}"}), 500

# ------------------------
# Compute NDVI & AI Insight
# ------------------------
@app.route('/api/compute_ndvi', methods=['POST'])
def compute_ndvi():
    data = request.get_json(force=True) or {}
    geojson = data.get("feature")
    user_id = data.get("user_id")
    if not geojson or not user_id:
        return jsonify({"error": "Missing geometry or user_id"}), 400

    parcel_id = f"parcel-{uuid.uuid4()}"
    parcel_name = data.get("name", parcel_id)

    try:
        polygon = ee.Geometry(geojson["geometry"])
    except Exception as geom_err:
        return jsonify({"error": f"Invalid geometry: {geom_err}"}), 400

    ndvi_vals = []
    series = []
    score = 0.0
    message = ""

    if ee_initialized:
        try:
            collection = (
                ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
                .filterBounds(polygon)
                .filterDate("2023-01-01", datetime.date.today().isoformat())
                .map(lambda img: img.normalizedDifference(['SR_B5', 'SR_B4'])
                     .rename('NDVI')
                     .copyProperties(img, ['system:time_start']))
            )

            # Use safer aggregation
            features = collection.map(
                lambda image: ee.Feature(None, {
                    'date': image.date().format('YYYY-MM-dd'),
                    'ndvi': image.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=polygon,
                        scale=100,
                        maxPixels=1e10,
                        bestEffort=True
                    ).get('NDVI')
                })
            ).filter(ee.Filter.notNull(['ndvi'])).getInfo().get('features', [])

            if not features:
                raise ValueError("No NDVI values found")

            series = [{"date": f['properties']['date'], "ndvi": round(f['properties']['ndvi'], 4)}
                      for f in features if f['properties'].get('ndvi') is not None]
            ndvi_vals = [f['properties']['ndvi'] for f in features if f['properties'].get('ndvi') is not None]
            score = round(max(0.0, -np.polyfit(range(len(ndvi_vals)), ndvi_vals, 1)[0] * 100), 2)
            message = "✅ NDVI computed from Landsat 8 SR real data"
        except Exception as ee_err:
            # fallback simulation
            ndvi_vals = [round(0.6 + np.random.uniform(-0.05, 0.05), 4) for _ in range(12)]
            today = datetime.date.today()
            dates = [(today - datetime.timedelta(days=30 * i)).isoformat() for i in reversed(range(len(ndvi_vals)))]
            series = [{"date": d, "ndvi": v} for d, v in zip(dates, ndvi_vals)]
            score = 0.0
            message = f"⚠️ NDVI simulation used. Earth Engine error: {ee_err}"
    else:
        ndvi_vals = [round(0.6 + np.random.uniform(-0.05, 0.05), 4) for _ in range(12)]
        today = datetime.date.today()
        dates = [(today - datetime.timedelta(days=30 * i)).isoformat() for i in reversed(range(len(ndvi_vals)))]
        series = [{"date": d, "ndvi": v} for d, v in zip(dates, ndvi_vals)]
        score = 0.0
        message = f"⚠️ NDVI simulation used. EE init failed: {ee_init_error}"

    ai_insight = predict_soil_health(ndvi_vals)
    ai_message = ai_recommendation(score)

    # Save to Supabase
    if supabase:
        try:
            supabase.table('parcels').insert({
                'id': parcel_id,
                'user_id': user_id,
                'name': parcel_name,
                'geom': json.dumps(geojson),
                'ai_insight': json.dumps({"ai_insight": ai_insight, "series": series})
            }).execute()
        except Exception as db_err:
            print("⚠️ Failed to save parcel:", db_err)

    return jsonify({
        "parcel_id": parcel_id,
        "series": series,
        "degradation_score": score,
        "ai_insight": ai_insight,
        "ai_message": ai_message,
        "message": message
    })

# ------------------------
# Map, trend, and PDF endpoints remain unchanged
# ------------------------
@app.route('/api/ndvi_map', methods=['POST'])
def ndvi_map():
    data = request.get_json(force=True) or {}
    geojson = data.get("feature")
    if not geojson:
        return jsonify({"error": "Missing geometry"}), 400

    try:
        geom = ee.Geometry(geojson["geometry"])
        latlon = geom.centroid().coordinates().getInfo()
        lat, lon = latlon[1], latlon[0]

        image = (
            ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
            .filterBounds(geom)
            .filterDate("2023-01-01", datetime.date.today().isoformat())
            .sort("CLOUD_COVER")
            .first()
        )
        ndvi = image.normalizedDifference(["SR_B5", "SR_B4"]).rename("NDVI")
        vis_params = {"min": 0, "max": 1, "palette": ["brown", "yellow", "green"]}

        m = folium.Map(location=[lat, lon], zoom_start=12)
        folium.TileLayer("OpenStreetMap").add_to(m)
        map_id = ndvi.getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id["tile_fetcher"].url_format,
            attr="Google Earth Engine",
            overlay=True,
            name="NDVI",
        ).add_to(m)
        folium.LayerControl().add_to(m)

        file_path = os.path.join("templates", "ndvi_map.html")
        m.save(file_path)

        return jsonify({"map_url": "/ndvi_map"})
    except Exception as e:
        return jsonify({"error": f"Map generation failed: {e}"}), 500

@app.route('/ndvi_map')
def serve_ndvi_map():
    return render_template("ndvi_map.html")

@app.route('/api/download_report/<parcel_id>', methods=['GET'])
def download_report(parcel_id):
    resp = supabase.table('parcels').select('*').eq('id', parcel_id).single().execute()
    parcel = resp.data
    if not parcel:
        return jsonify({"error": "Parcel not found"}), 404
    html = render_template('report_template.html', parcel=parcel)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=soil_report_{parcel_id}.pdf'
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)), debug=True)
