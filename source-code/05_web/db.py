import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


@st.cache_resource
def get_database():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("MONGO_DB", "ecommerce_db")

    if not uri:
        raise RuntimeError("Chưa khai báo MONGO_URI trong file .env")

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")
    return client[db_name]


def get_collection(name):
    return get_database()[name]


@st.cache_data(ttl=300)
def load_products():
    collection = get_collection("products_cleaned")
    records = list(collection.find({}, {"_id": 0}))
    return pd.DataFrame(records)


def clear_data_cache():
    load_products.clear()

