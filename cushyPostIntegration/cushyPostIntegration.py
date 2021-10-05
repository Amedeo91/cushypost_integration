import requests
import json
import datetime
import uuid
from cushyPostIntegration.logger_decorator import logger
import logging


class CushyPostIntegration:
    @logger
    def __init__(self, environment, app, token=None, refresh_token=None):
        """
        Class initialization
        :param environment: TEST or PRD
        :param app: app name for CushyPost
        :param token: (optional) in case you already have a valid token
        :param refresh_token: (optional) in case you already have a valid refresh token
        """
        self.environment = environment
        self.token = token
        self.refresh_token = refresh_token
        self.app = app
        if self.environment == "TEST":
            self.domain = "https://test.api.cushypost.com"
        elif self.environment == "PRD":
            self.domain = "https://api.cushypost.com"
        else:
            raise Exception("ENVIRONMENT NOT VALID")
        self.from_location = None
        self.to_location = None
        self.services = None
        self.shipping = None
        self.geo_db_data = {}

    @logger
    def login(self, username, password):
        """
        This method get the token and refresh_token starting a session with CushyPost
        :param username:
        :param password:
        :return:
        """
        request_body = {
            "app": self.app,
            "username": username,
            "password": password
        }
        response = requests.request("POST",
                                    "{}/security/v1/login".format(self.domain),
                                    headers={'Content-Type': 'application/json'},
                                    data=json.dumps(request_body))
        if response.status_code != 200:
            raise Exception("LOGIN FAILED")
        self.token = response.raw.headers.get('X-Cushypost-JWT')
        self.refresh_token = response.raw.headers.get('X-Cushypost-Refresh-JWT')

    @logger
    def refresh_tokens(self):
        """
        This method is refreshing the token using the refresh_token
        :return:
        """
        if not self.refresh_token:
            raise Exception("MISSING TOKENS")
        response = requests.request("POST",
                                    "{}/security/refresh_token".format(self.domain),
                                    headers={'Content-Type': 'application/json',
                                             'Authorization': 'Bearer {}'.format(self.refresh_token)},
                                    data=json.dumps({"app": "InOne"}))
        if response.status_code != 200:
            raise Exception("REFRESH FAILED")
        self.token = response.raw.headers.get('X-Cushypost-JWT')
        self.refresh_token = response.raw.headers.get('X-Cushypost-Refresh-JWT')

    @logger
    def __call_endpoint_with_refresh(self, http_method, path, data=None, retry=True):
        """
        Method that integrate CushyPost with the refreshToken call in case of 401
        :param http_method: GET/POST/PATCH/DELETE
        :param path: path on CushyPost
        :param data: body of the message as string
        :param retry: (Optional) Flag to trigger retry. Do not populate
        :return:
        """
        response = requests.request(http_method,
                                    "{}/{}".format(self.domain, path),
                                    headers={'Content-Type': 'application/json',
                                             'Authorization': 'Bearer {}'.format(self.token)},
                                    data=data)
        if response.status_code == 401 and retry:
            self.refresh_tokens()
            return self.__call_endpoint_with_refresh(http_method, path, data=data, retry=False)
        return response

    @logger
    def __geo_db_place_autocomplete(self, country_code, cap, multi_results=False):
        """
        Integration of autocomplete
        :param country_code:
        :param cap:
        :param multi_results: In case you are actually searching the DB
        :return:
        """
        if not self.token:
            raise Exception("MISSING TOKENS")
        request_body = {
            "app": self.app,
            "country_code": country_code,
            "sequence": cap,
            "limit": 10
        }
        response = self.__call_endpoint_with_refresh("POST",
                                                     "geodb/place_autocomplete",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            raise Exception("GEODB AUTOCOMPLETE FAILED")
        # I am expecting only one result
        locations = response.json()["response"]["data"]
        if multi_results:
            for location in locations:
                self.geo_db_data["{}_{}".format(country_code, location["postcode"])] = location
            return locations
        if len(locations) != 1:
            raise Exception("GEODB AUTOCOMPLETE FAILED")
        return locations[0]

    @logger
    def search_geo_db(self, country_code, cap):
        """
        This method is searching the DB, returning all the location that maches
        :param country_code:
        :param cap:
        :return:
        """
        return self.__geo_db_place_autocomplete(country_code, cap, multi_results=True)

    @logger
    def set_from(self, country_code, cap):
        self.__set_elem(country_code, cap, "from_location", "from")

    @logger
    def set_to(self, country_code, cap):
        self.__set_elem(country_code, cap, "to_location", "to")

    @logger
    def __set_elem(self, country_code, cap, elem, elem_name):
        """
        Here we are expecting a real zipcode.
        :param country_code:
        :param cap:
        :param elem:
        :param elem_name:
        :return:
        """
        geo_db_data_key = "{}_{}".format(country_code, cap)
        location = self.geo_db_data[geo_db_data_key] \
            if self.geo_db_data.get("{}_{}".format(country_code, cap)) \
            else self.__geo_db_place_autocomplete(country_code, cap)
        setattr(self, elem, {
            "name": elem_name,
            "country": country_code,
            "postalcode": cap,
            "city": location["city"],
            "province": location["province"],
            "phone": "",
            "email": "",
            "contact": "",
            "locality": location["city"],
            "administrative_area_level_1": location["region"],
            "administrative_area_level_2": location["province"],
            "location": {
                "lat": location["location"]["coordinates"][1],
                "lng": location["location"]["coordinates"][0],
                "location_type": "APPROXIMATE"
            },
            "validity": {
                "valid": True,
                "component": "postalcode"
            },
            "type": "geodb",
            "hash": location["id"]
        })

    @logger
    def set_services(self, year):
        """
        Generation of the services node
        :param year:
        :return:
        """
        if not self.from_location:
            raise Exception("MISSING FROM")
        if not self.token:
            raise Exception("MISSING TOKENS")
        request_body = {
            "app": self.app,
            "country": self.from_location["country"],
            "year": year
        }
        collection_date = datetime.datetime.utcnow().replace(microsecond=0)
        # We take the first day out of the weekend
        collection_date = collection_date + datetime.timedelta(days=7-collection_date.weekday()
                                                                    if collection_date.weekday() > 3 else 1)

        response = self.__call_endpoint_with_refresh("POST",
                                                     "calendar/holidays",
                                                     data=json.dumps(request_body))
        if response.status_code == 200:
            date_yyyy_mm_dd_format = collection_date.strftime('%Y-%m-%d')
            for holiday in response.json()["response"]["data"]:
                if date_yyyy_mm_dd_format == holiday["date"]:
                    collection_date = collection_date + datetime.timedelta(days=1)
                    date_yyyy_mm_dd_format = collection_date.strftime('%Y-%m-%d')
                    # If the next day is during the week end, we move after
                    if collection_date.weekday() > 4:
                        collection_date = collection_date + datetime.timedelta(days=1 if collection_date.weekday() == 6
                                                                                    else 2)
        # We keep cash_on_delivery and insurance hardcoded to 0
        self.services = {
            "collection": {
                "date": "{}Z".format(collection_date.isoformat()),
                "hours": [10, 14]
            },
            "insurance": {
                "value": 0,
                "currency": "EUR",
                "algorithm": "none"
            },
            "cash_on_delivery": {
                "value": 0,
                "currency": "EUR"
            }
        }

    @logger
    def set_shipping(self, packages):
        """
        Generation of shipping node
        :param packages:
        :return:
        """
        # goods_desc, product, special_instructions --> eventually, those should be specified by the user
        if not packages:
            raise Exception("MISSING DATA")
        self.shipping = {
            "total_weight": sum([int(package["weight"]) for package in packages]),
            "goods_desc": "content",
            "product": "All",
            "special_instructions": "Questo è solo un test. Si prega di cancellare!"
                if self.environment == "TEST" else "Nessuna",
            "packages": [{
                "type": package.get("type", "Parcel"),
                "height": package["height"],
                "width": package["width"],
                "length": package["length"],
                "weight": package["weight"],
                "content": "content",
                "hash": uuid.uuid4().hex
            } for package in packages]
        }

    @logger
    def get_rates(self):
        """
        Call to get rates
        :return:
        """
        if not self.token:
            raise Exception("MISSING TOKENS")
        if not self.from_location or not self.to_location or not self.shipping or not self.services:
            raise Exception("MISSING DATA")
        request_body = {
            "app": self.app,
            "from": self.from_location,
            "to": self.to_location,
            "shipping": self.shipping,
            "services": self.services
        }
        response = self.__call_endpoint_with_refresh("POST",
                                                     "shipment/rate",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            raise Exception("SHIPPING RATE FAILED")
        return response.json()["response"]["data"]

    def __get_dict(self):
        return {
            "classConfig": {
                "environment": self.environment,
                "app": self.app,
                "domain": self.domain,
                "token": self.token,
                "refresh_token": self.refresh_token
            },
            "from_location": self.from_location,
            "to_location": self.to_location,
            "services": self.services,
            "shipping": self.shipping,
            "geo_db_data": self.geo_db_data
        }

    def __get_string(self):
        return json.dumps(self.__get_dict())

    def __repr__(self):
        return self.__get_string()

    def __str__(self):
        return self.__get_string()
