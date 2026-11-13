<p align="right">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/belikh/design/main/packages/graphics/logo/jupiter-logo-dark.svg">
    <img alt="jupiter.au" src="https://raw.githubusercontent.com/belikh/design/main/packages/graphics/logo/jupiter-logo-light.svg" width="260">
  </picture>
</p>

# City of Moreton Bay

Home Assistant integration for the City of Moreton Bay, Queensland. It turns datasets from the council's Datahub into sensors, reports bin collection days for one property, and reports the nearest development application, road closure and emergency site to a zone. It needs no API key.

<p>
  <a href="#install">Install</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#entities">Entities</a> ·
  <a href="#bin-days">Bin days</a> ·
  <a href="#develop">Develop</a>
</p>

<br>

---

<br>

## Install

1. In HACS, add a custom repository: `https://github.com/belikh/ha-moreton-bay`, type **Integration**.
2. Install **City of Moreton Bay** and restart Home Assistant.
3. Go to **Settings > Devices & Services > Add integration** and pick **City of Moreton Bay**.

<br>

## Configuration

Setup is a short wizard.

| Step | Fields |
| --- | --- |
| Zone | Zone (default `zone.home`), radius in km (default 2, 0.1 to 50), refresh interval in hours (default 6, 1 to 48). |
| Address | Pick a suburb, street and house number from the council's list, or type the address. Leave it empty to use the property at the zone's position. |
| Confirm | Check the matched address. |

Change the refresh interval later under **Configure** on the integration card.

<br>

## Entities

| Entity | Type | Meaning |
| --- | --- | --- |
| One per Datahub layer | sensor | Number of features in the layer. Attributes: `layer_title`, `source_url`, `feature_count`. |
| Next bin collection | sensor | Date of the next general waste collection. |
| Next recycling collection | sensor | Date of the next recycling or garden organics collection. |
| Put bins out tonight | binary sensor | On when general waste is collected tomorrow. |
| Recycling out tonight | binary sensor | On when recycling is collected tomorrow. |
| Development application (nearest) | sensor | Nearest development application within the radius. |
| Road closure (nearest) | sensor | Nearest road closure within the radius. |
| Emergency site (nearest) | sensor | Nearest emergency site within the radius. |

The layer list comes from the council's Datahub (`datahub.moretonbay.qld.gov.au`, ArcGIS Hub). It is filtered to datasets that change over time. Datasets whose titles do not match the integration's list of live-data keywords, and historical datasets, are skipped.

<br>

## Bin days

The waste feed is `MBRC_Waste`. It matches the council's upper-case `ADDRESS` field, for example `5 BOTANY CRESCENT BANKSIA BEACH`. General waste is weekly. Recycling and garden organics alternate each fortnight (`WEEK 1` and `WEEK 2`).

> [!NOTE]
> Public holiday shifts are not modelled. The council publishes them separately.

<br>

## Develop

```sh
uv sync
uv run pytest
uv run ruff check .
uv run mypy
```

The `hacs` and `hassfest` workflows in `.github/workflows/` run the HACS and Home Assistant validations on GitHub.

<br>

## Licence

MIT. Data (c) City of Moreton Bay, CC BY 4.0. Unofficial; not endorsed by the council.

<br>

<p align="right"><sub>jupiter.au</sub></p>
