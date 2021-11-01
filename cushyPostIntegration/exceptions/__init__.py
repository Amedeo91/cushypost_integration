

class LoginFailed(Exception):
    def __init__(self):
        super(LoginFailed, self).__init__("LOGIN FAILED")


class RefreshFailed(Exception):
    def __init__(self):
        super(RefreshFailed, self).__init__("REFRESH FAILED")


class MissingToken(Exception):
    def __init__(self):
        super(MissingToken, self).__init__("MISSING TOKENS")


class GeoDbAutoComplete(Exception):
    def __init__(self):
        super(GeoDbAutoComplete, self).__init__("GEODB AUTOCOMPLETE FAILED")


class MissingFrom(Exception):
    def __init__(self):
        super(MissingFrom, self).__init__("MISSING FROM")


class MissingData(Exception):
    def __init__(self):
        super(MissingData, self).__init__("MISSING DATA")


class ShippingRateFailed(Exception):
    def __init__(self):
        super(ShippingRateFailed, self).__init__("SHIPPING RATE FAILED")


class ApproveRateFailed(Exception):
    def __init__(self):
        super(ApproveRateFailed, self).__init__("APPROVE RATE FAILED")


class SearchPaidShipmentsFailed(Exception):
    def __init__(self):
        super(SearchPaidShipmentsFailed, self).__init__("SEARCH PAID SHIPMENTS FAILED")


class SearchQuotationFailed(Exception):
    def __init__(self):
        super(SearchQuotationFailed, self).__init__("SEARCH QUOTATION FAILED")


class NoQuotationFoundFailed(Exception):
    def __init__(self):
        super(NoQuotationFoundFailed, self).__init__("NO QUOTATION FOUND")


class AddToCartFailed(Exception):
    def __init__(self):
        super(AddToCartFailed, self).__init__("ADD TO CART FAILED")


class RemoveFromCartFailed(Exception):
    def __init__(self):
        super(RemoveFromCartFailed, self).__init__("REMOVE FROM CART FAILED")


class BuyCartFailed(Exception):
    def __init__(self):
        super(BuyCartFailed, self).__init__("BUY CART FAILED")


class ConfirmCartFailed(Exception):
    def __init__(self):
        super(ConfirmCartFailed, self).__init__("CONFIRM CART FAILED")


class ConfirmCartMissingParameters(Exception):
    def __init__(self):
        super(ConfirmCartMissingParameters, self).__init__("CONFIRM CART FAILED - MISSING PARAMETERS")


class InvalidEnvironment(Exception):
    def __init__(self):
        super(InvalidEnvironment, self).__init__("ENVIRONMENT NOT VALID")
