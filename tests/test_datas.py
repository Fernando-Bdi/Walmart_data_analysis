from Datas import Data
from tests.conftest import TESTS_DIR

# Use the test DB and data folder from the tests directory.
TEST_DATA = TESTS_DIR / "data"
TEST_DB = TESTS_DIR / "test_database.db"

def test_read_csv_files():

    d = Data()

    d.read_csv_files(
        str(TEST_DATA / "shipping_data_*.csv")
    )

    assert d.dfs is not None and len(d.dfs) == 3

def test_sql_clean():

    d = Data()

    d.read_csv_files(
        str(TEST_DATA / "shipping_data_*.csv")
    )

    d.load_raw_tables(str(TEST_DB))

    d.sql_to_df_clean()

    # Ensure dfs list exists and the last dataframe is not None or empty
    assert d.dfs and d.dfs[-1] is not None and len(d.dfs[-1]) > 0

def test_single_csv():

    d = Data()

    d.run_single_csv(
        str(TEST_DATA / "shipping_data_0.csv"),
        TEST_DB
    )


def test_multiple_csv():

    d = Data()

    d.run_multiple_csv(
        str(TEST_DATA / "shipping_data_*.csv"),
        TEST_DB
    )