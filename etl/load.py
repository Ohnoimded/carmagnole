import os
import sys
import pandas as pd
from dotenv import load_dotenv
from django.utils import timezone
from utils.models import DailyData, FrequentData
from etl.logger import configure_logger
import asyncio 

# Load environment variables
load_dotenv()
class ETLLoader:
    @classmethod
    def  load_data(cls, data_file, model_class):
        etl_logger = configure_logger("LOAD", "/carmagnole/etl/logs/etl_log.log")
        data_dir = os.path.dirname(data_file)
        os.makedirs(data_dir, exist_ok=True)
        # print(os.path.abspath( data_file))
        data = pd.read_csv(data_file,na_filter=True, parse_dates=['publishdate'])

        if data.empty:
            raise Exception(f"No data found in {data_file}")

        try:
            for index, row in data.iterrows():
                model_class.objects.update_or_create(
                    url=row["url"],
                    defaults={
                        "shorturl": row.get("shorturl"),
                        "source": row.get("source"),
                        "section": row.get("section"),
                        "author": row.get("author") or None,
                        "imageurl": row.get("imageurl") or None,
                        "headline": row.get("headline"),
                        "wordcount": row.get("wordcount"),
                        "publishdate": row["publishdate"],
                        "nohtmlbody": row.get("nohtmlbody") or None, 
                        "htmlbody": row.get("htmlbody") or None, # This should go to a new table that maps article id from frequent data with nohtmlbody
                        # "description": row.get("description"),  # For DailyData
                    }
                )
            etl_logger.info(f"ETL END: Successful loading for {model_class.__name__}")
        except Exception as e:
            etl_logger.error(f"Data load failed: {e}")
            raise e

class FrequentDataLoader(ETLLoader):
    @classmethod
    def frequent_load(cls):
        super().load_data("/carmagnole/etl/data/frequent_extraction_transformed.csv", FrequentData)

# class DailyDataLoader(ETLLoader):
#     @classmethod
#     def daily_load(cls):
#         super().load_data("./etl/data/daily_extraction_transformed.csv", DailyData)

 