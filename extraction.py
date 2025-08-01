from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from utils import sanitize_filename, load_processed_list, append_processed_file
from datetime import datetime
from typing import List, Dict, Any
import json
from clients import XAIClient
from models import DodContractInfo, DOD_RSS


def extract_contract_awards_content(url: str) -> list[str]:
    """ Contract Announcements
    Extracts paragraphs from a dod contract announcement page.
    """
    output_dir = Path("dod_awards_json")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        content = page.content()
        browser.close()

    soup = BeautifulSoup(content, 'html.parser')
    body_div = soup.find("div", class_="body")
    if body_div is None:
        raise RuntimeError("Could not find <div class='body'> on the page")

    raw_title = soup.find("h1").get_text(strip=True)
    page_title = sanitize_filename(raw_title)
    date_month = page_title.split("_")[2]
    date_day = page_title.split("_")[3]
    date_year = page_title.split("_")[4]
    
    date_string = f"{date_month} {date_day}, {date_year}"
    contract_date = datetime.strptime(date_string, "%B %d, %Y")
    iso_date = contract_date.date().isoformat()
    # print(f"Contract Date: {contract_date}")

    out_path = output_dir / f"{page_title}.json"

    if out_path.exists():
        print(f"File {out_path} already exists, skipping extraction.")
    else:
        paragraphs_raw = [
            p.get_text(strip=True) for p in body_div.find_all("p") if p.get_text(strip=True) and not (p.get("style") and "text-align" in p.get("style", ""))
        ]

        paragraphs = [
            {
                "text": para, "contract_date": iso_date
            } for para in paragraphs_raw 
        ]

        # Write to JSON file
        with open(f"dod_awards_json/{page_title}.json", "w", encoding="utf-8") as f:
            json.dump(paragraphs, f, ensure_ascii=False, indent=2)

        print(f"Extracted {len(paragraphs)} paragraphs and saved to contracts.json")
        print(f"Page Title: {page_title}")


def sync_contract_announcements_feed_json():
    dod = DOD_RSS()
    entries = dod.get_contract_announcements_feed()

    for entry in entries['entries']:
        title = entry.get('title', 'No Title')
        link = entry.get('link', None)
        
        if link:
            print(f"Processing: {title} - {link}")
            extract_contract_awards_content(link)
        else:
            print(f"Skipping entry without link: {title}")


def contract_awards_to_master_json(out_path: str, filepath: str):
    """
    Load one day's extracted paragraph file, get structured award info, and merge into a master JSON file.
    """
    out_path = Path(out_path)
    filepath = Path(filepath)

    # Load input day's data
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Load existing master if present
    if out_path.exists():
        with open(out_path, "r", encoding="utf-8") as f:
            try:
                master_awards: List[Dict[str, Any]] = json.load(f)
            except json.JSONDecodeError:
                master_awards = []
    else:
        master_awards = []

    # Build a set of dedupe keys already present
    existing_keys = set()
    for a in master_awards:
        # key: contractor name(s) + contract_id(s) + contract_date
        contractors = a.get("contractors", [])
        if contractors:
            first = contractors[0]
            key = (
                first.get("name", "").strip().lower(),
                a.get("contract_date", ""),
            )
        else:
            key = (a.get("award_text", "").strip().lower(), a.get("contract_date", ""))
        existing_keys.add(key)

    new_awards = []
    for entry in data:
        text = entry.get("text", "").strip()
        if not text or text.lower().startswith("*small business"):
            continue  # skip noise

        # Get structured award
        xclient = XAIClient()
        award_details = xclient.get_structured_response(
            model="grok-3-mini",
            response_format=DodContractInfo,
            content=text,
        )
        record = award_details.model_dump() if hasattr(award_details, "model_dump") else award_details.dict()

        # Attach metadata
        contract_date = entry.get("contract_date")
        record["contract_date"] = contract_date
        record["award_text"] = text

        # Build the dedupe key
        contractors = record.get("contractors", [])
        if contractors:
            first = contractors[0]
            key = (
                first.get("name", "").strip().lower(),
                record["contract_date"],
            )
        else:
            key = (text.lower(), record["contract_date"])

        if key in existing_keys:
            # already have it
            continue
        existing_keys.add(key)
        new_awards.append(record)

    if not new_awards:
        print(f"No new awards to add from {filepath.name}")
    else:
        master_awards.extend(new_awards)
        # Write back to master
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(master_awards, f, ensure_ascii=False, indent=2)
        print(f"Appended {len(new_awards)} new award(s) from {filepath.name} to {out_path}")


def batch_process_awards_json(data_dir: Path, master_path: Path):
    manifest_path = data_dir / "processed_files.txt"
    processed = load_processed_list(manifest_path=manifest_path)

    for file in sorted(data_dir.iterdir()):
        if not file.is_file():
            continue
        if file.name in {master_path.name, manifest_path.name}:
            continue
        if file.suffix.lower() != ".json":
            continue
        if file.name in processed:
            print(f"Skipping already-processed file {file.name}")
            continue

        try:
            print(f"Processing {file.name}...")
            contract_awards_to_master_json(out_path=str(master_path), filepath=str(file))
            append_processed_file(manifest_path, file.name)
        except Exception as e:
            print(f"Failed to process {file.name}: {e}")


