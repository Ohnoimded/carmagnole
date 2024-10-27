

import os
import json
from datetime import datetime, timedelta, timezone, UTC
from .paperboy import newsApiFetch, guardianApiFetch
from etl import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the logger for the 'Extraction' module
etlLogger = logger.configure_logger("EXTRACT", "/carmagnole/etl/logs/etl_log.log")


class ETLExtractor:
    @classmethod
    def daily_extract(cls, what_date: str = ""):
        """
        Daily pull. cron job has to handle the date if necessary.

        Args:
            what_date (str, optional): datetime variable to get news from the past x minutes, where x=what_date. Defaults to ''.
        """
        try:
            log_date = what_date if what_date else (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
            # etlLogger.info(f"ETL START: Begin extraction for day {log_date}")

            # Make API call
            daily_data = newsApiFetch().getTopHeadlines(sort_by="newest")
            if not daily_data:
                raise Exception("No data fetched from API")

            # Save to JSON
            dump_path = f"/carmagnole/etl/data/daily_extraction.json"
            with open(dump_path, "w") as f:
                json.dump(daily_data, f, indent=True)

            etlLogger.info(f"Daily extraction successful for {log_date}. Saved to {dump_path}")
        except Exception as e:
            etlLogger.error(f"Extraction failed: {e}")

    @classmethod
    def frequent_extract(cls, how_past_in_time: str = "45"):
        """
        We will be pulling data every given interval.
        The cron job should take care of it.

        Args:
            how_past_in_time (str): datetime variable to get news from the past x minutes, where x = how_past_in_time
        """
        try:
            how_past_in_time = timedelta(minutes=int(how_past_in_time))
            from_date = datetime.now(UTC) - how_past_in_time
            from_date = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            etlLogger.info(f"ETL START: Begin extraction for the last {how_past_in_time.seconds // 60} minutes")

            # Make the API call
            frequent_data = guardianApiFetch().searchContent(from_date=from_date)

            # Save the data to a JSON file
            dump_path = f"/carmagnole/etl/data/frequent_extraction.json"
            with open(dump_path, "w") as f:
                json.dump(frequent_data, f, indent=True)

            etlLogger.info(f"Extraction successful for {from_date}. Saved to {dump_path}")
        except Exception as e:
            etlLogger.error(f"Extraction failed: {e}")
            raise e

# Example usage
if __name__ == "__main__":
    extraction_interval = "frequent"  # or "daily"
    if extraction_interval == "daily":
        ETLExtractor.daily_extract()
    else:
        ETLExtractor.frequent_extract()
