from pathlib import Path
from extraction import sync_contract_announcements_feed_json, batch_process_awards_json


def main():
    data_dir = Path("dod_awards_json")
    master_path = data_dir / "dod_awards_master.json"

    sync_contract_announcements_feed_json()
    batch_process_awards_json(data_dir=data_dir, master_path=master_path)


if __name__ == "__main__":
    main()
