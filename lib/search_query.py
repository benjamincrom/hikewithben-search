#!/usr/bin/python
'''
search_query.py - module containing methods for campsite search
'''
import datetime
import json
import os

import redis

from lib.common_utilities import travel

REDIS_URL = os.environ['REDIS_URL']
DEFAULT_PROCESS_POOL_SIZE = 8


class SearchQuery(object):
    '''
    Contain data pulled from redis and methods required to search redis.
    '''
    def __init__(self):
        self.redis_instance = redis.from_url(REDIS_URL)
        self.recarea_list = []
        self.small_recarea_dict = {
            key.split('_')[0]: json.loads(self.redis_instance.get(key))
            for key in self.redis_instance.keys() if key.find('_small') != -1
        }

    def filter_name(self, name_contains_str):
        '''
        Filter recarea ids by name
        '''
        self.small_recarea_dict = {
            recarea_id: recarea
            for recarea_id, recarea in self.small_recarea_dict.iteritems()
            if recarea['RecAreaName'].find(name_contains_str) != -1
        }

    def filter_distance(self, min_distance, max_distance, home_coordinate):
        '''
        Calculate the distance to every recarea and return a sorted dict of
        recareas which fall within distance bounds
        '''
        coordinates_dict = {}
        for recarea_id, recarea in self.small_recarea_dict.iteritems():
            if (recarea.get('RecAreaLatitude') and
                    recarea.get('RecAreaLongitude')):
                coordinate = (float(recarea['RecAreaLatitude']),
                              float(recarea['RecAreaLongitude']))
                coordinates_dict[coordinate] = recarea_id

        if coordinates_dict:
            distance_coordinate_dict = travel.distance_dict_from_coordinate(
                home_coordinate,
                coordinates_dict.keys()
            )
        else:
            distance_coordinate_dict = {}

        recarea_distance_dict = {}
        for distance in distance_coordinate_dict:
            if (distance >= min_distance) and (distance <= max_distance):
                coordinate = (float(distance_coordinate_dict[distance][0]),
                              float(distance_coordinate_dict[distance][1]))
                recarea_id = coordinates_dict[coordinate]
                recarea_distance_dict[recarea_id] = distance

        new_small_recarea_dict = {}
        for recarea_id, recarea in self.small_recarea_dict.iteritems():
            if recarea_id in recarea_distance_dict:
                recarea['distance_from_home'] = int(
                    recarea_distance_dict.get(recarea_id, 'Unknown')
                )
                new_small_recarea_dict[recarea_id] = recarea

        self.small_recarea_dict = new_small_recarea_dict

    @staticmethod
    def remove_res_dates_not_in_weather(recarea_obj, facility):
        '''
        Remove dates from reservation dictionary which are not found in the
        weather dictionary.
        '''
        remove_date_list = [
            reserve_date_str for reserve_date_str in facility['reservation']
            if reserve_date_str not in recarea_obj['RecAreaWeatherDict']
        ]

        for reservation_date_str in remove_date_list:
            facility['reservation'].pop(reservation_date_str)

    @staticmethod
    def remove_dates_not_in_weekend(recarea):
        '''
        Remove dates from the weather dictionary which are not Fridays or
        Saturdays.
        '''
        weekday_date_list = []
        for date_str in recarea.get('RecAreaWeatherDict', {}):
            (year, month, day) = [int(x) for x in date_str.split('-')]
            this_date = datetime.datetime(year, month, day)
            if this_date.weekday() not in [4, 5, 6]:
                weekday_date_list.append(this_date)

        for weekday_date in weekday_date_list:
            recarea['RecAreaWeatherDict'].pop(weekday_date.date().isoformat())

    @staticmethod
    def filter_weather_dict(station_weather_dict, min_temp, max_temp,
                            start_date, finish_date):
        '''
        Remove dates from weather dict which fall outside date and temp
        bounds
        '''
        new_weather_dict = {}
        for date_str in station_weather_dict:
            (year, month, day) = [int(x) for x in date_str.split('-')]
            this_date = datetime.datetime(year, month, day)
            if this_date >= start_date and this_date <= finish_date:
                day_entry_dict = station_weather_dict[date_str]
                if (day_entry_dict['min_temp'] >= min_temp and
                        day_entry_dict['max_temp'] <= max_temp):
                    new_weather_dict[date_str] = day_entry_dict

        return new_weather_dict

    @classmethod
    def filter_reservation_dict(cls, recarea):
        '''
        Remove dates from reservation dict which fall outside date and temp
        bounds and return whether or not this recarea still has a reservable
        facility after filtering by query parameters
        '''
        recarea_is_reservable = False
        for facility in recarea.get('facilities', []):
            if facility.get('reservation'):
                recarea_is_reservable = True
                if 'RecAreaWeatherDict' in recarea:
                    cls.remove_res_dates_not_in_weather(recarea, facility)

                # Add totals to reservation dictionary entries
                for date_dict in facility['reservation'].values():
                    date_dict['TOTAL'] = sum(date_dict.values())

        return recarea_is_reservable

    def apply_recarea_list_filters(self, min_temp, max_temp, start_date,
                                   finish_date, weekends_only,
                                   show_only_available):
        '''
        Filter weather dictionary to only include days which fall within
        temperature and date parameters.
        '''
        filtered_recarea_list = []
        for recarea in self.recarea_list:
            station_weather_dict = recarea.get('RecAreaWeatherDict')

            # Filter weather dictionary by temp and date bounds
            if station_weather_dict:
                recarea['RecAreaWeatherDict'] = self.filter_weather_dict(
                    station_weather_dict,
                    min_temp,
                    max_temp,
                    start_date,
                    finish_date,
                )

            if weekends_only:
                self.remove_dates_not_in_weekend(recarea)

            recarea_is_reservable = self.filter_reservation_dict(recarea)
            if recarea_is_reservable:
                filtered_recarea_list.append(recarea)

        if show_only_available:
            self.recarea_list = filtered_recarea_list

    @staticmethod
    def extract_dates(query_parameter_dict):
        '''
        Extract dates from query parameter dict and format them to refer to
        the current year.
        '''
        start_date = datetime.datetime.strptime(
            query_parameter_dict.get(
                'start_date',
                '{}-01-01'.format(datetime.datetime.today().year)
            ),
            '%Y-%m-%d'
        )

        finish_date = datetime.datetime.strptime(
            query_parameter_dict.get(
                'finish_date',
                '{}-12-31'.format(datetime.datetime.today().year)
            ),
            '%Y-%m-%d'
        )

        return start_date, finish_date

    def sort_recareas_and_facilities(self):
        '''
        Sort recareas first by distance_from_home and then sort facilities
        belonging to that recarea by name
        '''
        # Sort recareas by distance
        self.recarea_list = sorted(self.recarea_list,
                                   key=lambda k: k['distance_from_home'])
        # Sort facilities by name
        for recarea in self.recarea_list:
            if 'facilities' in recarea:
                recarea['facilities'] = sorted(recarea['facilities'],
                                               key=lambda k: k['FacilityName'])

    def search(self, query_parameter_dict):
        '''
        Search recareas by criteria in query_parameter_dict:
            - home_address_str (datatype: str, required)
            - name_contains_str (datatype: str, optional)
            - min_distance (unit: miles, datatype: float, default: 0)
            - max_distance (unit: miles, datatype: float, default: 100000)
            - min_temp (unit: degrees Fahrenheit, datatype: int, default: -1000)
            - max_temp (unit: degrees Fahrenheit, datatype: int, default: 1000)
            - start_date (datatype: datetime, default: first day of this year)
            - finish_date (datatype: datetime, default: last day of this year)
            - weekends_only (datatype: bool, default: None)
            - show_only_available (datatype: bool, default: None)
        '''
        min_distance = int(query_parameter_dict.get('min_distance', 0))
        max_distance = int(query_parameter_dict.get('max_distance', 100000))
        (start_date, finish_date) = self.extract_dates(query_parameter_dict)
        home_coordinate = travel.geocode_address(
            query_parameter_dict['home_address_str']
        )

        # Pre-filter the small_recarea_dict
        if query_parameter_dict.get('name_contains_str'):
            self.filter_name(query_parameter_dict['name_contains_str'])

        self.filter_distance(min_distance, max_distance, home_coordinate)

        # Load full recarea list
        self.recarea_list = [json.loads(self.redis_instance.get(recarea_id))
                             for recarea_id in self.small_recarea_dict]

        # Copy distances from small recarea list to the large recarea list
        for recarea in self.recarea_list:
            recarea_id_str = str(recarea['RecAreaID'])
            small_recarea = self.small_recarea_dict[recarea_id_str]
            recarea['distance_from_home'] = small_recarea['distance_from_home']

        # Apply remaining filters
        self.apply_recarea_list_filters(
            int(query_parameter_dict.get('min_temp', -1000)),
            int(query_parameter_dict.get('max_temp', 1000)),
            start_date,
            finish_date,
            query_parameter_dict.get('weekends_only'),
            query_parameter_dict.get('show_only_available')
        )

        self.sort_recareas_and_facilities()

        return self.recarea_list
