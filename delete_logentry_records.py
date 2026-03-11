"""
Delete LogEntry__c records older than a given CreatedDate cutoff.

Default query:
SELECT Id
FROM LogEntry__c
WHERE CreatedDate < 2026-03-02T13:29:43.394+05:30
ORDER BY CreatedDate
LIMIT 100000

Usage examples:
python delete_logentry_records.py
python delete_logentry_records.py --dry-run
"""

import argparse
import math
import sys
from datetime import datetime, timezone

import requests


class LogEntryCleaner:
    SESSION_ID = ""
    INSTANCE_URL = "https://trimbledx--tecq.sandbox.my.salesforce.com"
    API_VERSION = "v58.0"

    def __init__(self, session_id=None, instance_url=None, api_version=None):
        self.session_id = session_id or self.SESSION_ID
        self.instance_url = (instance_url or self.INSTANCE_URL).rstrip("/")
        self.api_version = api_version or self.API_VERSION
        self.headers = {
            "Authorization": f"Bearer {self.session_id}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def to_soql_datetime(dt_str):
        """
        Convert ISO datetime with optional timezone offset to Salesforce SOQL datetime literal in UTC.
        Example:
          2026-03-02T13:29:43.394+05:30 -> 2026-03-02T07:59:43.394Z
        """
        parsed = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        utc_dt = parsed.astimezone(timezone.utc)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    def query_ids(self, cutoff_dt, limit=100000):
        soql_dt = self.to_soql_datetime(cutoff_dt)
        soql = (
            f"SELECT Id FROM LogEntry__c "
            f"WHERE CreatedDate < {soql_dt} "
            f"ORDER BY CreatedDate "
        )

        url = f"{self.instance_url}/services/data/{self.api_version}/query"
        params = {"q": soql}

        all_ids = []

        while True:
            response = requests.get(url, headers=self.headers, params=params, timeout=60)
            if response.status_code != 200:
                raise RuntimeError(
                    f"Query failed ({response.status_code}): {response.text}"
                )

            payload = response.json()
            records = payload.get("records", [])
            all_ids.extend(record["Id"] for record in records if "Id" in record)

            if len(all_ids) >= limit:
                all_ids = all_ids[:limit]
                break

            next_records_url = payload.get("nextRecordsUrl")
            if not next_records_url:
                break

            url = f"{self.instance_url}{next_records_url}"
            params = None

        return all_ids

    def delete_ids(self, ids, chunk_size=200):
        """
        Delete in chunks using Salesforce composite sObjects delete endpoint (up to 200 IDs per call).
        """
        if not ids:
            return {"success": 0, "failed": 0, "total": 0}

        chunk_size = max(1, min(int(chunk_size), 200))
        total_chunks = int(math.ceil(len(ids) / chunk_size))

        success = 0
        failed = 0

        for idx in range(total_chunks):
            chunk = ids[idx * chunk_size : (idx + 1) * chunk_size]
            delete_url = f"{self.instance_url}/services/data/{self.api_version}/composite/sobjects"
            params = {
                "ids": ",".join(chunk),
                "allOrNone": "false",
            }

            response = requests.delete(
                delete_url, headers=self.headers, params=params, timeout=60
            )

            if response.status_code != 200:
                failed += len(chunk)
                print(
                    f"Chunk {idx + 1}/{total_chunks} failed ({response.status_code}): {response.text}"
                )
                continue

            results = response.json()
            for item in results:
                if item.get("success"):
                    success += 1
                else:
                    failed += 1

            print(f"Deleted chunk {idx + 1}/{total_chunks} ({len(chunk)} records)")

        return {"success": success, "failed": failed, "total": len(ids)}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Delete LogEntry__c records older than a CreatedDate cutoff"
    )
    parser.add_argument(
        "--before",
        default="2026-03-02T13:29:43.394+05:30",
        help="Delete records where CreatedDate is earlier than this ISO datetime",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100000,
        help="Maximum number of records to delete",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only query and print count, do not delete",
    )
    return parser


def main():
    args = build_parser().parse_args()

    cleaner = LogEntryCleaner()

    try:
        soql_dt = cleaner.to_soql_datetime(args.before)
        print(f"Instance URL: {cleaner.instance_url}")
        print(f"API Version: {cleaner.api_version}")
        print(f"Cutoff (input): {args.before}")
        print(f"Cutoff (SOQL UTC): {soql_dt}")
        print(f"Limit: {args.limit}")

        ids = cleaner.query_ids(cutoff_dt=args.before, limit=args.limit)
        print(f"Found {len(ids)} LogEntry__c records matching criteria")

        if args.dry_run:
            print("Dry run enabled; no records deleted")
            return

        result = cleaner.delete_ids(ids)
        print(
            f"Deletion complete. Success: {result['success']}, Failed: {result['failed']}, Total: {result['total']}"
        )
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
