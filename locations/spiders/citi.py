# -*- coding: utf-8 -*-
import scrapy

from scrapy.http import JsonRequest

from locations.items import GeojsonPointItem


class CitiSpider(scrapy.Spider):
    name = "citi"
    item_attributes = {"brand": "Citi", "brand_wikidata": "Q219508"}
    allowed_domains = ["citi.com"]
    download_delay = 1.5

    headers = {"client_id": "4a51fb19-a1a7-4247-bc7e-18aa56dd1c40"}

    def start_requests(self):
        with open(
            "./locations/searchable_points/us_centroids_100mile_radius_state.csv"
        ) as points:
            next(points)
            for point in points:
                _, lat, lon, state = point.strip().split(",")
                if state not in {"AK", "HI"}:
                    yield JsonRequest(
                        url="https://online.citi.com/gcgapi/prod/public/v1/geoLocations/places/retrieve",
                        headers=self.headers,
                        data={
                            "type": "branchesAndATMs",
                            "inputLocation": [float(lon), float(lat)],
                            "resultCount": "1000",
                            "distanceUnit": "MILE",
                            "findWithinRadius": "100",
                        },
                    )

        # Alaska and Hawaii
        for point in [[-149.318198, 62.925651], [-156.400325, 20.670266]]:
            yield JsonRequest(
                url="https://online.citi.com/gcgapi/prod/public/v1/geoLocations/places/retrieve",
                headers=self.headers,
                data={
                    "type": "branchesAndATMs",
                    "inputLocation": point,
                    "resultCount": "1000",
                    "distanceUnit": "MILE",
                    "findWithinRadius": "1000",
                },
            )

    def parse(self, response):
        data = response.json()

        for feature in data["features"]:
            postcode = feature["properties"]["postalCode"]

            # fix 4-digit postcodes :(
            if (
                feature["properties"]["country"] == "united states of america"
                and postcode
            ):
                postcode = postcode.zfill(5)

            properties = {
                "ref": feature["id"],
                "name": feature["properties"]["name"],
                "street_address": feature["properties"]["addressLine1"].strip(),
                "city": feature["properties"]["city"].title(),
                "state": feature["properties"]["state"].upper(),
                "postcode": postcode,
                "country": feature["properties"]["country"].title(),
                "phone": feature["properties"]["phone"],
                "lat": float(feature["geometry"]["coordinates"][1]),
                "lon": float(feature["geometry"]["coordinates"][0]),
                "extras": {"type": feature["properties"]["type"]},
            }

            yield GeojsonPointItem(**properties)
