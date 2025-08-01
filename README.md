# DoD Contract Awards Scraper & Parser (with grok-3-mini)

A Python-based pipeline to collect, parse, and structure U.S. Department of Defense (DoD) contract award announcements for use as model context or training data.

This project automates the extraction of contract award data from the DoD RSS feed, structures it into JSON, and optionally deduplicates and aggregates it into a master dataset for future use in AI workflows.

---

## Features

* **RSS Feed Parsing**

  * Pulls entries from the official DoD Contract Announcements RSS feed.
  * Extracts URLs to the detailed award announcements.

* **Automated Web Scraping**

  * Uses [Playwright](https://playwright.dev/python/) to scrape the linked DoD contract announcement pages.
  * Uses Beautiful Soup 4 ([bs4](https://beautiful-soup-4.readthedocs.io/en/latest/)) for parsing.
  * Extracts `<p>` tags from the `<body>` section, treating each paragraph as an individual announcement.

* **Structured Contract Data Extraction**

  * Extracted paragraphs are passed to **Grok-3-mini** via the OpenAI Python SDK.
  * Outputs structured data using Pydantic models:

    ```python
    class Entity(BaseModel):
        name: str
        contract_id: str
        location: str

    class ContractingAgency(BaseModel):
        name: str
        location: str

    class DodContractInfo(BaseModel):
        """
        Pydantic model to extract contract details from text
        scraped from DoD awards/contracts pages.
        """
        contractors: list[Entity]
        purpose: str
        amount: float
        contracting_agency: ContractingAgency
    ```

* **Data Storage & Aggregation**

  * Contract dates are the date of announcement.
  * Raw announcements stored as JSON in `dod_awards_json/`.
  * Structured outputs aggregated into `dod_awards_master.json`.
  * Tracks processed files in `processed_files.txt` to prevent duplicate processing.

---

## How It Works

1. **Fetch RSS Feed** – Pull the DoD contract announcements RSS feed.
2. **Scrape Details** – For each entry, scrape the page and extract paragraph text.
3. **Process Contracts** – Send text to Grok-3-mini to extract structured contract info.
4. **Save Results** – Store results in JSON and append to a master dataset.
5. **Dedupe Checks** – Avoid reprocessing old files via `processed_files.txt` and records key gens.

---

## Setup (with Astral UV)

1. **Install [UV](https://docs.astral.sh/uv/)**

   If you don’t already have UV:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Or with pipx:

   ```bash
   pipx install uv
   ```

2. **Create & Sync the Environment**

   ```bash
   uv init
   uv add playwright openai pydantic feedparser bs4 python-dotenv
   uv sync
   ```

   This will create a `.venv` automatically and pin dependencies in `uv.lock`.

3. **Install Playwright Browsers**

   ```bash
   source .venv/bin/activate
   playwright install
   ```

4. **Set Environment Variables**
   I use .env with python-dotenv to load variables

   ```bash
   export XAI_API_KEY="your_api_key_here"
   ```

5. **Run the Script**

   ```bash
   uv run main.py
   ```

---

## Example Output

**`dod_awards_master.json` entry:**

```json
[
  {
    "contractors": [
      {
        "name": "F.K. Horn GmbH & Co.KG",
        "contract_id": "FA5613-25-D-0003",
        "location": "Kaiserslautern, Germany"
      },
      {
        "name": "SKE Support Services GmbH",
        "contract_id": "FA5613-25-D-0004",
        "location": "Goldbach, Germany"
      },
      {
        "name": "Wayss & Freytag Ingenieurbau AG",
        "contract_id": "FA5613-25-D-0005",
        "location": "Frankfurt Am Main, Germany"
      },
      {
        "name": "J&J Maintenance Inc., doing business as J&J Worldwide Services",
        "contract_id": "FA5613-25-D-0006",
        "location": "Mclean, Virginia"
      },
      {
        "name": "Wolff & Müller Government Services GmbH & Co. KG",
        "contract_id": "FA5613-25-D-0007",
        "location": "Stuttgart, Germany"
      },
      {
        "name": "MICKAN Generalbaugesellschaft Amberg mbH& Co.KG",
        "contract_id": "FA5613-25-D-0008",
        "location": "Amberg, Germany"
      },
      {
        "name": "PORR Government Services GmbH",
        "contract_id": "FA5613-25-D-0009",
        "location": "Kaiserslautern, Germany"
      }
    ],
    "purpose": "Indefinite-delivery/indefinite-quantity, multiple-award construction contract for construction services, including sustainment, maintenance, repair, alteration, renovation, and minor construction projects for residential and commercial work in the Kaiserslautern military community and Spangdahlem Air Base areas.",
    "amount": 950000000.0,
    "contracting_agency": {
      "name": "700th Contracting Squadron",
      "location": "Kapaun Air Station, Germany"
    },
    "contract_date": "2025-07-22",
    "award_text": "F.K. Horn GmbH & Co.KG, Kaiserslautern, Germany (FA5613-25-D-0003); SKE Support Services GmbH, Goldbach, Germany (FA5613-25-D-0004); Wayss & Freytag Ingenieurbau AG, Frankfurt Am Main, Germany (FA5613-25-D-0005); J&J Maintenance Inc., doing business as J&J Worldwide Services, Mclean, Virginia (FA5613-25-D-0006); Wolff & Müller Government Services GmbH & Co. KG, Stuttgart, Germany (FA5613-25-D-0007); MICKAN Generalbaugesellschaft Amberg mbH& Co.KG, Amberg, Germany (FA5613-25-D-0008); and PORR Government Services GmbH, Kaiserslautern, Germany (FA5613-25-D-0009), were awarded a combined ceiling of $950,000,000 indefinite-delivery/indefinite-quantity, multiple-award construction contract for construction services. This contract provides for a streamlined execution method for a broad range of sustainment, maintenance, repair, alteration, renovation, and minor construction projects to include residential and commercial work for the Kaiserslautern military community and Spangdahlem Air Base areas. Work will be performed within the Federal Republic of Germany and is expected to be completed by July 21, 2034, if all options are exercised. These contracts were competitive acquisitions and seven offers were received. Fiscal 2025 operations and maintenance funds in the amount of $22,705 ($3,244 per awardee) are being obligated at time of award. The 700th Contracting Squadron, Kapaun Air Station, Germany, is the contracting activity."
  },
]
```


