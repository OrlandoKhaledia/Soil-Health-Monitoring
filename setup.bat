@echo off
REM ------------------------------
REM Soil Health Dashboard Setup
REM ------------------------------

echo ===============================================
echo Setting up Soil Health Dashboard Environment
echo ===============================================

REM Step 1: Remove existing venv (optional)
IF EXIST venv (
    echo Removing old virtual environment...
    rmdir /s /q venv
)

REM Step 2: Create a new virtual environment
echo Creating virtual environment...
python -m venv venv

REM Step 3: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Step 4: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Step 5: Install dependencies
echo Installing dependencies...
pip install Flask>=2.3.2 supabase>=1.0.0 numpy>=1.26.2 python-dotenv>=1.0.0 earthengine-api>=0.1.319 weasyprint>=59.0 folium>=0.16.0 requests>=2.31.0

REM Step 6: Confirm installations
echo Verifying installations...
python -c "import folium; print('folium version:', folium.__version__)"
python -c "import supabase; print('supabase version:', supabase.__version__)"
python -c "import ee; print('earthengine-api version:', ee.__version__)"

REM Step 7: Run Flask app
echo Launching Flask server...
set FLASK_APP=app.py
set FLASK_ENV=development
flask run --host=0.0.0.0 --port=7860

pause
