# CushypostIntegration

Module to integrate the API exposed by CushyPost: https://www.cushypost.com/

``` python
import cushyPostIntegration
client = cushyPostIntegration.CushyPostIntegration("TEST", "MY_APP")
client.login("USERNAME", "PASSWORD")
client.set_from("IT", "00150", "Roma")
client.search_geo_db("IT", "2015")
client.set_to("IT", "20150", "Milano")
client.set_services("2021")
client.set_shipping([{
	"type": "Parcel",
	"height": "10",
	"width": "10",
	"length": "10",
	"weight": "10"
}])
rate_id = client.get_rates()["list"][0]["id"]["$oid"]
client.approve_quotation(
    rate_id,
    {
        "country": "IT",
        "zipCode": "00150",
        "city": "Roma"
    },
    {
        "country": "IT",
        "zipCode": "20150",
        "city": "Milano"
    },
    {
        "year": "2021"
    },
    shipping_extra_data={
        "packages": [{
            "type": "Parcel",
            "height": "10",
            "width": "10",
            "length": "10",
            "weight": "10"
        }]
    })
shipping_ids = client.search_by_quotation_id([rate_id])
client.add_shipping_ids_to_cart(shipping_ids)
url = "http://localhost:5000"
client.buy_cart("{}&success=true".format(url),
                url,
                "Finalize your payment")
client.confirm_cart()
client.get_shipment_label(shipping_ids)
```