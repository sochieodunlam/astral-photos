from geopy.geocoders import Nominatim
from skyfield.api import load, wgs84, Star
from datetime import datetime, timezone
from pprint import pprint
from collections import defaultdict
import pycountry
eph = load('de421.bsp')
ts = load.timescale()
sun = eph['sun']
earth = eph['earth']
galaxy_center = Star(ra_hours=(17 + 45/60 + 40/3600), dec_degrees=-(29 + 0/60 + 28/3600))
georeverse = Nominatim(user_agent="astro_app")

'''
ATTENTION!

Go to line 179 to change the location. Go to
the end of the file in order to run the ranking function
which will give the final output

'''
#retreive coordinates
def load_admin1(admin_path="admin1CodesASCII.txt"):
    name_to_code = {}   # (cc, admin_name_lower) -> code
    code_to_name = {}   # (cc, code) -> admin_name
    with open(admin_path, encoding="utf-8") as f:
        for line in f:
            key, name, *_ = line.rstrip("\n").split("\t")
            cc, code = key.split(".")
            code_to_name[(cc, code)] = name
            name_to_code[(cc, name.lower())] = code
    return name_to_code, code_to_name

def load_cities(cities_path="cities1000.txt", code_to_name=None):
    by_place = {}  # (city_lower, cc, admin_name_lower) -> (lat, lon)
    with open(cities_path, encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            city = p[1]
            lat, lon = float(p[4]), float(p[5])
            cc = p[8]
            admin1_code = p[10]
            admin1_name = code_to_name.get((cc, admin1_code), admin1_code) if code_to_name else admin1_code
            by_place[(city.lower(), cc, str(admin1_name).lower())] = (lat, lon)
    return by_place



name_to_code, code_to_name = load_admin1()
coords = load_cities(code_to_name=code_to_name)


def to_cc(country: str) -> str:
    country = country.strip()
    if len(country) == 2:
        return country.upper()
    return pycountry.countries.lookup(country).alpha_2

#to_cc("France")  # "FR"
#to_cc("fr")      # "FR"
by_full = {}                      
by_city = defaultdict(list)        

with open("cities1000.txt", encoding="utf-8") as f:
    for line in f:
        p = line.rstrip("\n").split("\t")
        city = p[1].strip().lower()
        cc = p[8].strip().upper()
        admin = p[10].strip()          # code, or map to name if you loaded admin1 names
        lat, lon = float(p[4]), float(p[5])
        pop = int(p[14] or 0)

        by_full[(city, cc, admin)] = (lat, lon, pop)
        by_city[(city, cc)].append((admin, lat, lon, pop))

for k in by_city:
    by_city[k].sort(key=lambda x: x[3], reverse=True)

def get_coords(city, country_code, admin=None):
    city = city.strip().lower()
    cc = country_code.strip().upper()

    if admin is not None:
        a = admin.strip()
        lat, lon, _ = by_full[(city, cc, a)]
        return lat, lon

    candidates = by_city.get((city, cc), [])
    if not candidates:
        raise KeyError("city not found")
    if len(candidates) == 1:
        _, lat, lon, _ = candidates[0]
        return lat, lon

    # multiple matches: return the biggest by population + the alternatives
    best = candidates[0]
    return (best[1], best[2]), candidates

def key(city, cc, admin):
    return (city.strip().lower(), cc.strip().upper(), admin.strip().lower())

class UTC:
    '''
    Given a time, it can return the minutes (which will be the same) the hour in UTC, or given a
    time in UTC it can convert it back to the original time. Input in HH:MM.
    '''
    def __init__ (self):
        pass
    def hour(self, offset, time):
        '''
        Returns: your current hour, converted to UTC
        '''    
        if time[2] != ':':
            raise ValueError('invalid time format! Use HH:MM')
        if int(time[3:]) >= 60 or int(time[:2]) < 0 or int(time[:2]) > 24:
            raise ValueError('Minutes / Hours are outside of bounds!')
        converted_hour = (int(time[0:2]) - offset) % 24
        return converted_hour
    
    def minute(self, time):
        if time[2] != ':':
            raise ValueError('invalid time format! Use HH:MM')
        if int(time[3:]) >= 60 or int(time[:2]) < 0 or int(time[:2]) > 24:
            raise ValueError('Minutes / Hours are outside of bounds!')
        return int(time[3:])
    
    def revert(self, offset, time):
        '''
        Takes a UTC time and reverts the hour back to the
        original timezone hour
        '''
        if time[2] != ':':
            raise ValueError('invalid time format! Use HH:MM')
        if int(time[3:]) >= 60 or int(time[:2]) < 0 or int(time[:2]) > 24:
            raise ValueError('Minutes / Hours are outside of bounds!')
        reverted_hour = (int(time[0:2]) + offset) % 24
        return reverted_hour

class City:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="astrophotos_program", timeout = 10)
    def coords(self, city):
        """
        Takes a city as a string and returns its longitude.
        """
        location = self.geolocator.geocode(city, exactly_one=True)
        if location == None:
            raise ValueError(f'{city} not found in database!')
        return location.latitude, location.longitude

