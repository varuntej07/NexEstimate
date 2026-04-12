"""
Unit tests for _parse_property.

_parse_property is a pure function: it takes a raw RapidAPI response dict and returns a PropertyEstimate. 
No I/O, no side effects. These tests cover:

  - Correct field extraction from a full upstream response
  - Graceful degradation when individual fields are absent (no exceptions,
    nullable fields return None)
  - zillow_url construction fallback chain: zillowURL -> hdpUrl -> None
  - full_address construction with partial address components
"""

from api.core import PropertyEstimate, _parse_property


class TestFullResponse:
    """All fields present — verify every extracted value is correct."""

    def test_zestimate(self, full_property_response):
        assert _parse_property(full_property_response).zestimate == 850000

    def test_rent_zestimate(self, full_property_response):
        assert _parse_property(full_property_response).rent_zestimate == 3200

    def test_zestimate_range_low(self, full_property_response):
        result = _parse_property(full_property_response)
        assert result.zestimate_range is not None
        assert result.zestimate_range.low_percent == "5"

    def test_zestimate_range_high(self, full_property_response):
        result = _parse_property(full_property_response)
        assert result.zestimate_range is not None
        assert result.zestimate_range.high_percent == "10"

    def test_address_street(self, full_property_response):
        assert _parse_property(full_property_response).street_address == "328 26th Avenue"

    def test_address_city(self, full_property_response):
        assert _parse_property(full_property_response).city == "Seattle"

    def test_address_state(self, full_property_response):
        assert _parse_property(full_property_response).state == "WA"

    def test_address_zipcode(self, full_property_response):
        assert _parse_property(full_property_response).zipcode == "98122"

    def test_full_address_construction(self, full_property_response):
        assert _parse_property(full_property_response).full_address == "328 26th Avenue, Seattle, WA 98122"

    def test_bedrooms(self, full_property_response):
        assert _parse_property(full_property_response).bedrooms == 3

    def test_bathrooms(self, full_property_response):
        assert _parse_property(full_property_response).bathrooms == 2.0

    def test_living_area(self, full_property_response):
        assert _parse_property(full_property_response).living_area == 1800

    def test_lot_size(self, full_property_response):
        assert _parse_property(full_property_response).lot_size == 5000.0

    def test_year_built(self, full_property_response):
        assert _parse_property(full_property_response).year_built == 1998

    def test_home_type(self, full_property_response):
        assert _parse_property(full_property_response).home_type == "SINGLE_FAMILY"

    def test_home_status(self, full_property_response):
        assert _parse_property(full_property_response).home_status == "FOR_SALE"

    def test_price(self, full_property_response):
        assert _parse_property(full_property_response).price == 895000

    def test_last_sold_price(self, full_property_response):
        assert _parse_property(full_property_response).last_sold_price == 720000

    def test_zpid(self, full_property_response):
        assert _parse_property(full_property_response).zpid == 12345678

    def test_image_url_prefers_hi_res(self, full_property_response):
        result = _parse_property(full_property_response)
        assert result.image_url == "https://photos.zillowstatic.com/fp/abc123.jpg"

    def test_zillow_url_top_level_field(self, full_property_response):
        result = _parse_property(full_property_response)
        assert result.zillow_url == "https://www.zillow.com/homedetails/12345678_zpid/"

    def test_returns_property_estimate_instance(self, full_property_response):
        assert isinstance(_parse_property(full_property_response), PropertyEstimate)


