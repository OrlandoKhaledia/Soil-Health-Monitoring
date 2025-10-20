# Soil Health Intelligence System

A client-ready web system leveraging AI and real-time data analytics to help stakeholders (farmers, policymakers, NGOs) monitor land conditions, identify degradation trends, and receive actionable recommendations to restore ecosystem health.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Environment Setup](#environment-setup)
6. [Running the Application](#running-the-application)
7. [Python Dependencies](#python-dependencies)
8. [Folder Structure](#folder-structure)
9. [Contributing](#contributing)
10. [License](#license)

---

## Project Overview
This system uses:
- Flask for the backend
- Supabase for database management
- Google Earth Engine for satellite data & NDVI computation
- AI models for soil health prediction
- PDF report generation for actionable insights

---

## Features
- Predict soil health based on AI models
- Generate NDVI maps and degradation trends
- Export PDF reports with actionable recommendations
- Dashboard for monitoring land conditions
- User workflow from parcel input → NDVI computation → AI recommendations → report

---

## Prerequisites
Before running this project, ensure you have:

- Python 3.11 or higher
- Git
- Virtual environment tool (venv or conda)
- Node.js & npm (if frontend uses JS frameworks)
- Access to Google Earth Engine account
- Supabase account (for database)

---

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/soil-health-intelligence.git
cd soil-health-intelligence

2. Create a Python virtual environment
python -m venv venv

3.Activate the environment
venv\Scripts\activate
4. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
5. Install Node.js dependencies (if applicable)
npm install

6. Running the Application
python app.py 
or 
flask run
