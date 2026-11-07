"""Tests for the Moreton Bay integration."""

from datetime import date, timedelta

from custom_components.moreton_bay.client import (
    build_where_clause,
    parse_catalogue,
    parse_waste_property,
)
from custom_components.moreton_bay.waste import (
    collection_type,
    next_collection_date,
    next_recycle_date,
    put_out_tonight,
    recycle_out_tonight,
)

CATALOGUE_FIXTURE = {
    "features": [
        {
            "properties": {
                "title": (
                    "City of Moreton Bay Property Waste Collection Days "
                    "and Recycle Weeks"
                ),
                "url": "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/MBRC_Waste/FeatureServer",
                "snippet": "Bin days",
            }
        },
        {
            "properties": {
                "title": "Moreton Bay Regional Council - Sandbag Locations (Open)",
                "url": "https://services-ap1.arcgis.com/x/arcgis/rest/services/MBRC_Sandbag_Locations_and_Evacuation_Centres_(Open)/FeatureServer/0",
            }
        },
        {"properties": {"title": "", "url": ""}},
    ]
}

WASTE_FIXTURE = {
    "features": [
        {
            "attributes": {
                "ADDRESS": "5 BOTANY CRESCENT BANKSIA BEACH",
                "Bin_Day": "TUESDAY",
                "Recycle_Week": "WEEK 1",
                "Suburb": "BANKSIA BEACH",
            }
        }
    ]
}


def test_parse_catalogue_skips_empty_and_sorts() -> None:
    layers = parse_catalogue(CATALOGUE_FIXTURE)
    assert len(layers) == 2
    assert layers[0].title.startswith("City of Moreton Bay")
    assert layers[1].layer == 0
    # query_url for a layer-suffixed URL is unchanged + /query
    assert layers[1].query_url().endswith("/FeatureServer/0/query")


def test_build_where_clause_escapes_quotes() -> None:
    assert build_where_clause("5 O'Brien St") == "upper(ADDRESS) = '5 O''BRIEN ST'"


def test_parse_waste_property() -> None:
    result = parse_waste_property(WASTE_FIXTURE)
    assert result is not None
    assert result["Bin_Day"] == "TUESDAY"
    assert parse_waste_property({"features": []}) is None


def test_next_collection_date() -> None:
    # 2026-11-07 is a Saturday; next Tuesday is 2026-11-10.
    assert next_collection_date("tuesday", date(2026, 11, 7)) == date(2026, 11, 10)
    # Same-day counts as today.
    assert next_collection_date("SATURDAY", date(2026, 11, 7)) == date(2026, 11, 7)
    assert next_collection_date("BOGUS", date(2026, 11, 7)) is None


def test_put_out_tonight() -> None:
    # Monday 2026-11-09 is the night before Tuesday collection.
    assert put_out_tonight("TUESDAY", date(2026, 11, 9)) is True
    assert put_out_tonight("TUESDAY", date(2026, 11, 8)) is False


def test_next_recycle_datefortnightly() -> None:
    # EPOCH Monday 2026-01-05 = WEEK 1. Tuesday 2026-11-10 follows 44 weeks later?
    nxt = next_recycle_date("TUESDAY", "WEEK 1", date(2026, 11, 7))
    assert nxt is not None
    assert nxt.weekday() == 1  # Tuesday
    assert collection_type("TUESDAY", "WEEK 1", date(2026, 11, 7)) in (
        "Recycling",
        "Organics",
    )


def test_recycle_out_tonight() -> None:
    # If next Tuesday is a recycle week, Monday night is out.
    nxt = next_recycle_date("TUESDAY", "WEEK 1", date(2026, 11, 7))
    assert nxt is not None
    assert recycle_out_tonight("TUESDAY", "WEEK 1", nxt - timedelta(days=1)) is True