class TestGracefulDegradation:
    """
    Partial or schema-shifted upstream responses must not raise exceptions.
    Every Optional field must return None rather than crashing when absent.
    """

    def test_missing_zestimate_returns_none(self, full_property_response):
        del full_property_response["propertyDetails"]["zestimate"]
        assert _parse_property(full_property_response).zestimate is None

    def test_missing_rent_zestimate_returns_none(self, full_property_response):
        del full_property_response["propertyDetails"]["rentZestimate"]
        assert _parse_property(full_property_response).rent_zestimate is None

    def test_missing_bedrooms_returns_none(self, full_property_response):
        del full_property_response["propertyDetails"]["bedrooms"]
        assert _parse_property(full_property_response).bedrooms is None

    def test_missing_year_built_returns_none(self, full_property_response):
        del full_property_response["propertyDetails"]["yearBuilt"]
        assert _parse_property(full_property_response).year_built is None

    def test_missing_zpid_returns_none(self, full_property_response):
        del full_property_response["propertyDetails"]["zpid"]
        assert _parse_property(full_property_response).zpid is None

    def test_empty_property_details_returns_all_none(self):
        result = _parse_property({"propertyDetails": {}})
        assert isinstance(result, PropertyEstimate)
        assert result.zestimate is None
        assert result.zpid is None
        assert result.street_address is None
        assert result.full_address is None

    def test_absent_property_details_key_returns_all_none(self):
        """
        The endpoint guards against this before calling _parse_property, but
        the function itself must still be safe against a totally empty input.
        """
        result = _parse_property({})
        assert isinstance(result, PropertyEstimate)
        assert result.zestimate is None
        assert result.zpid is None

    def test_null_zestimate_value_returns_none(self, full_property_response):
        """Zillow can return null for the zestimate on unlisted properties."""
        full_property_response["propertyDetails"]["zestimate"] = None
        assert _parse_property(full_property_response).zestimate is None


class TestZillowUrlFallback:
    """
    zillow_url construction follows a three-step fallback:
      1. Top-level zillowURL
      2. propertyDetails.hdpUrl prefixed with https://www.zillow.com
      3. None
    """

    def test_uses_top_level_zillow_url_when_present(self, full_property_response):
        result = _parse_property(full_property_response)
        assert result.zillow_url == "https://www.zillow.com/homedetails/12345678_zpid/"

    def test_falls_back_to_hdp_url_when_zillow_url_absent(self, full_property_response):
        del full_property_response["zillowURL"]
        result = _parse_property(full_property_response)
        assert result.zillow_url == (
            "https://www.zillow.com"
            "/homedetails/328-26th-Ave-Seattle-WA-98122/12345678_zpid/"
        )

    def test_empty_zillow_url_triggers_hdp_fallback(self, full_property_response):
        """An empty string zillowURL is treated as absent."""
        full_property_response["zillowURL"] = ""
        result = _parse_property(full_property_response)
        assert result.zillow_url is not None
        assert result.zillow_url.startswith("https://www.zillow.com/homedetails/")

    def test_returns_none_when_both_sources_missing(self, full_property_response):
        del full_property_response["zillowURL"]
        del full_property_response["propertyDetails"]["hdpUrl"]
        assert _parse_property(full_property_response).zillow_url is None


class TestFullAddressConstruction:
    """
    full_address is built by joining non-empty parts with ", ".
    Missing or empty components must be omitted cleanly.
    """

    def test_all_parts_present(self, full_property_response):
        assert _parse_property(full_property_response).full_address == (
            "328 26th Avenue, Seattle, WA 98122"
        )

    def test_missing_city_excluded(self, full_property_response):
        full_property_response["propertyDetails"]["city"] = ""
        result = _parse_property(full_property_response)
        assert result.full_address == "328 26th Avenue, WA 98122"

    def test_missing_state_and_zip_excluded(self, full_property_response):
        full_property_response["propertyDetails"]["state"] = ""
        full_property_response["propertyDetails"]["zipcode"] = ""
        result = _parse_property(full_property_response)
        assert result.full_address == "328 26th Avenue, Seattle"

    def test_only_street_present(self, full_property_response):
        full_property_response["propertyDetails"]["city"] = ""
        full_property_response["propertyDetails"]["state"] = ""
        full_property_response["propertyDetails"]["zipcode"] = ""
        result = _parse_property(full_property_response)
        assert result.full_address == "328 26th Avenue"

    def test_all_address_parts_missing_returns_none(self, full_property_response):
        full_property_response["propertyDetails"]["streetAddress"] = ""
        full_property_response["propertyDetails"]["city"] = ""
        full_property_response["propertyDetails"]["state"] = ""
        full_property_response["propertyDetails"]["zipcode"] = ""
        result = _parse_property(full_property_response)
        assert result.full_address is None
