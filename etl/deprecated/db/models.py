import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from sqlalchemy import MetaData, Table, Column, Integer, Text, DateTime, create_engine
from dotenv import load_dotenv


load_dotenv()
engine = create_engine(
    f'postgresql+psycopg2://{os.environ.get("POSTGRES_USERID")}:{os.environ.get("POSTGRES_PWD")}@localhost/{os.environ.get("POSTGRES_DB")}',
    echo=False
)


# CREATE TABLES IF EXISTS THINGY
metadata = MetaData()

daily_data = Table(
    "daily_data",
    metadata,
    Column("id", Integer, primary_key=True, unique=True, nullable=False, autoincrement=True),
    Column("url", Text, primary_key=True, unique=True, nullable=False),
    Column("source", Text),
    Column("author", Text),
    Column("imageurl", Text),
    Column("headline", Text),
    Column("publishdate", DateTime(timezone=True), nullable=False),
    Column("description", Text),
)

frequent_data = Table(
    "frequent_data",
    metadata,
    Column("id", Integer, primary_key=True, unique=True, nullable=False, autoincrement=True),
    Column("url", Text, primary_key=True, unique=True, nullable=False),
    Column("shorturl", Text, unique=True),
    Column("source", Text),
    Column("section", Text),
    Column("author", Text),
    Column("imageurl", Text),
    Column("headline", Text),
    Column("wordcount", Integer),
    Column("publishdate", DateTime(timezone=True), nullable=False),
    Column("htmlbody", Text),
)

metadata.create_all(engine, checkfirst=True)
