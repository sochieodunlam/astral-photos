from astrophotos import get_coords, ranking, to_cc
from pprint import pprint

city, country_code = get_coords("Sydney", to_cc("Australia"))
pprint(ranking(2026, 6, 7, 2026, 6, 17, "20:00", '23:00', 11))