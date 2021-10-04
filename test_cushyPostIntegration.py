import unittest
from cushyPostIntegration import CushyPostIntegration


class TestEmailSenderHelper(unittest.TestCase):
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
        except Exception as error:
            self.assertEqual(str(error), "ENVIRONMENT NOT VALID")
