"""
urls.py (planner app)

Maps URL paths to views for this app specifically. Kept separate from
the project-level urls.py so this app's routes stay self-contained.
"""

from django.urls import path
from .views import PlanTripView

urlpatterns = [
    path("plan-trip/", PlanTripView.as_view(), name="plan-trip"),
]