import enum
import logging
import requests
import urllib.parse

from datetime import date, datetime, timedelta

# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ----------------------------------------------------------------------
class Week(enum.Enum):
    last = 1
    this = 2
    next = 3


# ----------------------------------------------------------------------
def get_week_from_text(text_week):
    """ helper function to map text representations of a week to Week enum """
    txt = text_week.lower()
    if (txt == "last"):
        wk = Week.last
    elif (txt == "this"):
        wk = Week.this
    elif (txt == "next"):
        wk = Week.next
    else:
        wk = None
        logger.error(
            f'get_week_from_text: invalid argument: week={text_week}')

    return wk


# ----------------------------------------------------------------------
class Movie:
    """ class which represents a single movie """
    def __init__(self, title, overview, release_date, poster_path):
        self.title = title
        self.overview = overview
        self.release_date = release_date
        if (poster_path is None):
            self.image = self.thumbnail = None
        else:
            self.image = 'https://image.tmdb.org/t/p/w500' + poster_path
            self.thumbnail = 'https://image.tmdb.org/t/p/w92' + poster_path


# ----------------------------------------------------------------------
class MovieSearch:
    """ class responsible for querying TMDB and formatting APL results """
    # https://developers.themoviedb.org/3/configuration/get-api-configuration
    API_KEY = '[REPLACE WITH TMDB API KEY]'
    BASE_URL_DISCOVER = 'https://api.themoviedb.org/3/discover/movie'
    BASE_URL_SEARCH = 'https://api.themoviedb.org/3/search/movie'

    # ------------------------------------------------------------------
    def __init__(self, region='GB', release_type='3'):
        """ constructor - defaults to movies released in GB cinemas """
        self.region = region
        self.release_type = release_type
        self.movies = {}
        self.week = None

    # ------------------------------------------------------------------
    def format_date(self, date):
        """ format a date string suitable for use in TMDB queries """
        return date.strftime('%Y-%m-%d')

    # ------------------------------------------------------------------
    def get_apl_launch(self):
        """ return input data for the APL_DOC['launch'] APL document """
        # https://developer.amazon.com/en-US/docs/alexa/alexa-presentation-language/apl-alexa-headline-layout.html
        apl_data = {
            "launchData": {
                "primaryText": f"New Movies ({self.region})",
                "secondaryText": ("I can tell you what new movies have been"
                                  " released"),
                "footerHintText": ("Try saying, 'Alexa, tell me about new"
                                   " movies'")
            }
        }
        return apl_data

    # ------------------------------------------------------------------
    def get_apl_movies_list(self):
        """ return input data for the APL_DOC['movie_list'] APL document """
        # https://developer.amazon.com/en-US/docs/alexa/alexa-presentation-language/apl-alexa-text-list-layout.html
        apl_data = {
            "textListData": {
                "type": "object",
                "objectId": "textListMovies",
                "title": "New Movies",
                "listItems": []
            }
        }
        for m in self.movies.values():
            li = {}
            li['primaryText'] = m.title
            li['imageThumbnailSource'] = m.thumbnail
            apl_data['textListData']['listItems'].append(li)
            logger.info(li)

        return apl_data

    # ------------------------------------------------------------------
    def get_apl_movies_detail(self):
        """ return input data for the APL_DOC['movie_detail'] APL document """
        # https: // developer.amazon.com/en-US/docs/alexa/alexa-presentation-language/apl-alexa-image-list-item-layout.html
        apl_data = {
            "imageListData": {
                "type": "object",
                "objectId": "imageListMovies",
                "listItems": []
            }
        }
        for m in self.movies.values():
            li = {}
            li['primaryText'] = m.title
            li['imageSource'] = m.image
            apl_data['imageListData']['listItems'].append(li)
            logger.info(li)

        return apl_data

    # ------------------------------------------------------------------
    def process_response(self, response):
        """ process query results from TMDB by creating new Movie objects """
        self.movies.clear()
        if (response['total_results'] > 0):
            for m in response['results']:
                title = m['title'] if 'title' in m else '[blank]'
                overview = m['overview'] if 'overview' in m else '[blank]'
                release_date = (m['release_date'] if 'release_date' in m
                                else None)
                poster_path = m['poster_path'] if 'poster_path' in m else None
                movie = Movie(title, overview, release_date, poster_path)
                self.movies[title] = movie

    # ------------------------------------------------------------------
    def movie_info(self, movie_name):
        """ query TMDB for info relating to movies calls movie_name """
        encode_movie_name = urllib.parse.quote(movie_name)
        year = datetime.now().year
        url = (f'{self.BASE_URL_SEARCH}?api_key={self.API_KEY}'
               + f'&query={encode_movie_name}'
               + f'&primary_release_year={year}')
        logger.info(f'MovieSearch:movie_info: {url}')
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = 'utf-8'
        except requests.HTTPError as http_err:
            logger.error(
                f'MovieSearch:movie_info: HTTP error occurred: {http_err}')
            success = False
        else:
            self.process_response(response.json())
            success = True

        return success

    # ------------------------------------------------------------------
    def num_movies(self):
        """ return the number of movies for which info is currently held """
        return len(self.movies.keys())

    # ------------------------------------------------------------------
    def released_in_week(self, week):
        """ query TMDB to get all movies released in the requested week """
        self.week = week
        today = date.today()
        date_start = today - timedelta(days=today.weekday())
        date_stop = date_start + timedelta(days=6)
        offset = timedelta(days=7)
        if (week == Week.last):
            date_start -= offset
            date_stop -= offset
        elif (week == Week.next):
            date_start += offset
            date_stop += offset
        elif (week == Week.this):
            pass
        else:
            logger.error('MovieSearch:get_movies_in_week: invalid argument:'
                         f' week={week}')
            raise ValueError('Invalid argument')

        str_start = self.format_date(date_start)
        str_stop = self.format_date(date_stop)

        return self.released_between_dates(str_start, str_stop)

    # ------------------------------------------------------------------
    def released_between_dates(self, start, stop):
        """ query TMDB to get all movies released between two dates """
        url = (f'{self.BASE_URL_DISCOVER}?api_key={self.API_KEY}'
               + f'&primary_release_date.gte={start}'
               + f'&primary_release_date.lte={stop}'
               + f'&region={self.region}'
               + f'&with_release_type={self.release_type}')
        logger.info(f'MovieSearch:get_movies_between_dates: {url}')
        try:
            response = requests.get(url)
            response.raise_for_status()
            response.encoding = 'utf-8'
        except requests.HTTPError as http_err:
            logger.error('MovieSearch:released_between_dates: HTTP error'
                         f' ocurred: {http_err}')
            success = False
        else:
            self.process_response(response.json())
            success = True

        return success
