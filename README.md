### HikeWithBen REST API Resources
##### lib.search_query.search(query_dict)
##### query_dict schema:
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

curl -fsSL https://get.docker.com/ | sh
sudo docker run --name hikewithben-redis -d redis
sudo docker run --name hikewithben -p 80:80 --link hikewithben-redis:redis -e REDIS_URL="redis://redis:6379" -e GOOGLE_MAPS_API_KEY="" -d benjamincrom/hikewithben:latest
