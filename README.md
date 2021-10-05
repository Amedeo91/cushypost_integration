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
client.get_rates()
```