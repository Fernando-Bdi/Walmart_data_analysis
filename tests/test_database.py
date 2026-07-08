from database import get_connection

def test_connection():

    conn = get_connection()

    assert conn is not None
    conn.close()

def test_shipment_table():

    conn = get_connection()

    cursor = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='shipment'
    """)

    assert conn is not None
    assert cursor.fetchone() is not None

    conn.close()

def test_product_table():

    conn = get_connection()

    cursor = conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='product'
    """)

    assert conn is not None
    assert cursor.fetchone() is not None

    conn.close()