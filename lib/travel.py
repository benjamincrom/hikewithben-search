#!/usr/bin/python
'''
travel.py -- this module contains helper functions which caluculate distance
and duration of travel between points.
'''
import os
import json
import requests

import numpy


GOOGLE_MAPS_API_URL = ('https://maps.googleapis.com/maps/api/distancematrix/'
                       'json?origins=%s,%s&destinations=%s,%s&mode=driving&key'
                       '=%s')

GOOGLE_MAPS_GEOCODING_URL = ('https://maps.googleapis.com/maps/api/geocode/json'
                             '?address=%s&key=%s')

EARTH_RADIUS_MILES = 3959.0
SECONDS_IN_HOUR = 3600.0
METERS_IN_MILE = 1609.34

def geocode_address(address_str):
    '''
    Given address search string return coordinate (uses Google Maps API)
    '''
    try:
        google_maps_api_response = requests.get(
            GOOGLE_MAPS_GEOCODING_URL % (
                address_str,
                os.environ['GOOGLE_MAPS_API_KEY']
            )
        )
    except requests.exceptions.ConnectionError:
        google_maps_api_response = None

    home_coordinate = ()
    if google_maps_api_response:
        response_dict = json.loads(google_maps_api_response.text)
        if response_dict.get('results'):
            location_dict = response_dict['results'][0]['geometry']['location']
            home_coordinate = (float(location_dict['lat']),
                               float(location_dict['lng']))

    return home_coordinate

def distance_dict_from_coordinate(origin_coordinate, coordinates_list):
    '''
    Given an origin coordinate and a list of destination coordinates,
    calculate a list of distances to each coordinate.  Returns a dictionary
    where each key is a distance and value is a destination point.
    '''
    origin_coordinate = [float(origin_coordinate[0]),
                         float(origin_coordinate[1])]

    coordinates_array = numpy.array(coordinates_list)
    all_latitudes_array = numpy.radians(coordinates_array[:, 0])
    all_longitudes_array = numpy.radians(coordinates_array[:, 1])
    origin_latitude = numpy.radians(origin_coordinate[0])
    origin_longitude = numpy.radians(origin_coordinate[1])

    lat_diff_array = all_latitudes_array - origin_latitude
    lon_diff_array = all_longitudes_array - origin_longitude

    calc_array = (
        numpy.square(numpy.sin(lat_diff_array/2.0)) +
        numpy.cos(origin_latitude) *
        numpy.cos(all_latitudes_array) *
        numpy.square(numpy.sin(lon_diff_array/2.0))
    )

    great_circle_distance_array = (
        2 *
        numpy.arcsin(
            numpy.minimum(
                numpy.sqrt(calc_array),
                numpy.repeat(1, len(calc_array))
            )
        )
    )

    distance_array = great_circle_distance_array * EARTH_RADIUS_MILES
    distance_coordinate_dict = {
        distance_array[i]: (float(coordinates_array[i][0]),
                            float(coordinates_array[i][1]))
        for i in range(len(coordinates_array))
    }

    return distance_coordinate_dict

def travel_between_coordinates(origin_coordinate,
                               destination_coordinate):
    '''
    Return duration and distance according to google maps between two (lat, lon)
    points
    '''
    try:
        google_maps_api_response = requests.get(
            GOOGLE_MAPS_API_URL % (
                origin_coordinate[0],
                origin_coordinate[1],
                destination_coordinate[0],
                destination_coordinate[1],
                os.environ['GOOGLE_MAPS_API_KEY']
            )
        )
    except requests.exceptions.ConnectionError:
        google_maps_api_response = None

    travel_dict = None
    if google_maps_api_response:
        response_dict = json.loads(google_maps_api_response.text)
        if response_dict['rows']:
            travel_dict = extract_duration_and_distance(response_dict)

    return travel_dict

def extract_duration_and_distance(response_dict):
    '''
    Given a directions response dictionary from the Google Maps API, return a
    dictionary containing only the duration and distance of the trip.
    '''
    travel_duration_dict = response_dict['rows'][0]['elements'][0].get(
        'duration'
    )
    travel_distance_dict = response_dict['rows'][0]['elements'][0].get(
        'distance'
    )

    if travel_duration_dict:
        travel_duration_hours = travel_duration_dict['value'] / SECONDS_IN_HOUR
    else:
        travel_duration_hours = None

    if travel_distance_dict:
        travel_distance_miles = travel_distance_dict['value'] / METERS_IN_MILE
    else:
        travel_distance_miles = None

    travel_dict = {'duration': travel_duration_hours,
                   'distance': travel_distance_miles}

    return travel_dict
