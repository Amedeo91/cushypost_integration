import requests
import json
import datetime
import uuid
from cushyPostIntegration.logger_decorator import logger, logging
from cushyPostIntegration.exceptions import LoginFailed, RefreshFailed, MissingToken, ShippingRateFailed, \
    GeoDbAutoComplete, MissingFrom, MissingData, ApproveRateFailed, SearchPaidShipmentsFailed, SearchQuotationFailed, \
    NoQuotationFoundFailed, AddToCartFailed, RemoveFromCartFailed, BuyCartFailed, ConfirmCartFailed, \
    ConfirmCartMissingParameters, InvalidEnvironment


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
        self.domain = self.__get_domain()
        self.from_location = None
        self.to_location = None
        self.services = None
        self.shipping = None
        self.checkout_session_id = None
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
            logging.error(response.json())
            raise LoginFailed()
        self.token = response.raw.headers.get('X-Cushypost-JWT')
        self.refresh_token = response.raw.headers.get('X-Cushypost-Refresh-JWT')

    @logger
    def refresh_tokens(self):
        """
        This method is refreshing the token using the refresh_token
        :return:
        """
        if not self.refresh_token:
            raise MissingToken()
        response = requests.request("POST",
                                    "{}/security/refresh_token".format(self.domain),
                                    headers={'Content-Type': 'application/json',
                                             'Authorization': 'Bearer {}'.format(self.refresh_token)},
                                    data=json.dumps({"app": self.app}))
        if response.status_code != 200:
            logging.error(response.json())
            raise RefreshFailed()
        self.token = response.raw.headers.get('X-Cushypost-JWT')
        self.refresh_token = response.raw.headers.get('X-Cushypost-Refresh-JWT')

    @logger
    def __call_endpoint_with_refresh(self, http_method, path, params=None, data=None, retry=True):
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
                                    data=data,
                                    params=params)
        if response.status_code == 401 and retry:
            self.refresh_tokens()
            return self.__call_endpoint_with_refresh(http_method, path, params=params, data=data, retry=False)
        return response

    @logger
    def __geo_db_place_autocomplete(self, country_code, cap, city=None, multi_results=False):
        """
        Integration of autocomplete
        :param country_code:
        :param cap:
        :param multi_results: In case you are actually searching the DB
        :return:
        """
        if not self.token:
            raise MissingToken()
        request_body = {
            "app": self.app,
            "country_code": country_code,
            "sequence": "{} {}".format(cap, city) if city else cap,
            "limit": 10
        }
        response = self.__call_endpoint_with_refresh("POST",
                                                     "geodb/place_autocomplete",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            logging.error(response.json())
            raise GeoDbAutoComplete()
        # I am expecting only one result
        locations = response.json()["response"]["data"]
        if multi_results:
            for location in locations:
                self.geo_db_data["{}_{}_{}".format(country_code, location["postcode"], location["city"])] = location
            return locations
        if len(locations) == 0:
            # This part is useful for the quotation part! As the CAP define the price.
            locations = self.__geo_db_place_autocomplete(country_code, cap, multi_results=True)
            if len(locations) == 0:
                raise GeoDbAutoComplete()
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
    def set_from(self, country_code, cap, city):
        self.__set_elem(country_code, cap, city, "from_location", "from")

    @logger
    def set_to(self, country_code, cap, city):
        self.__set_elem(country_code, cap, city, "to_location", "to")

    @logger
    def __set_elem(self, country_code, cap, city, elem, elem_name):
        """
        Here we are expecting a real zipcode.
        :param country_code:
        :param cap:
        :param elem:
        :param elem_name:
        :return:
        """
        geo_db_data_key = "{}_{}_{}".format(country_code, cap, city)
        location = self.geo_db_data[geo_db_data_key] \
            if self.geo_db_data.get(geo_db_data_key) \
            else self.__geo_db_place_autocomplete(country_code, cap, city)
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
    def set_services(self, year, month=None, day=None, insurance_value=None, cash_on_delivery=None):
        """
        Generation of the services node
        :param year:
        :param month (optional)
        :param day (optional)
        :param insurance_value (optional)
        :param cash_on_delivery (optional)
        :return:
        """
        if not self.from_location:
            raise MissingFrom()
        if not self.token:
            raise MissingToken()
        request_body = {
            "app": self.app,
            "country": self.from_location["country"],
            "year": year
        }
        collection_date = datetime.datetime.utcnow().replace(microsecond=0)
        collection_date = collection_date.replace(year=int(year))
        if month:
            collection_date = collection_date.replace(month=int(month))
        if day:
            collection_date = collection_date.replace(day=int(day))
        if day or month:
            if collection_date.weekday() > 4:
                collection_date = collection_date + datetime.timedelta(days=1 if collection_date.weekday() == 6 else 2)
        else:
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
                "value": float(insurance_value) if insurance_value else 0,
                "currency": "EUR",
                "algorithm": "any" if insurance_value else "none"
            },
            "cash_on_delivery": {
                "value": float(cash_on_delivery) if cash_on_delivery else 0,
                "currency": "EUR"
            }
        }

    @logger
    def set_shipping(self, packages, goods_desc=None, special_instructions=None):
        """
        Generation of shipping node
        :param packages:
        :param goods_desc: (optional)
        :param special_instructions: (optional)
        :return:
        """
        if not packages:
            raise MissingData()
        self.shipping = {
            "total_weight": sum([int(package["weight"]) for package in packages]),
            "goods_desc": goods_desc if goods_desc else "content",
            "product": "All",
            "special_instructions": "Questo è solo un test. Si prega di cancellare!"
                                    if self.environment == "TEST" else (special_instructions
                                                                        if special_instructions else "Nessuna"),
            "packages": [{
                "type": package.get("type", "Parcel"),
                "height": package["height"],
                "width": package["width"],
                "length": package["length"],
                "weight": package["weight"],
                "content": package["contentDesc"] if package.get("contentDesc") else "content",
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
            raise MissingToken()
        if not self.from_location or not self.to_location or not self.shipping or not self.services:
            raise MissingData()
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
            logging.error(response.json())
            raise ShippingRateFailed()
        return response.json()["response"]["data"]

    @logger
    def approve_quotation(self, quotation_id, from_extra_data, to_extra_data, shipping_extra_data=None):
        """
        Call to get rates
        :param quotation_id: id of the rate to approve
        :param from_extra_data: data with all the info for from address
        :param to_extra_data: data with all the info for to address
        :param shipping_extra_data: (optional) data with description and special instructions.
                                    It needs to contains the has of the packages for which
                                    we want to modify the description
        :return:
        """
        if not self.token:
            raise MissingToken()
        if not self.from_location or not self.to_location or not self.shipping or not self.services:
            raise MissingData()
        # PUT FINAL INFORMATION FOR ADDRESSES AND DESCRIPTIONS
        self.from_location["name"] = from_extra_data["name"]
        self.from_location["phone"] = from_extra_data["phone"]
        self.from_location["email"] = from_extra_data["email"]
        self.from_location["address"] = from_extra_data["address"]
        self.from_location["city"] = from_extra_data.get("city", self.from_location["city"])
        self.from_location["administrative_area_level_3"] = self.from_location["city"]
        self.to_location["name"] = to_extra_data["name"]
        self.to_location["phone"] = to_extra_data.get("phone", self.from_location["phone"])
        self.to_location["email"] = to_extra_data.get("email", self.from_location["email"])
        self.to_location["address"] = to_extra_data["address"]
        self.from_location["city"] = from_extra_data.get("city", self.from_location["city"])
        self.to_location["administrative_area_level_3"] = self.to_location["city"]
        if shipping_extra_data:
            if shipping_extra_data.get("packages") and isinstance(shipping_extra_data["packages"], dict):
                for package in self.shipping["packages"]:
                    extra_details = shipping_extra_data["packages"].get(package["hash"], {})
                    package["content"] = extra_details.get("contentDesc", package["content"])
                    package["contentDesc"] = package["content"]
            self.set_shipping(self.shipping["packages"],
                              goods_desc=shipping_extra_data.get("goodsDesc"),
                              special_instructions=shipping_extra_data.get("specialInstructions"))
        request_body = {
            "app": self.app,
            "as": "WaitingForPayment",
            "quotation_id": quotation_id,
            "order": {
                "quotation": quotation_id,
                "from": self.from_location,
                "to": self.to_location,
                "shipping": self.shipping,
                "services": self.services
            }
        }
        response = self.__call_endpoint_with_refresh("POST",
                                                     "quotation/approve",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            logging.error(response.json())
            raise ApproveRateFailed()
        return response.json()["response"]["data"]

    @logger
    def search_paid_shipping(self, page=None):
        """

        :param page: (optional) the endpoint has pagination
        :return:
        """
        if page is None:
            page = 0
        request_body = {
            "app": self.app,
            "limit": 10,
            "skip": page*10,
            "sort": {
                "services.collection.date": -1
            },
            "filter": {
                "status.current.value": {
                    "$nin": ["WaitingForPayment", "PaymentInitiated", "Draft", "Archived"]
                }
            },
            "match": {
                "status.current.value": {
                    "$nin": ["WaitingForPayment", "PaymentInitiated", "Draft", "Archived"]
                }
            },
            "inspect": False
        }

        response = self.__call_endpoint_with_refresh("POST",
                                                     "shipment/search",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            logging.error(response.json())
            raise SearchPaidShipmentsFailed()
        return response.json()["response"]["data"]

    @logger
    def search_quotation_to_pay(self, page=None):
        """

        :param page: (optional) the endpoint has pagination
        :return:
        """
        if page is None:
            page = 0
        request_body = {
            "app": self.app,
            "limit": 10,
            "skip": page*10,
            "sort": {
                "services.collection.date": -1
            },
            "filter": {
                "status.current.value": {
                    "$in": ["WaitingForPayment", "PaymentInitiated"]
                }
            }
        }

        response = self.__call_endpoint_with_refresh("POST",
                                                     "shipment/search",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            logging.error(response.json())
            raise SearchQuotationFailed()
        return response.json()["response"]["data"]

    @logger
    def search_by_quotation_id(self, quotation_ids, page=None, shipments=None):
        """

        :param quotation_ids: quotation to get
        :param page: (optional) page to start to search
        :param shipments: (optional) list to start to build
        :return:
        """
        page = 0 if page is None else page
        response_data = self.search_quotation_to_pay(page)
        if len(response_data.get("items", [])) == 0:
            raise NoQuotationFoundFailed()
        shipments = [] if shipments is None else shipments
        shipments.extend([item["_id"]["$oid"]
                          for item in response_data["items"] if item["quotation"]["id"] in quotation_ids])
        if len(quotation_ids) == len(shipments):
            return shipments
        else:
            return self.search_by_quotation_id(quotation_ids, page=page+1, shipments=shipments)

    @logger
    def add_shipping_ids_to_cart(self, shipping_ids):
        """

        :param shipping_ids: Shipping ids to add
        :return:
        """
        response = None
        for shipping_id in shipping_ids:
            request_body = {
                "app": self.app,
                "type": "shipment",
                "id": shipping_id
            }
            response = self.__call_endpoint_with_refresh("POST",
                                                         "cart/item",
                                                         data=json.dumps(request_body))
            if response.status_code != 200:
                logging.error(response.json())
                self.remove_shipping_ids_to_cart(shipping_ids, raise_error=False)
                raise AddToCartFailed()
            response = response.json().get("response", {}).get("data")
        return response

    @logger
    def remove_shipping_ids_to_cart(self, shipping_ids, raise_error=True):
        """

        :param shipping_ids: Shipping ids to remove
        :param raise_error: (optional) continue removing without raising error
        :return:
        """
        response = None
        for shipping_id in shipping_ids:
            request_body = {
                "app": self.app,
                "id": shipping_id
            }
            response = self.__call_endpoint_with_refresh("DELETE",
                                                         "cart/item",
                                                         params=request_body)
            if response.status_code != 200 and raise_error:
                logging.error(response.json())
                raise RemoveFromCartFailed()
            else:
                response = response.json().get("response", {}).get("data")
        return response

    @logger
    def buy_cart(self, success_url, cancel_url, description):
        """

        :param success_url: Page to come back after payment
        :param cancel_url: Page to come back if payment is cancelled
        :param description: Description on the payment page
        :return:
        """
        request_body = {
            "app": self.app,
            "success_url": success_url,
            "cancel_url": cancel_url,
            "description": description
        }
        response = self.__call_endpoint_with_refresh("POST",
                                                     "cart/buy",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            logging.error(response.json())
            raise BuyCartFailed()
        self.checkout_session_id = response.json()["response"]["data"]["id"]
        return response.json()["response"]["data"]["url"]

    @logger
    def confirm_cart(self):
        """

        :return:
        """
        if not self.checkout_session_id:
            raise ConfirmCartMissingParameters()
        request_body = {
            "app": self.app,
            "session_id": self.checkout_session_id
        }
        response = self.__call_endpoint_with_refresh("POST",
                                                     "cart/confirm",
                                                     data=json.dumps(request_body))
        if response.status_code != 200:
            logging.error(response.json())
            raise ConfirmCartFailed()
        return response.json()["response"]["data"]

    @logger
    def get_shipment_label(self, shipping_ids):
        """

        :param shipping_ids: Label to download
        :return:
        """
        shipment_labels = []
        for shipping_id in shipping_ids:
            request_body = {
                "app": self.app,
                "shipment_id": shipping_id
            }
            response = self.__call_endpoint_with_refresh("GET",
                                                         "shipment/label",
                                                         params=request_body)
            if response.status_code == 200 and response.json().get("response", {}).get("data"):
                shipment_labels.append(response.json()["response"]["data"])
        return shipment_labels

    def __get_domain(self):
        """

        :return:
        """
        if self.environment == "TEST":
            return "https://test.api.cushypost.com"
        elif self.environment == "PRD":
            return "https://api.cushypost.com"
        else:
            raise InvalidEnvironment()

    def parse_from_str(self, class_json_image):
        """

        :param class_json_image:
        :return:
        """
        self.parse_from_dict(json.loads(class_json_image))

    def parse_from_dict(self, class_dict_image):
        """

        :param class_dict_image:
        :return:
        """
        self.environment = class_dict_image.get("classConfig", {})["environment"]
        self.app = class_dict_image.get("classConfig", {})["app"]
        self.domain = self.__get_domain()
        self.token = class_dict_image.get("classConfig", {}).get("token")
        self.refresh_token = class_dict_image.get("classConfig", {}).get("refresh_token")
        self.from_location = class_dict_image.get("from_location")
        self.to_location = class_dict_image.get("to_location")
        self.services = class_dict_image.get("services")
        self.shipping = class_dict_image.get("shipping")
        self.checkout_session_id = class_dict_image.get("checkout_session_id")
        self.geo_db_data = class_dict_image.get("geo_db_data", {})

    def get_dict(self):
        """

        :return:
        """
        class_dictionary = {
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
        if self.checkout_session_id:
            class_dictionary["checkout_session_id"] = self.checkout_session_id
        return class_dictionary

    def __get_string(self):
        """

        :return:
        """
        return json.dumps(self.get_dict())

    def __repr__(self):
        """

        :return:
        """
        return self.__get_string()

    def __str__(self):
        """

        :return:
        """
        return self.__get_string()

    def __eq__(self, other):
        """

        :param other:
        :return:
        """
        if isinstance(other, CushyPostIntegration):
            return self.get_dict() == other.get_dict()
        return False