def sun_altitude(lati, longi, utc_dt):
    """
    Calculates the Sun's altitude (degrees) at lati/longi at a given UTC datetime.
    utc_dt should be timezone-aware and in UTC.
    """
    if utc_dt.tzinfo is None:
        raise ValueError("utc_dt must be timezone-aware (UTC).")
    utc_dt = utc_dt.astimezone(timezone.utc)

    observer = earth + wgs84.latlon(lati, longi)
    t = ts.from_datetime(utc_dt)
    alt, az, _ = observer.at(t).observe(sun).apparent().altaz()
    return alt.degrees

def core_altitude(lati, longi, utc_dt):
    '''
    Uses the star position from before, calculate the altitude at the galaxy's core
    '''
    observer = earth + wgs84.latlon(lati, longi)
    timescale = ts.from_datetime(utc_dt)  
    alt, az, _ = observer.at(timescale).observe(galaxy_center).apparent().altaz()
    return alt.degrees

clock = UTC()
city = City() 

#Uncomment and use this format if including provinces
#latitude, longitude = coords[key("rosario", to_cc("argentina"), "santa Fe")] 
latitude, longitude = get_coords('Sydney', to_cc('Australia'))


def score(year, month, day, offset, time, end_time, good_hours=0, library=None):
    '''
    Given a date, this function returns the amount of hours that
    meet the conditions for good astrophotography. Additionally, a
    number is also returned indicating the amount of 'good' hours
    for astrophotography in a given time range.
    '''

    end_hours = int(end_time.split(":")[0]) % 24 # expects "HH:MM"
    utc_dt = datetime(year, month, day, clock.hour(offset, time), clock.minute(time), tzinfo=timezone.utc)
    
    time = time.replace(':', '')
    minutes = time[-2:]
    hours = time[:-2]
    hours = int(hours) % 24

    if hours == 0 and library is not None: #changes the day/month when it goes overnight

        if month == 4 or month == 6 or month == 9 or month == 11: #30 day month
            day = (day % 30) + 1
            if day == 1:
                month += 1

        elif month == 2 and (year % 4) == 0 and (year % 100) != 0: #leap year check 1 (february)
            day = (day % 29) + 1
            if day == 1:
                month += 1

        elif month == 2 and (year % 400) == 0: #leap year check 2 (february)
            day = (day % 29) + 1
            if day == 1:
                month += 1

        elif month == 2: #non leap year (february)
            day = (day % 28) + 1
            if day == 1:
                month += 1

        elif month == 12 and day == 31: #New Years Eve
            day = 1
            month = 1
            year += 1

        elif month not in (4, 6, 9, 11): #31 day month
            day = (day % 31) + 1
            if day == 1:
                month += 1

    if library is None:
        library = []
    if hours == end_hours: 
        if good_hours == 0:
            library.append((f"{year:04d}-{month:02d}-{day:02d}", "No good hours!"))
        return good_hours, library
    
    mwc_alt = core_altitude(latitude, longitude, utc_dt) 
    sun_alt = sun_altitude(latitude, longitude, utc_dt) 

    if mwc_alt > 20 and sun_alt < -18:
        good_hours += 1
        library.append((f"{year:04d}-{month:02d}-{day:02d}", f"{hours:02d}:{minutes}"))
    hours = (hours + 1) % 24
    time = f"{hours:02d}:{minutes}" 
       
    return score(year, month, day, offset, time, end_time, good_hours, library)


def ranking(year, month, day, end_year, end_month, end_day, time, end_time, offset, tally=None):
    '''
    Given a date range, the function will return a ranking of the
    best nights for taking astrophotos, where the hours shown
    are optimal for astrophotos. Offset arguement is the difference
    between your timezone and UTC.

    Format:
    "[(# of good hours, [(date, optimal hour 1), (date, optimal hour 2)])]

   
    '''
    if tally is None:
        tally = []

    if year == end_year and month == end_month and day == end_day:
        
        return sorted(tally, reverse=True)
    else:
        ovr_score = score(year, month, day, offset, time, end_time, good_hours=0, library=None)
        tally.append(ovr_score)

        if month == 4 or month == 6 or month == 9 or month == 11: #30 day month
            day = (day % 30) + 1
            if day == 1:
                month += 1
          
        elif month == 2 and (year % 4) == 0 and (year % 100) != 0: #leap year check 1 (february)
            day = (day % 29) + 1
            if day == 1:
                month += 1

        elif month == 2 and (year % 400) == 0: #leap year check 2 (february)
            day = (day % 29) + 1
            if day == 1:
                month += 1

        elif month == 2: #non leap year (february)
            day = (day % 28) + 1
            if day == 1:
                month += 1

        elif month == 12 and day == 31: #New Years Eve
            day = 1
            month = 1
            year += 1

        elif month not in (4, 6, 9, 11): #31 day month
            day = (day % 31) + 1
            if day == 1:
                month += 1
           
    return ranking(year, month, day, end_year, end_month, end_day, time, end_time, offset, tally)
   
# data = ranking(2026, 6, 7, 2026, 6, 17, "20:00", '23:00', 11)
# pprint(data, width=80) #use pretty print!


'''
Disclaimer: Summer Months tend to be better, so it is
likely that you will get 0 good hours regardless of the location
in the winter time.

Disclaimer 2: Request with >990 days likely won't process due to
python's recursion stack being exceeded
'''