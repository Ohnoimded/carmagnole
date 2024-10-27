
import os
import pandas as pd
import numpy as np
import json
from etl.logger import configure_logger
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import html
import re

from etl.news_groq import getNewsSummary

# Configure logger
etlLogger = configure_logger("TRANSFORM", "/carmagnole/etl/logs/etl_log.log")

load_dotenv()


class ETLTransformer:
    @classmethod
    def daily_transform(cls):
        try:
            etlLogger.info("Begin daily data transform")
            with open("/carmagnole/etl/data/daily_extraction.json", "r") as f:
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
            result.drop(result[result["source"] ==
                        "[Removed]"].index, inplace=True)
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
            result.replace(np.nan, None)
            result.to_csv(
                "/carmagnole/etl/data/daily_extraction_transformed.csv",
                index=False,
                mode="w",
            )

            etlLogger.info(
                f"Daily data transform successful. Rows: {result.shape[0]}, Columns: {result.shape[1]}"
            )
        except FileNotFoundError as e:
            etlLogger.error(
                f"Daily data transform failed: FileNotFoundError {e.__str__()}")
        except Exception as e:
            etlLogger.error(f"Daily data transform failed: {e.__str__()}")


# IGNORE THE ABOVE

    @classmethod
    def frequent_transform(cls):
        # should have appended instead of copying file paths.
        transformed_stored_path = "/carmagnole/etl/data/frequent_extraction_transformed.csv"
        try:
            etlLogger.info("Begin frequent data transform")

            with open("/carmagnole/etl/data/frequent_extraction.json", "r") as f:
                data = json.load(f)
            if not data:
                print(data)
                raise "No data to transform"
            data = data["response"]["results"]
            selected_attr = ["webUrl", "webPublicationDate", "sectionId"]
            selected_fields = [
                "headline",
                "shortUrl",
                "byline",
                "publication",
                "wordcount",
                "bodyText",
                "body",
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
                    "nohtmlbody",
                ]
                empty_result = pd.DataFrame(columns=columns)
                empty_result.to_csv(transformed_stored_path,
                                    index=False, mode="w")
                raise Exception("No new data to transform")

            result.rename(
                columns={
                    "shortUrl": "shorturl",
                    "webUrl": "url",
                    "sectionId": "section",
                    "publication": "source",
                    "thumbnail": "imageurl",
                    "byline": "author",
                    "body": "htmlbody",
                    "bodyText": "nohtmlbody",
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
                    "nohtmlbody",
                    "htmlbody",
                ]
            ]
            result['wordcount'] = pd.to_numeric(result['wordcount'])
            result = result.loc[result['wordcount'] > 150]

            unwanted_sections = ['commentisfree']
            result = result.loc[~result['section'].isin(unwanted_sections)]

            # Gotta extract only p tags and sanitize it. Javascri[t]: "Ooooo, I'm a snowflake"

            def process_html_content(txt):
                pattern = re.compile(r'<p> <span>Related: </span><a href')
                soup = BeautifulSoup(txt, 'html.parser')
                list_of_pees = soup.find_all('p',)
                out_pee = []

                for tag in soup.find_all('p'):
                    tag.attrs = {}
                    
                figures = soup.find_all('figure', class_='element element-tweet')
                if figures: 
                    for figure in figures:
                        figure.decompose()

                for pee in list_of_pees:
                    if not pattern.search(str(pee)):
                        content_length = len(pee.get_text(strip=True))
                        if content_length >= 25:
                            for tag in pee.find_all(['a', 'span']):
                                tag.unwrap()

                            # Look at this long shit!!!!!!!!!
                            pee = str(pee).replace('\xad', '').replace(r'[\x00-\x1F]', '').replace('\u00A0', ' ').replace('\u200E', '').replace('\u200F', '').replace('\u200B', '').replace('\uFFFD', '')
                            pee = re.sub(r'(<p>)(.*?)(</p>)',lambda m: m.group(1) + m.group(2).replace('"', '\u201C', 1).replace('"', '\u201D', 1) + m.group(3),pee).replace("'", '"').replace('\\', '\\\\')
                            # pee = pee.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
                            # sanitized_pee = json.dumps(pee)
                            sanitized_pee = html.escape(pee)
                            sanitized_pee = re.sub(
                                r'\s+', ' ', sanitized_pee).strip()

                            out_pee.append(sanitized_pee)

                return str(out_pee)

            result['htmlbody'] = result['htmlbody'].apply(process_html_content)

            result.fillna(value='', inplace=True)

            '''DONT USE THIS. MOVE GROQ STUFF TO DEPRECATED
            # result['htmlbody'] = result['htmlbody'].where(pd.isna(result['htmlbody']), result['htmlbody'].apply(getNewsSummary)) ## Dont use this
            # etlLogger.info("Frequent data transform htmlBody: Summary collected from Groq")
            '''

            if os.path.isfile(transformed_stored_path):
                etlLogger.info(
                    "Frequent data transform duplicate: Removing duplicates from saved file")
                df = pd.read_csv(transformed_stored_path)
                if not df.empty:
                    indices_to_remove = []

                    for index, row in result.iterrows():
                        if row["url"] in df["url"].values:
                            indices_to_remove.append(index)

                    result = result.drop(indices_to_remove)
                result.replace(np.nan, None)

            result.to_csv(transformed_stored_path,
                          na_rep='', index=False, mode="w")

            if not result.index.__len__():
                etlLogger.warning("No new data after checking for duplicates")
            if result.shape[0] != 0:
                etlLogger.info(
                    f"Frequent data transform successful: Rows: {result.shape[0]}, Columns: {result.shape[1]}")
        except FileNotFoundError as e:
            etlLogger.error(
                f"Frequent data transform failed: FileNotFoundError {e.__str__()}")
            raise e
        except Exception as e:
            etlLogger.error(f"Frequent data transform failed: {e.__str__()}")
            raise e
