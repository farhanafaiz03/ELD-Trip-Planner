"""
serializers.py

Defines what a valid trip-planning request looks like, and rejects
anything that doesn't match before it ever reaches the parts of the
app that do real work (geocoding, routing, HOS math). Think of it as
the front door bouncer - nothing gets past here unless it's legit.
"""

from rest_framework import serializers


class TripRequestSerializer(serializers.Serializer):
    current_location = serializers.CharField(max_length=255)
    pickup_location = serializers.CharField(max_length=255)
    dropoff_location = serializers.CharField(max_length=255)
    cycle_hours_used = serializers.FloatField(min_value=0, max_value=70)