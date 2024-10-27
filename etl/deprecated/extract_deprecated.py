import sys
import os

import json
from paperboy import newsApiFetch, guardianApiFetch
import logger
from datetime import datetime, timedelta, timezone

# Extract command-line arguments

if len(sys.argv) > 1:
    extraction_interval = sys.argv[1]
else:
    extraction_interval = "frequent"

# Configure the logger for the 'Extraction' module
etlLogger = logger.configure_logger("EXTRACT", "./etl/logs/etl_log.log")


############################
### EXTRACTION FUNCTIONS ###
############################


def dailyExtract(whatDate: str = ""):
    """
    Daily pull. cron job has to handle the date if necessary.

    Args:
        whatDate (str, optional): datetime variable to get news from the past x minutes, where x=whatDate. Defaults to ''.

    """
    try:
        if whatDate:
            log_date = whatDate
        else:
            log_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        etlLogger.info(f"ETL START: Begin extraction for day {log_date}")

        # make api call
        daily_data = newsApiFetch().getTopHeadlines(sort_by="newest")
        if not daily_data:
            raise Exception
        # save to json
        dump_path = f"./etl/data/daily_extraction.json"
        with open(dump_path, "w") as f:
            json.dump(daily_data, f, indent=True)
        etlLogger.info(
            f"Daily extraction successful for {log_date}. Saved to {dump_path}"
        )
    except Exception:
        etlLogger.error(f"Extraction failed")


def freqExtract(howPastInTime: str = "600"):
    """

    We will be pulling data every
    The cron job should take care of it.

    Args:
        howPastInTime (str): datetime variable to get news from the past x minutes, where x = howPastInTime
    """
    try:
        howPastInTime = timedelta(minutes=int(howPastInTime))
        log_date = (datetime.now(timezone.utc) - howPastInTime).strftime("%Y-%m-%d-%H-%M-%S")
        etlLogger.info(
            f"ETL START: Begin extraction for every {howPastInTime.seconds//60} minutes"
        )

        # Make the API call
        frequent_data = guardianApiFetch().searchContent(
            from_date=datetime.strptime(log_date, "%Y-%m-%d-%H-%M-%S").isoformat()
        )

        # Save the data to a JSON file
        # dump_path = f'./data/frequent/{howPastInTime.seconds//60}_frequent_extraction.json'
        dump_path = f"./etl/data/frequent_extraction.json"
        with open(dump_path, "w") as f:
            json.dump(frequent_data, f, indent=True)

        etlLogger.info(f"Extraction successful for {log_date}. Saved to {dump_path}")
    except Exception as e:
        etlLogger.error(f"{e}")


if __name__ == "__main__":
    if extraction_interval == "daily":
        dailyExtract()
    else:
        freqExtract()
