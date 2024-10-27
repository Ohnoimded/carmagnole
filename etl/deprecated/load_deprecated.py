import os
import sys
from sqlalchemy import MetaData, create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pytz
from dotenv import load_dotenv
from logger import configure_logger


load_dotenv()


if len(sys.argv) > 1:
    which_data = sys.argv[1]
else:
    which_data = "frequent"

etlLogger = configure_logger("LOAD", "./etl/logs/etl_log.log")

engine = create_engine(
    f'postgresql+psycopg2://{os.environ.get("POSTGRES_USERID")}:{os.environ.get("POSTGRES_PWD")}@localhost/{os.environ.get("POSTGRES_DB")}',
    echo=False)

metadata = MetaData()
metadata.reflect(engine)

daily_data = metadata.tables["daily_data"]
frequent_data = metadata.tables["frequent_data"]


def loadToDb(which_data: str):
    etlLogger.info(f"Begin loading for {which_data}_data")
    try:
        data = pd.read_csv(f"./etl/data/{which_data}_extraction_transformed.csv", parse_dates=['publishdate'])
        if data.empty:
            raise Exception("No data to load")
        data = pd.read_csv(f"./etl/data/{which_data}_extraction_transformed.csv", parse_dates=['publishdate']).to_dict(
            orient="records"
        )
        Session = sessionmaker(bind=engine)
        session = Session()

        if which_data == "frequent":
            for row in data:
                row['publishdate'] = row['publishdate'].astimezone(pytz.utc)
                statement = insert(frequent_data).values(**row)
                statement = statement.on_conflict_do_update(
                    constraint="frequent_data_pkey",
                    set_={
                        frequent_data.c.url: row["url"],
                        frequent_data.c.shorturl: row["shorturl"],
                        frequent_data.c.source: row["source"],
                        frequent_data.c.section: row["section"],
                        frequent_data.c.author: row["author"],
                        frequent_data.c.imageurl: row["imageurl"],
                        frequent_data.c.headline: row["headline"],
                        frequent_data.c.wordcount: row["wordcount"],
                        frequent_data.c.publishdate: row["publishdate"],
                        frequent_data.c.htmlbody: row["htmlbody"],
                    },
                )

                session.execute(statement)
                session.commit()

        else:
            for row in data:
                row['publishdate'] = row['publishdate'].astimezone(pytz.utc)
                statement = insert(daily_data).values(**row)
                statement = statement.on_conflict_do_update(
                    constraint="daily_data_pkey",
                    set_={
                        daily_data.c.url: row["url"],
                        daily_data.c.source: row["source"],
                        daily_data.c.author: row["author"],
                        daily_data.c.imageurl: row["imageurl"],
                        daily_data.c.headline: row["headline"],
                        daily_data.c.publishdate: row["publishdate"],
                        daily_data.c.description: row["description"],
                    },
                )
                session.execute(statement)
                session.commit()
        session.close()
        etlLogger.info(f"ETL END: Successful loading for {which_data}_data")
    except Exception as e:
        etlLogger.error(f"Data load failed: {e.__str__()}")


if __name__ == "__main__":
    if which_data in ["frequent", "daily"]:
        loadToDb(which_data)
