.. raw:: html

   <p align="right">
     <picture>
       <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/belikh/design/latest/packages/graphics/logo/jupiter-logo-dark.svg">
       <img alt="jupiter.au" src="https://raw.githubusercontent.com/belikh/design/latest/packages/graphics/logo/jupiter-logo-light.svg" width="260">
     </picture>
   </p>

   <h1>City of Moreton Bay</h1>

.. meta::
   :description: Home Assistant integration for the City of Moreton Bay, Queensland, with Datahub sensors, bin collection days and nearest-event sensors.

Home Assistant integration for the City of Moreton Bay, Queensland. It turns datasets from the council's Datahub into sensors, reports bin collection days for one property, and reports the nearest development application, road closure and emergency site to a zone. It needs no API key.

`Install`_ · `Configuration`_ · `Entities`_ · `Bin days`_ · `Develop`_

|

.. raw:: html

   <p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/rule/end-dark.svg"><img alt="" src="https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/rule/end-light.svg" width="50%"></picture></p>

Install
-------

1. In HACS, add a custom repository: ``https://github.com/belikh/ha-moreton-bay``, type **Integration**.
2. Install **City of Moreton Bay** and restart Home Assistant.
3. Go to **Settings > Devices & Services > Add integration** and pick **City of Moreton Bay**.

|

Configuration
-------------

Setup is a short wizard.

.. list-table::
   :header-rows: 1

   * - Step
     - Fields
   * - |pin-l| |pin-d| Zone
     - Zone (default ``zone.home``), radius in km (default 2, 0.1 to 50), refresh interval in hours (default 6, 1 to 48).
   * - |home-l| |home-d| Address
     - Pick a suburb, street and house number from the council's list, or type the address. Leave it empty to use the property at the zone's position.
   * - |check-l| |check-d| Confirm
     - Check the matched address.

Change the refresh interval later under **Configure** on the integration card.

|

Entities
--------

.. list-table::
   :header-rows: 1

   * - Entity
     - Type
     - Meaning
   * - |database-l| |database-d| One per Datahub layer
     - sensor
     - Number of features in the layer. Attributes: ``layer_title``, ``source_url``, ``feature_count``.
   * - |calendar-l| |calendar-d| Next bin collection
     - sensor
     - Date of the next general waste collection.
   * - |refresh-l| |refresh-d| Next recycling collection
     - sensor
     - Date of the next recycling or garden organics collection.
   * - |bell-l| |bell-d| Put bins out tonight
     - binary sensor
     - On when general waste is collected tomorrow.
   * - |bell-l| |bell-d| Recycling out tonight
     - binary sensor
     - On when recycling is collected tomorrow.
   * - |file-l| |file-d| Development application (nearest)
     - sensor
     - Nearest development application within the radius.
   * - |block-l| |block-d| Road closure (nearest)
     - sensor
     - Nearest road closure within the radius.
   * - |alert-l| |alert-d| Emergency site (nearest)
     - sensor
     - Nearest emergency site within the radius.

The layer list comes from the council's Datahub (``datahub.moretonbay.qld.gov.au``, ArcGIS Hub). It is filtered to datasets that change over time. Datasets whose titles do not match the integration's list of live-data keywords, and historical datasets, are skipped.

|

Bin days
--------

The waste feed is ``MBRC_Waste``. It matches the council's upper-case ``ADDRESS`` field, for example ``5 BOTANY CRESCENT BANKSIA BEACH``. General waste is weekly. Recycling and garden organics alternate each fortnight (``WEEK 1`` and ``WEEK 2``).

.. raw:: html

   <table>
     <tr align="left"><th>Note</th></tr>
     <tr><td>

Public holiday shifts are not modelled. The council publishes them separately.

.. raw:: html

   </td></tr>
   </table>

|

Develop
-------

.. code-block:: sh

   uv sync
   uv run pytest
   uv run ruff check .
   uv run mypy

The ``hacs`` and ``hassfest`` workflows in ``.github/workflows/`` run the HACS and Home Assistant validations on GitHub.

|

.. raw:: html

   <p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/rule/end-dark.svg"><img alt="" src="https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/rule/end-light.svg" width="50%"></picture></p>

Licence
-------

MIT. Data (c) City of Moreton Bay, CC BY 4.0. Unofficial; not endorsed by the council.

|

.. raw:: html

   <p align="right"><sub>jupiter.au</sub></p>

.. |pin-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/pin-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |pin-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/pin-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |home-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/home-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |home-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/home-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |check-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/check-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |check-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/check-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |database-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/database-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |database-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/database-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |calendar-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/calendar-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |calendar-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/calendar-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |refresh-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/refresh-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |refresh-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/refresh-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |bell-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/bell-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |bell-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/bell-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |file-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/file-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |file-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/file-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |block-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/block-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |block-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/block-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
.. |alert-l| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/alert-light.svg#gh-light-mode-only
   :width: 20
   :alt:
.. |alert-d| image:: https://raw.githubusercontent.com/belikh/design/latest/packages/github/graphics/icon/alert-dark.svg#gh-dark-mode-only
   :width: 20
   :alt:
