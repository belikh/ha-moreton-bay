# City of Moreton Bay

Home Assistant integration for the **City of Moreton Bay** — Queensland, Australia.

Everything in here comes from the council's public **Datahub** (ArcGIS Hub,
Creative Commons Attribution 4.0). Every endpoint is **token-free**: no API
keys, no add-ons, no MQTT broker.

## What you get

- **All Datahub layers** — every published dataset (currently ~85 feature
  services: waste, road closures, sandbags and evacuation centres, waste
  facilities, parks, dog beaches, bus stops, planned burns, flood and bushfire
  overlays, planning zones, and the rest) becomes a sensor showing its
  feature count and source URL.
- **Property waste collection days** — given one exact address
  (e.g. `5 BOTANY CRESCENT BANKSIA BEACH`), sensors/binary sensor answer
  "next bin collection" and "put bins out tonight?" using the council's
  `Property Waste Collection Days and Recycle Weeks` feed
  (216,000+ properties, live-tested).

This is the Moreton Bay counterpart to the Brisbane City Council bin day
integrations (`mark1foley/Brisbane-Bin-Day-Sensor`, `matterbury/Brisbane-Bin-Day`).
Unlike those, this one covers every layer the council publishes, not just bins.

## Install (HACS)

1. Open HACS and add a custom repository:
   `https://github.com/belikh/ha-moreton-bay` as type **Integration**.
2. Install **City of Moreton Bay** and restart Home Assistant.
3. Add the integration:

   - **All Datahub layers** — one sensor per dataset.
   - **Property waste collection days** — enter the exact `ADDRESS`.
   - **Single Datahub layer** — enter one dataset title.

## Waste address lookup

The waste feed matches on the council's upper-case `ADDRESS` field exactly.
Find yours on council's Datahub (`MBRC_Waste`) or via "When are my bins
collected?" and paste it in.

General waste is weekly; recycling and garden organics alternate fortnightly
(`WEEK 1` / `WEEK 2`). Public-holiday shifts are not modelled — the council
publishes them separately.

## Development

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy
```

hassfest can be run with
`python -m homeassistant.hassfest` via the script in `.github/workflows/`.

## Licence

MIT. Data © City of Moreton Bay, CC-BY 4.0. Unofficial; not endorsed by the council.
