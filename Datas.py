import glob
import sqlite3
import pandas as pd
from pathlib import Path

from config import (
    DATABASE,
    DATA_FOLDER
)


class Data:
    """
    Loads shipping_data_0/1/2.csv into the shipment_database.db SQLite database.

    Spreadsheet 0 is self-contained (one row per shipment).
    Spreadsheets 1 and 2 are split: 1 has one row per product per shipment
    (so quantity = number of rows per shipment+product), 2 has the
    origin/destination per shipment. They're joined on shipment_identifier.
    """

    def __init__(self):
        self._conn = None
        self._cursor = None
        self._csv_path = None
        self._db_path = None
        self._dfs = None

    @property
    def db_path(self):
        return self._db_path

    @db_path.setter
    def db_path(self, db_path):
        self._db_path = db_path

    @property
    def csv_path(self):
        return self._csv_path

    @csv_path.setter
    def csv_path(self, csv_path):
        self._csv_path = csv_path

    @property
    def conn(self):
        return self._conn

    @conn.setter
    def conn(self, db_path):
        if db_path is None:
            db_path = self.db_path
        if db_path is not None:
            self._conn = sqlite3.connect(db_path)

    @property
    def dfs(self):
        return self._dfs

    def read_csv_files(self, csv_path):
        """Read every csv matching csv_path into a list of DataFrames, in
        filename order (0, 1, 2...) rather than whatever order glob happens
        to return."""

        self.csv_path = csv_path

        f_list = sorted(glob.glob(self.csv_path))

        if not f_list:
            raise FileNotFoundError(
                "No CSV files found."
            )

        dfs = []
        for f in f_list:
            df = pd.read_csv(f)
            df["source_file"] = Path(f).name
            dfs.append(df)
        self._dfs = dfs

    def load_raw_tables(self, db_path):
        """Stage spreadsheets 1 and 2 as raw tables so we can join them with SQL. 
        Basically, it's a csv-to-db function"""

        self.db_path = db_path

        # Ensure CSVs have been read
        if not self._dfs or len(self._dfs) < 3:
            raise RuntimeError("Expected at least 3 CSV files to be loaded before staging raw tables.")

        # Open DB connection (setter will use self.db_path when passed None)
        self.conn = None
        try:
            # use the internal _dfs directly to avoid false-positive type
            # checkers that think the property might be None
            self._dfs[1].to_sql("product_shipments", self.conn, if_exists="replace", index=False)
            self._dfs[2].to_sql("origin_dest", self.conn, if_exists="replace", index=False)
        except Exception:
            # re-raise to surface the original exception
            raise

    def sql_to_df_clean(self):
        """
        Combine spreadsheets 1 + 2 into one shipment-level dataframe:
        one row per (shipment, product), with quantity = row count,
        plus the origin/destination pulled in from spreadsheet 2.

        Grouping is done on shipment_identifier + product (not on
        origin/destination) so that two different shipments that happen
        to share a route never get merged together.
        """
        # Ensure dataframes and DB connection are available
        if not self._dfs or len(self._dfs) < 3:
            raise RuntimeError("Expected raw tables and spreadsheet 0 \
                               to be loaded before cleaning SQL to DF.")
        query = """
            SELECT
                p.shipment_identifier,
                p.product,
                o.origin_warehouse,
                o.destination_store,
                count(*) as product_quantity
            FROM product_shipments AS p
            JOIN origin_dest AS o
                ON p.shipment_identifier = o.shipment_identifier
            GROUP BY
                p.shipment_identifier,
                p.product
        """
        df_new = pd.read_sql(query, self.conn)
        df_new = df_new.rename(columns={
            "origin_warehouse": "origin",
            "destination_store": "destination",
            "product_quantity": "quantity"
        })

        # Spreadsheet 0 uses different column names for the same concepts;
        # align it to the same shape (origin, destination, product, quantity)
        # before concatenating. on_time / driver_identifier aren't part of the
        # shipment table schema, so they're dropped rather than carried through.
        df_0 = self._dfs[0].rename(columns={
            "origin_warehouse": "origin",
            "destination_store": "destination",
            "product_quantity": "quantity",
        })[["origin", "destination", "product", "quantity"]]

        df_new = df_new[["origin", "destination", "product", "quantity"]]

        df_combined = pd.concat([df_0, df_new], ignore_index=True)
        self._dfs.append(df_combined)

    def df_to_sql(self):
        """
        Insert any new product names into the `product` table (without
        duplicating ones that already exist), then insert every shipment
        row into 'shipment', mapping product -> the real product_id
        assigned by the database rather than an id invented locally.
        """
        # Ensure cleaned dataframe is available
        if not self._dfs or len(self._dfs) < 1:
            raise RuntimeError("No combined dataframe available to write to SQL.")

        # Ensure DB connection is established (uses self.db_path if needed)
        if self._conn is None:
            self.conn = None

        df_combined = self._dfs[-1]

        # 1. Make sure every product name in our data exists in `product`.
        existing_products = pd.read_sql("SELECT id, name FROM product", self.conn)
        existing_names = set(existing_products["name"])

        new_names = [p for p in df_combined["product"].unique() if p not in existing_names]
        if new_names:
            pd.DataFrame({"name": new_names}).to_sql(
                "product", self.conn, if_exists="append", index=False
            )

        # 2. Re-read the product table so we map onto the ids SQLite actually
        # assigned (don't invent our own ids).
        product_lookup = pd.read_sql("SELECT id, name FROM product", self.conn)
        name_to_id = dict(zip(product_lookup["name"], product_lookup["id"]))

        df_combined = df_combined.copy()
        df_combined["product_id"] = df_combined["product"].map(name_to_id)

        # 3. Insert shipment rows. Don't supply `id` - let it autoincrement.
        df_db = df_combined[["product_id", "quantity", "origin", "destination"]]
        df_db.to_sql("shipment", self.conn, if_exists="append", index=False)

        if self.conn is not None:
            self.conn.commit()

    def run(self, csv_glob_path, db_path):
        path = Path(csv_glob_path)

        if "*" in str(path):
            self.run_multiple_csv(csv_glob_path, db_path)
        else:
            self.run_single_csv(csv_glob_path, db_path)

    def run_multiple_csv(self, csv_glob_path, db_path):
        self.read_csv_files(csv_glob_path)
        self.load_raw_tables(db_path)
        self.sql_to_df_clean()
        self.df_to_sql()
        if self.conn is not None:
            self.conn.close()
        
    def run_single_csv(self, csv_glob_path, db_path):
        df= pd.read_csv(csv_glob_path)
        target_cols= ["origin_warehouse", "destination_store", "product", "product_quantity"]
        if all([True if i in df.columns else False for i in target_cols]):
                df= df[target_cols]
                df= df.rename(columns={"origin_warehouse": "origin",
                    "destination_store": "destination",
                    "product_quantity": "quantity",})
                
                self.db_path= db_path
                self.conn= None

                existing_products = pd.read_sql("SELECT id, name FROM product", self.conn)
                existing_names = set(existing_products["name"])
        
                new_names = [p for p in df["product"].unique() if p not in existing_names]
                if new_names:
                    pd.DataFrame({"name": new_names}).to_sql(
                        "product", self.conn, if_exists="append", index=False
                    )
                
                product_lookup = pd.read_sql("SELECT id, name FROM product", self.conn)
                name_to_id = dict(zip(product_lookup["name"], product_lookup["id"]))
        
                df["product_id"] = df["product"].map(name_to_id)
                df= df[[
                    "product_id", "quantity", "origin", "destination"
                    ]]
                
                df.to_sql("shipment", self.conn, if_exists="append", index= False)
                
                if self.conn is not None:
                    try:
                        self.conn.commit()
                    finally:
                        self.conn.close()
        else:
                print("CSV does not contain the required columns.")        

if __name__ == "__main__":
    d = Data()
    d.run(
        str(DATA_FOLDER / "shipping_data_*.csv"),
        str(DATABASE)
    )
    print("Done!!!")