import pandas as pd
import sqlite3
import glob
import os

conn = sqlite3.connect("repeaters.db")

files = glob.glob("data/**/*.csv", recursive=True)

for file in files:
    print("Importing:", file)

    df = pd.read_csv(file)

    folder = os.path.basename(os.path.dirname(file))
    name = os.path.basename(file).replace(".csv", "")

    table = f"{folder}_{name}".replace("-", "_")

    df.to_sql(table, conn, if_exists="replace", index=False)

conn.close()

print("DONE")