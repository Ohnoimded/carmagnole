import os
import sys

import pandas as pd
import numpy as np
import json
from logger import configure_logger

if len(sys.argv) > 1:
    choice = sys.argv[1]
else:
    choice = "frequent"

# configure logger
etlLogger = configure_logger("TRANSFORM", "./etl/logs/etl_log.log")


def dailyTransform():
    try:
        etlLogger.info(f"Begin daily data transform")
        with open("./etl/data/daily_extraction.json", "r") as f:
            data = json.load(f)

        data = data["articles"]
        selected_attr = [
            "url",
            "title",
            "urlToImage",
            "publishedAt",
            "author",
            "description",
        ]
        result = []
        for i, j in enumerate(data):
            temp = {}
            temp["name"] = j["source"]["name"]
            for k in j:
                if k in selected_attr:
                    temp[k] = j[k]
            result.append(temp)
        result = pd.DataFrame(result)
        result.rename(
            columns={
                "name": "source",
                "urlToImage": "imageurl",
                "author": "author",
                "publishedAt": "publishdate",
                "title": "headline",
            },
            inplace=True,
        )
        result.drop(result[result["source"] == "[Removed]"].index, inplace=True)
        result = result[
            [
                "url",
                "source",
                "author",
                "imageurl",
                "headline",
                "publishdate",
                "description",
            ]
        ]
        result.publishdate = pd.to_datetime(result.publishdate)
        result.replace(np.NaN, None)
        result.to_csv(
            "./data/daily_extraction_transformed.csv",
            index=False,
            mode="w",
        )

        etlLogger.info(
            f"Daily data transform successful. Rows: {result.shape[0]}, Columns: {result.shape[1]}"
        )
    except FileNotFoundError as e:
        etlLogger.error(f"Daily data transform failed: FileNotFoundError {e.__str__()}")
    except Exception as e:
        etlLogger.error(f"Daily data transform failed: {e.__str__()}")


def frequentTransform():
    transformed_stored_path = "./etl/data/frequent_extraction_transformed.csv"
    try:
        etlLogger.info(f"Begin frequent data transform")

        with open(f"./etl/data/frequent_extraction.json", "r") as f:
            data = json.load(f)

        data = data["response"]["results"]
        selected_attr = ["webUrl", "webPublicationDate", "sectionId"]
        selected_fields = [
            "headline",
            "shortUrl",
            "byline",
            "publication",
            "wordcount",
            "bodyText",
            "thumbnail",
        ]
        result = []

        for i, j in enumerate(data):
            temp = {}
            for k in j:
                if k in selected_attr:
                    temp[k] = j[k]
            for k in j["fields"]:
                if k in selected_fields:
                    temp[k] = j["fields"][k]
            result.append(temp)
        result = pd.DataFrame(result)

        if result.empty:
            columns = [
                "url",
                "shorturl",
                "source",
                "section",
                "author",
                "imageurl",
                "headline",
                "wordcount",
                "publishdate",
                "htmlbody",
            ]
            empty_result = pd.DataFrame(columns=columns)
            empty_result.to_csv(transformed_stored_path, index=False, mode="w")
            raise Exception("No new data to transform")

        result.rename(
            columns={
                "shortUrl": "shorturl",
                "webUrl": "url",
                "sectionId": "section",
                "publication": "source",
                "thumbnail": "imageurl",
                "byline": "author",
                "bodyText": "htmlbody",
                "webPublicationDate": "publishdate",
            },
            inplace=True,
        )
        result = result[
            [
                "url",
                "shorturl",
                "source",
                "section",
                "author",
                "imageurl",
                "headline",
                "wordcount",
                "publishdate",
                "htmlbody",
            ]
        ]

        if os.path.isfile(transformed_stored_path):
            etlLogger.info(
                f"Frequent data transform duplicate: Removing duplicates from saved file"
            )
            df = pd.read_csv(transformed_stored_path)
            if not df.empty:
                indices_to_remove = []

                for index, row in result.iterrows():
                    if row["url"] in df["url"].values:
                        indices_to_remove.append(index)

                result = result.drop(indices_to_remove)
            result.replace(np.NaN, None)
        result.to_csv(transformed_stored_path, index=False, mode="w")
        if not result.index.__len__():
            etlLogger.warning("No new data after checking for duplicates")

        etlLogger.info(
            f"Frequent data transform successful: Rows: {result.shape[0]}, Columns: {result.shape[1]}"
        )
    except FileNotFoundError as e:
        etlLogger.error(
            f"Frequent data transform failed: FileNotFoundError {e.__str__()}"
        )
    except Exception as e:
        etlLogger.error(f"Frequent data transform failed: {e.__str__()}")


if __name__ == "__main__":
    if choice == "daily":
        dailyTransform()
    else:
        frequentTransform()
