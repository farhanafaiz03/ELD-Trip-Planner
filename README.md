# ELD Trip Planner

A full-stack app that takes a trip's locations and a driver's current
Hours-of-Service cycle usage, then plans the trip against FMCSA HOS
regulations, showing the route on a map with all required stops, and
generating filled-out daily log sheets, one per day the trip spans.

**Live app:** https://eld-trip-planner-pi-nine.vercel.app/

## Stack

- Backend: Django + Django REST Framework
- Frontend: React (Vite)
- Routing: OSRM (free, no API key)
- Geocoding: OpenStreetMap Nominatim (free, no API key)
- Map rendering: Leaflet / react-leaflet

## Assumptions

- Property-carrying driver on the 70-hour/8-day cycle
- No adverse driving conditions exception
- Fuel stop at least once every 1,000 miles
- 1 hour on-duty for pickup, 1 hour for dropoff

## Running locally

**Backend:**

`cd backend`
`python -m venv venv`
`venv\Scripts\activate`
`pip install -r requirements.txt`
`python manage.py runserver`

**Frontend:**

`cd frontend`
`npm install`
`npm run dev`