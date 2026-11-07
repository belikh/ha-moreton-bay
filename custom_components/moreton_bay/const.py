"""Constants for the Moreton Bay integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "moreton_bay"

CONF_MODE = "mode"
CONF_ADDRESS = "address"
CONF_LAYER_TITLE = "layer_title"
CONF_SCAN_INTERVAL = "scan_interval_hours"

MODE_ALL_LAYERS = "all_layers"
MODE_WASTE = "waste"
MODE_SINGLE_LAYER = "single_layer"

DATAHUB_CATALOGUE_URL = (
    "https://datahub.moretonbay.qld.gov.au/api/search/v1/collections/dataset/items"
)
DATAHUB_BASE = "https://datahub.moretonbay.qld.gov.au"

MBRC_WASTE_URL = (
    "https://services-ap1.arcgis.com/152ojN3Ts9H3cdtl/arcgis/rest/services/"
    "MBRC_Waste/FeatureServer"
)
MBRC_WASTE_LAYER = 0

ARCGIS_ORG_ID = "152ojN3Ts9H3cdtl"

DEFAULT_SCAN_INTERVAL = timedelta(hours=6)
MIN_SCAN_INTERVAL_HOURS = 1
MAX_SCAN_INTERVAL_HOURS = 48

ATTR_LAYER_TITLE = "layer_title"
ATTR_FEATURE_COUNT = "feature_count"
ATTR_SOURCE_URL = "source_url"
ATTR_LAST_UPDATED = "last_updated"
