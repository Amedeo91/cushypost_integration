import unittest
from cushyPostIntegration import CushyPostIntegration
import json
import responses
import logging


logging.basicConfig(level=logging.DEBUG)


class TestCushyPostIntegration(unittest.TestCase):
    def test_create_class(self):
        class_initializer = CushyPostIntegration("TEST", "NEW_APP", token="token", refresh_token="refresh_token")
        self.assertEqual(class_initializer.environment, "TEST")
        self.assertEqual(class_initializer.domain, "https://test.api.cushypost.com")
        self.assertEqual(class_initializer.app, "NEW_APP")
        self.assertEqual(class_initializer.token, "token")
        self.assertEqual(class_initializer.refresh_token, "refresh_token")
        class_initializer = CushyPostIntegration("PRD", "NEW_APP", token="token", refresh_token="refresh_token")
        self.assertEqual(class_initializer.environment, "PRD")
        self.assertEqual(class_initializer.domain, "https://api.cushypost.com")
        self.assertEqual(class_initializer.app, "NEW_APP")
        self.assertEqual(class_initializer.token, "token")
        self.assertEqual(class_initializer.refresh_token, "refresh_token")
        try:
            CushyPostIntegration("NOT_VALID", "NEW_APP", token="token", refresh_token="refresh_token")
            raise Exception("ENVIRONMENT NOT VALID - TEST FAILED")
        except Exception as error:
            self.assertEqual(str(error), "ENVIRONMENT NOT VALID")

    @responses.activate
    def test_login_error(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        responses.add(responses.POST, "{}/security/v1/login".format(cushy_post_integration.domain),
                      json={"response": {"succeed": False, "errcode": 401,
                                         "errmsg": "Invalid credentials",
                                         "error": None, "data": None}}, status=401)
        try:
            cushy_post_integration.login("username", "password")
            raise Exception("LOGIN FAILED - TEST FAILED")
        except Exception as error:
            self.assertEqual(str(error), "LOGIN FAILED")
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_login_success(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        responses.add(responses.POST, "{}/security/v1/login".format(cushy_post_integration.domain),
                      json={"response": {"succeed": True, "errcode": 200, "errmsg": None, "error": None,
                                         "data": {"_id": {"$oid": "61532abf6c37d841dd3fed81"},
                                                  "name": "New Corps srl",
                                                  "region": {"country": "IT",
                                                             "postalcode": ".", "city": ".",
                                                             "province": ".", "address": "."},
                                                  "type": "company",
                                                  "created": {"$date": {"$numberLong": "1632840383431"}},
                                                  "updated": {"$date": {"$numberLong": "1632840383431"}},
                                                  "perms": {"owners": [{"$oid": "61532abf6c37d841dd3fed81"}]},
                                                  "contacts": {"administrative": {"email": "cagefa5348@bio123.net"},
                                                               "legal": {"pec": "cagefa5348@bio123.net"}},
                                                  "status": {"current":
                                                                 {"at": {"$date": {"$numberLong": "1632840383431"}},
                                                                  "value": "Prospect"},
                                                             "history": [
                                                                 {"at": {"$date": {"$numberLong": "1632840383431"}},
                                                                  "value": "Prospect"}]}}}},
                      status=200,
                      headers={
                          "X-Cushypost-JWT": "X-Cushypost-JWT_LOGIN",
                          "X-Cushypost-Refresh-JWT": "X-Cushypost-Refresh-JWT_REFRESH"
                      })
        cushy_post_integration.login("username", "password")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(json.loads(responses.calls[0].request.body),
                         {"app": cushy_post_integration.app, "username": "username", "password": "password"})
        self.assertEqual(cushy_post_integration.token, "X-Cushypost-JWT_LOGIN")
        self.assertEqual(cushy_post_integration.refresh_token, "X-Cushypost-Refresh-JWT_REFRESH")

    def test_refresh_token_missing_token(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        try:
            cushy_post_integration.refresh_tokens()
            raise Exception("MISSING TOKENS - TEST FAILED")
        except Exception as error:
            self.assertEqual(str(error), "MISSING TOKENS")
        self.assertEqual(len(responses.calls), 0)

    @responses.activate
    def test_refresh_token_failure(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        cushy_post_integration.token = "X-Cushypost-JWT_LOGIN"
        cushy_post_integration.refresh_token = "X-Cushypost-Refresh-JWT_REFRESH"
        responses.add(responses.POST, "{}/security/refresh_token".format(cushy_post_integration.domain),
                      json={"response": {"succeed": False, "errcode": 401,
                                         "errmsg": "Cannot handle token prior to 2021-10-05T11:32:14+0000",
                                         "error": None, "data": None}}, status=401)
        try:
            cushy_post_integration.refresh_tokens()
            raise Exception("REFRESH FAILED - TEST FAILED")
        except Exception as error:
            self.assertEqual(str(error), "REFRESH FAILED")
        self.assertEqual(len(responses.calls),  1)
        self.assertEqual(responses.calls[0].request.headers["Authorization"], "Bearer X-Cushypost-Refresh-JWT_REFRESH")

    @responses.activate
    def test_refresh_token_success(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        cushy_post_integration.token = "X-Cushypost-JWT_LOGIN"
        cushy_post_integration.refresh_token = "X-Cushypost-Refresh-JWT_REFRESH"
        responses.add(responses.POST, "{}/security/refresh_token".format(cushy_post_integration.domain),
                      json={"response": {"succeed": True, "errcode": 200, "errmsg": None, "error": None,
                                         "data": {"_id": {"$oid": "61532abf6c37d841dd3fed81"},
                                                  "name": "New Corps srl",
                                                  "region": {"country": "IT", "postalcode": ".",
                                                             "city": ".", "province": ".", "address": "."},
                                                  "type": "company",
                                                  "created": {"$date": {"$numberLong": "1632840383431"}},
                                                  "updated": {"$date": {"$numberLong": "1632840383431"}},
                                                  "perms": {"owners": [{"$oid": "61532abf6c37d841dd3fed81"}]},
                                                  "contacts": {"administrative": {"email": "cagefa5348@bio123.net"},
                                                               "legal": {"pec": "cagefa5348@bio123.net"}},
                                                  "status": {"current":
                                                                 {"at": {"$date": {"$numberLong": "1632840383431"}},
                                                                  "value": "Prospect"},
                                                             "history": [
                                                                 {"at": {"$date": {"$numberLong": "1632840383431"}},
                                                                  "value": "Prospect"}]}}}},
                      status=200,
                      headers={
                          "X-Cushypost-JWT": "X-Cushypost-JWT_LOGIN_new",
                          "X-Cushypost-Refresh-JWT": "X-Cushypost-Refresh-JWT_REFRESH_new"
                      })
        cushy_post_integration.refresh_tokens()
        self.assertEqual(len(responses.calls),  1)
        self.assertEqual(responses.calls[0].request.headers["Authorization"], "Bearer X-Cushypost-Refresh-JWT_REFRESH")
        self.assertEqual(cushy_post_integration.token, "X-Cushypost-JWT_LOGIN_new")
        self.assertEqual(cushy_post_integration.refresh_token, "X-Cushypost-Refresh-JWT_REFRESH_new")

    @responses.activate
    def test_search_geo_db_success_set_from_no_search(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        cushy_post_integration.token = "X-Cushypost-JWT_LOGIN"
        cushy_post_integration.refresh_token = "X-Cushypost-Refresh-JWT_REFRESH"
        responses.add(responses.POST, "{}/geodb/place_autocomplete".format(cushy_post_integration.domain),
                      match=[
                          responses.json_params_matcher({
                              "app": cushy_post_integration.app,
                              "country_code": "IT",
                              "sequence": "00020 Agosta",
                              "limit": 10
                          })
                      ],
                      json={
                          "response": {
                              "succeed": True,
                              "errcode": 200,
                              "errmsg": None,
                              "error": None,
                              "data": [
                                  {
                                      "updated": "2021-05-27T00:23:38.2459084Z",
                                      "id": "7e8ccb1698bb2a6f7a9dfcac0892c61f",
                                      "country": "IT",
                                      "province": "RM",
                                      "provinceDescription": "Roma",
                                      "region": "Lazio",
                                      "postcode": "00020",
                                      "city": "Agosta",
                                      "location": {
                                          "type": "Point",
                                          "coordinates": [
                                              "13.03128",
                                              "41.98044"
                                          ]
                                      },
                                      "description": "00020 Agosta"
                                  }
                              ]
                          }
                      },
                      status=200)
        cushy_post_integration.set_from("IT", "00020", "Agosta")
        self.assertEqual(cushy_post_integration.from_location, {
            "administrative_area_level_1": "Lazio", "administrative_area_level_2": "RM",
            "city": "Agosta", "contact": "", "country": "IT", "email": "", "hash": "7e8ccb1698bb2a6f7a9dfcac0892c61f",
            "locality": "Agosta", "location": {"lat": "41.98044", "lng": "13.03128", "location_type": "APPROXIMATE"},
            "name": "from",
            "phone": "",
            "postalcode": "00020",
            "province": "RM",
            "type": "geodb",
            "validity": {"component": "postalcode", "valid": True}})
        responses.add(responses.POST, "{}/geodb/place_autocomplete".format(cushy_post_integration.domain),
                      match=[
                          responses.json_params_matcher({
                              "app": cushy_post_integration.app,
                              "country_code": "IT",
                              "sequence": "00020 Agostaasdsd",
                              "limit": 10
                          })
                      ],
                      json={
                          "response": {
                              "succeed": True,
                              "errcode": 200,
                              "errmsg": None,
                              "error": None,
                              "data": []
                          }
                      },
                      status=200)
        responses.add(responses.POST, "{}/geodb/place_autocomplete".format(cushy_post_integration.domain),
                      match=[
                          responses.json_params_matcher({
                              "app": cushy_post_integration.app,
                              "country_code": "IT",
                              "sequence": "00020",
                              "limit": 10
                          })
                      ],
                      json={
                          "response": {
                              "succeed": True,
                              "errcode": 200,
                              "errmsg": None,
                              "error": None,
                              "data": [
                                  {
                                      "updated": "2021-05-27T00:23:38.2459084Z",
                                      "id": "7e8ccb1698bb2a6f7a9dfcac0892c61f",
                                      "country": "IT",
                                      "province": "RM",
                                      "provinceDescription": "Roma",
                                      "region": "Lazio",
                                      "postcode": "00020",
                                      "city": "Agosta",
                                      "location": {
                                          "type": "Point",
                                          "coordinates": [
                                              "13.03128",
                                              "41.98044"
                                          ]
                                      },
                                      "description": "00020 Agosta"
                                  }, {
                                      "updated": "2021-05-27T00:23:38.2459084Z",
                                      "id": "ba21e9f6013d6d97b4fa6f64939bef06",
                                      "country": "IT",
                                      "province": "RM",
                                      "provinceDescription": "Roma",
                                      "region": "Lazio",
                                      "postcode": "00020",
                                      "city": "Arcinazzo Romano",
                                      "location": {
                                          "type": "Point",
                                          "coordinates": [
                                              "13.11351",
                                              "41.88062"
                                          ]
                                      },
                                      "description": "00020 Arcinazzo Romano"
                                  }
                              ]
                          }
                      },
                      status=200)
        cushy_post_integration.set_from("IT", "00020", "Agostaasdsd")
        self.assertEqual(cushy_post_integration.from_location, {
            "administrative_area_level_1": "Lazio", "administrative_area_level_2": "RM",
            "city": "Agosta", "contact": "", "country": "IT", "email": "", "hash": "7e8ccb1698bb2a6f7a9dfcac0892c61f",
            "locality": "Agosta", "location": {"lat": "41.98044", "lng": "13.03128", "location_type": "APPROXIMATE"},
            "name": "from",
            "phone": "",
            "postalcode": "00020",
            "province": "RM",
            "type": "geodb",
            "validity": {"component": "postalcode", "valid": True}})

    @responses.activate
    def test_search_geo_db_success_with_refresh(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        cushy_post_integration.token = "X-Cushypost-JWT_LOGIN"
        cushy_post_integration.refresh_token = "X-Cushypost-Refresh-JWT_REFRESH"
        responses.add(responses.POST, "{}/security/refresh_token".format(cushy_post_integration.domain),
                      json={"response": {"succeed": True, "errcode": 200, "errmsg": None, "error": None,
                                         "data": {"_id": {"$oid": "61532abf6c37d841dd3fed81"},
                                                  "name": "New Corps srl",
                                                  "region": {"country": "IT", "postalcode": ".",
                                                             "city": ".", "province": ".", "address": "."},
                                                  "type": "company",
                                                  "created": {"$date": {"$numberLong": "1632840383431"}},
                                                  "updated": {"$date": {"$numberLong": "1632840383431"}},
                                                  "perms": {"owners": [{"$oid": "61532abf6c37d841dd3fed81"}]},
                                                  "contacts": {"administrative": {"email": "cagefa5348@bio123.net"},
                                                               "legal": {"pec": "cagefa5348@bio123.net"}},
                                                  "status": {"current":
                                                                 {"at": {"$date": {"$numberLong": "1632840383431"}},
                                                                  "value": "Prospect"},
                                                             "history": [
                                                                 {"at": {"$date": {"$numberLong": "1632840383431"}},
                                                                  "value": "Prospect"}]}}}},
                      status=200,
                      headers={
                          "X-Cushypost-JWT": "X-Cushypost-JWT_LOGIN_new",
                          "X-Cushypost-Refresh-JWT": "X-Cushypost-Refresh-JWT_REFRESH_new"
                      })
        geo_db_success_response = {
            "response": {
                "succeed": True,
                "errcode": 200,
                "errmsg": None,
                "error": None,
                "data": [
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "7e8ccb1698bb2a6f7a9dfcac0892c61f",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Agosta",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.03128",
                                "41.98044"
                            ]
                        },
                        "description": "00020 Agosta"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "ba21e9f6013d6d97b4fa6f64939bef06",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Arcinazzo Romano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.11351",
                                "41.88062"
                            ]
                        },
                        "description": "00020 Arcinazzo Romano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "54f9d1f2d34c1c20bcc9bcef22ef30fe",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Camerata Nuova",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.10799",
                                "42.0189"
                            ]
                        },
                        "description": "00020 Camerata Nuova"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "7fc951747d68f00eca61d87c45f6b01e",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Canterano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.03556",
                                "41.94264"
                            ]
                        },
                        "description": "00020 Canterano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "acb7f46dbbeb895881ac7f4024676e71",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Cerreto Laziale",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.98235",
                                "41.94176"
                            ]
                        },
                        "description": "00020 Cerreto Laziale"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "ba61abfbeeeb362a50eaf4e96b3a4c50",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Cervara di Roma",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.06809",
                                "41.98782"
                            ]
                        },
                        "description": "00020 Cervara di Roma"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "57a536516180422b041ed562fb67690a",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Ciciliano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.94025",
                                "41.95968"
                            ]
                        },
                        "description": "00020 Ciciliano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "b5e9b6bb4c6eae7303e18aabd2aadb3b",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Cineto Romano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.96173",
                                "42.04938"
                            ]
                        },
                        "description": "00020 Cineto Romano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "9a05c697ce5c7a5fcc516f5b46d9e941",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Jenne",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.17022",
                                "41.88807"
                            ]
                        },
                        "description": "00020 Jenne"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "70fcbc2e19b66e1b08133bb716c1d442",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Mandela",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.92258",
                                "42.02865"
                            ]
                        },
                        "description": "00020 Mandela"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "4f87468146d6245870dd46a168b6b84e",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Marano Equo",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.01495",
                                "41.99239"
                            ]
                        },
                        "description": "00020 Marano Equo"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "e4a15049b9a7fb915a2caa90c3f2b071",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Percile",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.90777",
                                "42.09578"
                            ]
                        },
                        "description": "00020 Percile"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "c3f1c23cb402ef04b8beea47c2c4c968",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Pisoniano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.96029",
                                "41.90715"
                            ]
                        },
                        "description": "00020 Pisoniano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "9c1f47f8d7158d09003bfe5f9b3ee942",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Riofreddo",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.99997",
                                "42.06159"
                            ]
                        },
                        "description": "00020 Riofreddo"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "6eec352b6dfe2cdd80fccd43fbf9a4b6",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Rocca Canterano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.02223",
                                "41.95566"
                            ]
                        },
                        "description": "00020 Rocca Canterano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "c4b4fea600cc34e094c7762e40deb8ea",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Roccagiovine",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.89943",
                                "42.05017"
                            ]
                        },
                        "description": "00020 Roccagiovine"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "59ed25456ff084c83ab1d9f53d4750f5",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Sambuci",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.93573",
                                "41.98435"
                            ]
                        },
                        "description": "00020 Sambuci"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "2121c861a3612cdfd50ba316d154bee6",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Saracinesco",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.95282",
                                "42.00316"
                            ]
                        },
                        "description": "00020 Saracinesco"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "fbf21528be30ee593ff3de0351a1ad4e",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Vallepietra",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.23058",
                                "41.92543"
                            ]
                        },
                        "description": "00020 Vallepietra"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "004839129ae3ee332d3fb5d61c640c31",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Vallinfreda",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.99502",
                                "42.08471"
                            ]
                        },
                        "description": "00020 Vallinfreda"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "b9b645b94641103026828a421dec14ce",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00020",
                        "city": "Vivaro Romano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.00659",
                                "42.09882"
                            ]
                        },
                        "description": "00020 Vivaro Romano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "372f708cbb6c26a7997b5087ba9d03f4",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00021",
                        "city": "Affile",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.10203",
                                "41.88488"
                            ]
                        },
                        "description": "00021 Affile"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "8d77a776ae1dd6c4fcc4983457afb87a",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00022",
                        "city": "Anticoli Corrado",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.98905",
                                "42.01061"
                            ]
                        },
                        "description": "00022 Anticoli Corrado"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "d731b84e9a52e8049b0d6182f4ef7468",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00023",
                        "city": "Arsoli",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.01609",
                                "42.04069"
                            ]
                        },
                        "description": "00023 Arsoli"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "8a287f982b3452a02af523c697826fe4",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00024",
                        "city": "Castel Madama",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.86566",
                                "41.9742"
                            ]
                        },
                        "description": "00024 Castel Madama"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "0a14f3b18799df30fd7a4fd3a8642ee7",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00025",
                        "city": "Gerano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.99504",
                                "41.93303"
                            ]
                        },
                        "description": "00025 Gerano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "3c8ff61bfe378981666a4fc7afe5eb5d",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00026",
                        "city": "Licenza",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.90044",
                                "42.07451"
                            ]
                        },
                        "description": "00026 Licenza"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "ddd79b8a71daeea7a863674556fdc07b",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00027",
                        "city": "Roviano",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.9944",
                                "42.02631"
                            ]
                        },
                        "description": "00027 Roviano"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "a006fcf1d1a756168439393a59002120",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00028",
                        "city": "Subiaco",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "13.09276",
                                "41.92532"
                            ]
                        },
                        "description": "00028 Subiaco"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "71682d7833761acd664cc46c463fae6f",
                        "country": "IT",
                        "province": "RM",
                        "provinceDescription": "Roma",
                        "region": "Lazio",
                        "postcode": "00029",
                        "city": "Vicovaro",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "12.89591",
                                "42.01614"
                            ]
                        },
                        "description": "00029 Vicovaro"
                    },
                    {
                        "updated": "2021-05-27T00:23:38.2459084Z",
                        "id": "ad013f64467d839447214b5a29b901a3",
                        "country": "IT",
                        "province": "MI",
                        "provinceDescription": "Milano",
                        "region": "Lombardia",
                        "postcode": "20002",
                        "city": "Ossona",
                        "location": {
                            "type": "Point",
                            "coordinates": [
                                "8.90145",
                                "45.50617"
                            ]
                        },
                        "description": "20002 Ossona"
                    }
                ]
            }
        }

        def request_callback(request):
            self.assertEqual({"app": "NEW_APP", "country_code": "IT", "sequence": "0002", "limit": 10},
                             json.loads(request.body))
            if request.headers["Authorization"] == "Bearer X-Cushypost-JWT_LOGIN":
                return (401,
                        {"Content-Type": "application/json; charset=UTF-8"},
                        json.dumps({"response": {"succeed": False, "errcode": 401,
                                                 "errmsg": "Not authorized",
                                                 "error": None, "data": None}}))
            elif request.headers["Authorization"] == "Bearer X-Cushypost-JWT_LOGIN_new":
                return (200,
                        {"Content-Type": "application/json; charset=UTF-8"},
                        json.dumps(geo_db_success_response))

        responses.add_callback(
            responses.POST, "{}/geodb/place_autocomplete".format(cushy_post_integration.domain),
            callback=request_callback,
            content_type='application/json',
        )
        self.assertEqual(cushy_post_integration.search_geo_db("IT", "0002"),
                         geo_db_success_response["response"]["data"])
        self.assertEqual(len(responses.calls), 3)
        self.assertEqual(json.loads(responses.calls[1].request.body), {"app": cushy_post_integration.app})
        self.assertEqual(responses.calls[1].request.headers["Authorization"], "Bearer X-Cushypost-Refresh-JWT_REFRESH")
        self.assertEqual(cushy_post_integration.token, "X-Cushypost-JWT_LOGIN_new")
        self.assertEqual(cushy_post_integration.refresh_token, "X-Cushypost-Refresh-JWT_REFRESH_new")
        cushy_post_integration.set_from("IT", "00020", "Vivaro Romano")
        self.assertEqual(cushy_post_integration.from_location,
                         {'administrative_area_level_1': 'Lazio', 'administrative_area_level_2': 'RM',
                          'city': 'Vivaro Romano', 'contact': '', 'country': 'IT', 'email': '',
                          'hash': 'b9b645b94641103026828a421dec14ce', 'locality': 'Vivaro Romano',
                          'location': {'lat': '42.09882', 'lng': '13.00659', 'location_type': 'APPROXIMATE'},
                          'name': 'from', 'phone': '', 'postalcode': '00020', 'province': 'RM', 'type': 'geodb',
                          'validity': {'component': 'postalcode', 'valid': True}})
        cushy_post_integration.set_to("IT", "00028", "Subiaco")
        self.assertEqual(cushy_post_integration.to_location,
                         {'administrative_area_level_1': 'Lazio', 'administrative_area_level_2': 'RM',
                          'city': 'Subiaco', 'contact': '', 'country': 'IT', 'email': '',
                          'hash': 'a006fcf1d1a756168439393a59002120', 'locality': 'Subiaco',
                          'location': {'lat': '41.92532', 'lng': '13.09276', 'location_type': 'APPROXIMATE'},
                          'name': 'to', 'phone': '', 'postalcode': '00028', 'province': 'RM', 'type': 'geodb',
                          'validity': {'component': 'postalcode', 'valid': True}})

    @responses.activate
    def test_set_services(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        cushy_post_integration.token = "X-Cushypost-JWT_LOGIN"
        cushy_post_integration.refresh_token = "X-Cushypost-Refresh-JWT_REFRESH"
        calendar_holiday_resp = {"response": {"succeed": True, "errcode": 200, "errmsg": None, "error": None, "data": [{"date": "2021-01-01", "localName": "Capodanno", "name": "NewYear'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": 1967, "type": "Public"}, {"date": "2021-01-06", "localName": "Epifania", "name": "Epiphany", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-04-04", "localName": "Pasqua", "name": "EasterSunday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-04-05", "localName": "Lunedìdell'Angelo", "name": "EasterMonday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": 1642, "type": "Public"}, {"date": "2021-04-25", "localName": "FestadellaLiberazione", "name": "LiberationDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-05-01", "localName": "FestadelLavoro", "name": "InternationalWorkersDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-06-02", "localName": "FestadellaRepubblica", "name": "RepublicDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-08-15", "localName": "FerragostooAssunzione", "name": "AssumptionDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-11-01", "localName": "Tuttiisanti", "name": "AllSaintsDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-12-08", "localName": "ImmacolataConcezione", "name": "ImmaculateConception", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-12-25", "localName": "Natale", "name": "ChristmasDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-12-26", "localName": "SantoStefano", "name": "St.Stephen'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-01-01", "localName": "Capodanno", "name": "NewYear'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": 1967, "type": "Public"}, {"date": "2022-01-06", "localName": "Epifania", "name": "Epiphany", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-04-17", "localName": "Pasqua", "name": "EasterSunday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-04-18", "localName": "Lunedìdell'Angelo", "name": "EasterMonday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": 1642, "type": "Public"}, {"date": "2022-04-25", "localName": "FestadellaLiberazione", "name": "LiberationDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-05-01", "localName": "FestadelLavoro", "name": "InternationalWorkersDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-06-02", "localName": "FestadellaRepubblica", "name": "RepublicDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-08-15", "localName": "FerragostooAssunzione", "name": "AssumptionDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-11-01", "localName": "Tuttiisanti", "name": "AllSaintsDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-12-08", "localName": "ImmacolataConcezione", "name": "ImmaculateConception", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-12-25", "localName": "Natale", "name": "ChristmasDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-12-26", "localName": "SantoStefano", "name": "St.Stephen'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}]}}

        responses.add(responses.POST, "{}/calendar/holidays".format(cushy_post_integration.domain),
                      json=calendar_holiday_resp,
                      status=200)
        cushy_post_integration.from_location = {'administrative_area_level_1': 'Lazio',
                                                'administrative_area_level_2': 'RM',
                                                'city': 'Vivaro Romano', 'contact': '', 'country': 'IT', 'email': '',
                                                'hash': 'b9b645b94641103026828a421dec14ce', 'locality': 'Vivaro Romano',
                                                'location': {'lat': '42.09882', 'lng': '13.00659',
                                                             'location_type': 'APPROXIMATE'},
                                                'name': 'from', 'phone': '', 'postalcode': '00020',
                                                'province': 'RM', 'type': 'geodb',
                                                'validity': {'component': 'postalcode', 'valid': True}}
        cushy_post_integration.set_services("2021")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(json.loads(responses.calls[0].request.body), {"app": cushy_post_integration.app,
                                                                       "year": "2021",
                                                                       "country": "IT"})
        collection_date = cushy_post_integration.services.get("collection", {}).pop("date", None)
        self.assertEqual(cushy_post_integration.services, {'cash_on_delivery': {'currency': 'EUR', 'value': 0},
                                                           'collection': {'hours': [10, 14]},
                                                           'insurance': {'algorithm': 'none',
                                                                         'currency': 'EUR',
                                                                         'value': 0}})
        self.assertNotIn(collection_date.split("T")[0],
                         [holiday["date"] for holiday in calendar_holiday_resp["response"]["data"]])

    @responses.activate
    def test_set_services_all_details(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        cushy_post_integration.token = "X-Cushypost-JWT_LOGIN"
        cushy_post_integration.refresh_token = "X-Cushypost-Refresh-JWT_REFRESH"
        calendar_holiday_resp = {"response": {"succeed": True, "errcode": 200, "errmsg": None, "error": None, "data": [{"date": "2021-01-01", "localName": "Capodanno", "name": "NewYear'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": 1967, "type": "Public"}, {"date": "2021-01-06", "localName": "Epifania", "name": "Epiphany", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-04-04", "localName": "Pasqua", "name": "EasterSunday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-04-05", "localName": "Lunedìdell'Angelo", "name": "EasterMonday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": 1642, "type": "Public"}, {"date": "2021-04-25", "localName": "FestadellaLiberazione", "name": "LiberationDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-05-01", "localName": "FestadelLavoro", "name": "InternationalWorkersDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-06-02", "localName": "FestadellaRepubblica", "name": "RepublicDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-08-15", "localName": "FerragostooAssunzione", "name": "AssumptionDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-11-01", "localName": "Tuttiisanti", "name": "AllSaintsDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-12-08", "localName": "ImmacolataConcezione", "name": "ImmaculateConception", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-12-25", "localName": "Natale", "name": "ChristmasDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2021-12-26", "localName": "SantoStefano", "name": "St.Stephen'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-01-01", "localName": "Capodanno", "name": "NewYear'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": 1967, "type": "Public"}, {"date": "2022-01-06", "localName": "Epifania", "name": "Epiphany", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-04-17", "localName": "Pasqua", "name": "EasterSunday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-04-18", "localName": "Lunedìdell'Angelo", "name": "EasterMonday", "countryCode": "IT", "fixed": False, "global": True, "counties": None, "launchYear": 1642, "type": "Public"}, {"date": "2022-04-25", "localName": "FestadellaLiberazione", "name": "LiberationDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-05-01", "localName": "FestadelLavoro", "name": "InternationalWorkersDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-06-02", "localName": "FestadellaRepubblica", "name": "RepublicDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-08-15", "localName": "FerragostooAssunzione", "name": "AssumptionDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-11-01", "localName": "Tuttiisanti", "name": "AllSaintsDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-12-08", "localName": "ImmacolataConcezione", "name": "ImmaculateConception", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-12-25", "localName": "Natale", "name": "ChristmasDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}, {"date": "2022-12-26", "localName": "SantoStefano", "name": "St.Stephen'sDay", "countryCode": "IT", "fixed": True, "global": True, "counties": None, "launchYear": None, "type": "Public"}]}}

        responses.add(responses.POST, "{}/calendar/holidays".format(cushy_post_integration.domain),
                      json=calendar_holiday_resp,
                      status=200)
        cushy_post_integration.from_location = {'administrative_area_level_1': 'Lazio',
                                                'administrative_area_level_2': 'RM',
                                                'city': 'Vivaro Romano', 'contact': '', 'country': 'IT', 'email': '',
                                                'hash': 'b9b645b94641103026828a421dec14ce', 'locality': 'Vivaro Romano',
                                                'location': {'lat': '42.09882', 'lng': '13.00659',
                                                             'location_type': 'APPROXIMATE'},
                                                'name': 'from', 'phone': '', 'postalcode': '00020',
                                                'province': 'RM', 'type': 'geodb',
                                                'validity': {'component': 'postalcode', 'valid': True}}
        cushy_post_integration.set_services("2021", month="11", day="1", insurance_value="10.0", cash_on_delivery="10")
        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(json.loads(responses.calls[0].request.body), {"app": cushy_post_integration.app,
                                                                       "year": "2021",
                                                                       "country": "IT"})
        collection_date = cushy_post_integration.services.get("collection", {}).pop("date", None)
        self.assertEqual(cushy_post_integration.services, {'cash_on_delivery': {'currency': 'EUR', 'value': 10},
                                                           'collection': {'hours': [10, 14]},
                                                           'insurance': {'algorithm': 'any',
                                                                         'currency': 'EUR',
                                                                         'value': 10.0}})
        self.assertEqual(collection_date.split("T")[0], "2021-11-02")
        self.assertNotIn(collection_date.split("T")[0],
                         [holiday["date"] for holiday in calendar_holiday_resp["response"]["data"]])

    @responses.activate
    def test_rate_generation(self):
        cushy_post_integration = CushyPostIntegration("TEST", "NEW_APP")
        cushy_post_integration.token = "X-Cushypost-JWT_LOGIN"
        cushy_post_integration.refresh_token = "X-Cushypost-Refresh-JWT_REFRESH"
        cushy_post_integration.from_location = {'administrative_area_level_1': 'Lazio',
                                                'administrative_area_level_2': 'RM',
                                                'city': 'Vivaro Romano', 'contact': '', 'country': 'IT', 'email': '',
                                                'hash': 'b9b645b94641103026828a421dec14ce', 'locality': 'Vivaro Romano',
                                                'location': {'lat': '42.09882', 'lng': '13.00659',
                                                             'location_type': 'APPROXIMATE'},
                                                'name': 'from', 'phone': '', 'postalcode': '00020',
                                                'province': 'RM', 'type': 'geodb',
                                                'validity': {'component': 'postalcode', 'valid': True}}
        cushy_post_integration.to_location = {'administrative_area_level_1': 'Lazio', 'administrative_area_level_2': 'RM',
                                              'city': 'Subiaco', 'contact': '', 'country': 'IT', 'email': '',
                                              'hash': 'a006fcf1d1a756168439393a59002120', 'locality': 'Subiaco',
                                              'location': {'lat': '41.92532',
                                                           'lng': '13.09276',
                                                           'location_type': 'APPROXIMATE'},
                                              'name': 'to', 'phone': '', 'postalcode': '00028',
                                              'province': 'RM', 'type': 'geodb',
                                              'validity': {'component': 'postalcode', 'valid': True}}
        cushy_post_integration.services = {'cash_on_delivery': {'currency': 'EUR', 'value': 0},
                                           'collection': {'date': '2021-10-06T15:31:51Z', 'hours': [10, 14]},
                                           'insurance': {'algorithm': 'none',
                                                         'currency': 'EUR',
                                                         'value': 0}}
        cushy_post_integration.set_shipping([{
            "type": "Parcel",
            "height": "10",
            "width": "10",
            "length": "10",
            "weight": "10"
        }, {
            "type": "Pallet",
            "height": "10",
            "width": "10",
            "length": "10",
            "weight": "10"
        }])
        shipment_rate_resp = {
            "response": {
                "succeed": True,
                "errcode": 200,
                "errmsg": None,
                "error": None,
                "data": {
                    "currency": "EUR",
                    "best_price": {
                        "id": {
                            "$oid": "61571df49361ef4712506e42"
                        },
                        "call": "61571df392efd",
                        "label": "TNT",
                        "product": "Express",
                        "delivery_time": "P1D",
                        "cost": 22.15,
                        "details": {
                            "insurance_algorithm": "none"
                        },
                        "currency": "EUR",
                        "contract": {
                            "$oid": "57f25d82beb0b0ec7ad44b9b"
                        },
                        "disabled": False,
                        "vat_rate": 1.22,
                        "vat": 6.16,
                        "net_price": 27.99,
                        "price": 34.15,
                        "trouble_rate": 0.05
                    },
                    "best_time": {
                        "id": {
                            "$oid": "61571df49361ef4712506e42"
                        },
                        "call": "61571df392efd",
                        "label": "TNT",
                        "product": "Express",
                        "delivery_time": "P1D",
                        "cost": 22.15,
                        "details": {
                            "insurance_algorithm": "none"
                        },
                        "currency": "EUR",
                        "contract": {
                            "$oid": "57f25d82beb0b0ec7ad44b9b"
                        },
                        "disabled": False,
                        "vat_rate": 1.22,
                        "vat": 6.16,
                        "net_price": 27.99,
                        "price": 34.15,
                        "trouble_rate": 0.05
                    },
                    "list": [
                        {
                            "id": {
                                "$oid": "61571df49361ef4712506e42"
                            },
                            "call": "61571df392efd",
                            "label": "TNT",
                            "product": "Express",
                            "delivery_time": "P1D",
                            "cost": 22.15,
                            "details": {
                                "insurance_algorithm": "none"
                            },
                            "currency": "EUR",
                            "contract": {
                                "$oid": "57f25d82beb0b0ec7ad44b9b"
                            },
                            "disabled": False,
                            "vat_rate": 1.22,
                            "vat": 6.16,
                            "net_price": 27.99,
                            "price": 34.15,
                            "trouble_rate": 0.05
                        }
                    ]
                }
            }
        }
        responses.add(responses.POST, "{}/shipment/rate".format(cushy_post_integration.domain),
                      json=shipment_rate_resp,
                      status=200)
        cushy_post_integration.get_rates()
        self.assertEqual(len(responses.calls), 1)
        request_sent =json.loads(responses.calls[0].request.body)
        request_sent["shipping"]["packages"][0]["hash"] = "HASH"
        request_sent["shipping"]["packages"][1]["hash"] = "HASH"
        self.assertEqual(request_sent, {"app": "NEW_APP", "from": {"administrative_area_level_1": "Lazio", "administrative_area_level_2": "RM", "city": "Vivaro Romano", "contact": "", "country": "IT", "email": "", "hash": "b9b645b94641103026828a421dec14ce", "locality": "Vivaro Romano", "location": {"lat": "42.09882", "lng": "13.00659", "location_type": "APPROXIMATE"}, "name": "from", "phone": "", "postalcode": "00020", "province": "RM", "type": "geodb", "validity": {"component": "postalcode", "valid": True}}, "to": {"administrative_area_level_1": "Lazio", "administrative_area_level_2": "RM", "city": "Subiaco", "contact": "", "country": "IT", "email": "", "hash": "a006fcf1d1a756168439393a59002120", "locality": "Subiaco", "location": {"lat": "41.92532", "lng": "13.09276", "location_type": "APPROXIMATE"}, "name": "to", "phone": "", "postalcode": "00028", "province": "RM", "type": "geodb", "validity": {"component": "postalcode", "valid": True}}, "shipping": {"total_weight": 20, "goods_desc": "content", "product": "All", "special_instructions": "Questo \u00e8 solo un test. Si prega di cancellare!", "packages": [{"type": "Parcel", "height": "10", "width": "10", "length": "10", "weight": "10", "content": "content", "hash": "HASH"}, {"type": "Pallet", "height": "10", "width": "10", "length": "10", "weight": "10", "content": "content", "hash": "HASH"}]}, "services": {"cash_on_delivery": {"currency": "EUR", "value": 0}, "collection": {"date": "2021-10-06T15:31:51Z", "hours": [10, 14]}, "insurance": {"algorithm": "none", "currency": "EUR", "value": 0}}})
