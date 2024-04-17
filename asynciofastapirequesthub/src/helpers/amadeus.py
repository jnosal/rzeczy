import json
import logging
import uuid

import httpx
from starlette.status import HTTP_408_REQUEST_TIMEOUT

from ..conf import settings

DEFAULT_CURRENCY = "PLN"
DEFAULT_TIMEOUT = 10


class Journey:  # pragma: no cover
    RETURN = "return"
    ONE_WAY = "one-way"
    MULTI_CITY = "multicity"


class CabinClass:  # pragma: no cover
    ANY = "any"


cabin_class_map = {
    CabinClass.ANY: "",
    "first": "FIRST",
    "business": "BUSINESS",
    "premium_economy": "PREMIUM_ECONOMY",
    "economy": "ECONOMY",
}


logger = logging.getLogger(__name__)


class Amadeus:
    def __init__(
        self,
        client,
        base_url=settings.AMADEUS_API_URL,
        api_key=settings.AMADEUS_API_KEY,
        api_secret=settings.AMADEUS_API_SECRET,
    ):
        self.client = client
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None

    def api_url(self, path):
        return f"{self.base_url}/{path}"

    def _get_client_request_id(self):
        return uuid.uuid4().hex

    @property
    def _default_headers(self):
        return {
            "Ama-Client-Ref": self._get_client_request_id(),
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def async_install_access_token(self):
        if self.access_token is None:
            self.access_token = await self.async_request_access_token()

    async def async_request_access_token(self):
        url = self.api_url("v1/security/oauth2/token")
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret,
        }
        headers = {
            "Ama-Client-Ref": self._get_client_request_id(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        logger.info(
            f"[AMADEUS] sending POST to {url} with {data} and headers={headers}"
        )
        r = await self.client.post(
            url,
            headers=headers,
            data=data,
            timeout=DEFAULT_TIMEOUT,
        )
        data = r.json()
        return data["access_token"]

    async def async_search(
        self,
        flights,
        passengers_map,
        cabin_class=CabinClass.ANY,
        currency_code=DEFAULT_CURRENCY,
    ):
        await self.async_install_access_token()
        url = self.api_url("v2/shopping/flight-offers")

        data = {
            "currencyCode": currency_code,
            "searchCriteria": {
                "allowAlternativeFareOptions": True,
                "additionalInformation": {
                    "chargeableCheckedBags": True,
                },
            },
            "originDestinations": [
                {
                    "id": index + 1,
                    "originLocationCode": flight["departure"]["iata"],
                    "destinationLocationCode": flight["arrival"]["iata"],
                    "departureDateTimeRange": {"date": flight["departure_date"]},
                }
                for (index, flight) in enumerate(flights)
            ],
            "travelers": [
                *[
                    {
                        "id": index1 + 1,
                        "travelerType": "ADULT",
                        "fareOptions": ["STANDARD"],
                    }
                    for index1 in range(0, passengers_map["adults"])
                ],
                *[
                    {
                        "id": index2 + 1 + passengers_map["adults"],
                        "travelerType": "CHILD",
                        "fareOptions": ["STANDARD"],
                    }
                    for (index2, age) in enumerate(passengers_map["children"])
                ],
            ],
            "sources": ["GDS", "PYTON", "LTC", "EAC", "NDC"],
        }

        if cabin_class and cabin_class != CabinClass.ANY:
            data["searchCriteria"]["flightFilters"] = {
                "cabinRestrictions": [
                    {
                        "cabin": cabin_class_map[cabin_class],
                        "originDestinationIds": [
                            i["id"] for i in data.get("originDestinations")
                        ],
                    }
                ]
            }

        json_data = json.dumps(data)

        logger.debug(
            f"[AMADEUS] sending POST to {url} with {json_data} and headers={self._default_headers}"
        )
        try:
            r = await self.client.post(
                url,
                data=json_data,
                headers=self._default_headers,
                timeout=DEFAULT_TIMEOUT,
            )
            data = r.json()
        except httpx.TimeoutException:
            return {"data": [], "status": HTTP_408_REQUEST_TIMEOUT}

        return {"data": data.get("data", []), "status": r.status_code}
