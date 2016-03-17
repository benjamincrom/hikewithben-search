#!/usr/bin/python
"""
test_travel.py - unit tests for travel module
"""
import requests
import json

from lib import travel

def test_geocode_location_success():
    test_address = '1600 Pennsylvania Ave, Washington, DC'
    expected = (38.8791981, -76.9818437)
    response = travel.geocode_address(test_address)
    assert response == expected

def test_travel_between_coordinates_good_response():
    response = travel.travel_between_coordinates((33.0, -84.0), (34.0, -85.0))
    assert response['duration'] and response['distance']

def test_extract_duration_and_distance():
    google_maps_api_response = requests.get(
        travel.GOOGLE_MAPS_API_URL % (33.0, -84.0, 34.0, -85.0,
                                      travel.GOOGLE_MAPS_API_KEY)
    )
    response_dict = json.loads(google_maps_api_response.text)
    travel_dict = travel.extract_duration_and_distance(response_dict)
    assert travel_dict['duration'] and travel_dict['distance']

def test_extract_duration_and_distance_no_duration():
    google_maps_api_response = requests.get(
        travel.GOOGLE_MAPS_API_URL % (33.0, -84.0, 34.0, -85.0,
                                      travel.GOOGLE_MAPS_API_KEY)
    )
    response_dict = json.loads(google_maps_api_response.text)
    response_dict['rows'][0]['elements'][0].pop('duration')
    travel_dict = travel.extract_duration_and_distance(response_dict)
    assert travel_dict['duration'] is None

def test_extract_duration_and_distance_no_distance():
    google_maps_api_response = requests.get(
        travel.GOOGLE_MAPS_API_URL % (33.0, -84.0, 34.0, -85.0,
                                      travel.GOOGLE_MAPS_API_KEY)
    )
    response_dict = json.loads(google_maps_api_response.text)
    response_dict['rows'][0]['elements'][0].pop('distance')
    travel_dict = travel.extract_duration_and_distance(response_dict)
    assert travel_dict['distance'] is None

def test_distance_dict_from_coordinate():
    response_dict = travel.distance_dict_from_coordinate((30, -80),
                                                         [(33, -84), (34, -85)])
    assert len(response_dict) == 2

# Destructive changes
def test_travel_between_coordinates_denied_response():
    travel.GOOGLE_MAPS_API_KEY = 'yay'
    response = travel.travel_between_coordinates((33.0, -84.0), (34.0, -85.0))
    assert response is None

def test_travel_between_coordinates_bad_response():
    travel.GOOGLE_MAPS_API_URL = 'https://%s%s%s%s%syay'
    response = travel.travel_between_coordinates((33.0, -84.0), (34.0, -85.0))
    assert response is None
