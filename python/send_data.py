from astrophotos import get_coords, ranking, to_cc
from pprint import pprint
import sys

def call_astrophotos(city:str, country:str, start_year:int, start_month: int, start_day:int, end_year:int, end_month:int, end_day:int, start_time:str, end_time:str, offset: int):
    city, country_code = get_coords("Morristown", to_cc("United States"))
    pprint(ranking(start_year, start_month, start_day, end_year, end_month, end_day, start_time, end_time, offset))