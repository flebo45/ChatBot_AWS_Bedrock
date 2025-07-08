import json
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
import pandas as pd
import os

args = {}
args["name"] = "amazon.titan-embed-text-v2:0"
args["region"] = "eu-central-1"

script_path = os.path.dirname(os.path.abspath(__file__))

model = get_registry().get("bedrock-text").create(**args)
table_name = "test"

chunks = []
source_dir = f"{script_path}\source_documents"
# print(source_dir)
for file in os.listdir(source_dir):
    with open(os.path.join(source_dir, file), "r", encoding="utf-8") as f:
        text = f.read()
        # print(text)
        chunks.append({"text": text})

class TextModel(LanceModel):
    text: str = model.SourceField()
    vector: Vector(model.ndims()) = model.VectorField()

db = lancedb.connect(f"{script_path}/tables")
db_tables= db.table_names()
if table_name not in db_tables:
    print(f"Creating table {table_name}...")
    tbl = db.create_table(table_name, schema=TextModel, mode="overwrite")
    tbl.add(chunks)
else:
    print(f"Table {table_name} already exists, using existing table...")
    tbl = db.open_table(table_name)

rs = tbl.search("Hi, i would to buy an vacuum cleaner, could you give me some advises?").limit(5)
print(rs.to_pydantic(TextModel))
print(rs.to_pandas())
