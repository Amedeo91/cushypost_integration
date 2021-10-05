import unittest
from cushyPostIntegration import CushyPostIntegration
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
        self.assertEqual(cushy_post_integration.token, "X-Cushypost-JWT_LOGIN")
        self.assertEqual(cushy_post_integration.refresh_token, "X-Cushypost-Refresh-JWT_REFRESH")

