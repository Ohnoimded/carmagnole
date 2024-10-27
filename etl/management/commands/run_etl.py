from django.core.management.base import BaseCommand
from etl.extract import ETLExtractor
from etl.transform import ETLTransformer
from etl.load import ETLLoader,FrequentDataLoader #, DailyDataLoader
from etl import logger
from datetime import datetime , timezone

etlLogger = logger.configure_logger("ETL", "/carmagnole/etl/logs/etl_log.log")

class Command(BaseCommand):
    help = 'Runs ETL process with default interval of "frequent"'

    def handle(self, *args, **kwargs):
        etl_interval = "frequent"  # Default interval is frequent
        etlLogger.info(f"Running Pipeline process for {etl_interval} interval")

        # if etl_interval == "daily":
        #     ETLExtractor.daily_extract()
        #     ETLTransformer.daily_transform()
        #     DailyDataLoader.daily_load()
        #     etlLogger.info(f"Successfully ran pipeline process for {etl_interval} interval")
        # else:
        
        
        ## Should have a retry system where each step is retried before givign up. THing for future me.
        ## Maybe keep the state of each step and then build from there instead of running the chain again? Again, for future me. 
        try:
            try:
                ETLExtractor.frequent_extract()
            except:
                raise Exception          
            try:
                ETLTransformer.frequent_transform()
            except:
                raise Exception
            try:
                FrequentDataLoader.frequent_load()
            except:
                raise Exception
            etlLogger.info(f"Successfully ran pipeline process for {etl_interval} interval")
        except:
            etlLogger.error(f"Failed to complete ETL pipeline process for {etl_interval} interval")

print(f"ETL cron ran at {datetime.now(timezone.utc)}")