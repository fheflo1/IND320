from pyspark.sql import SparkSession

# create a SparkSession named 'spark' for use when the module is run directly
spark = (
    SparkSession.builder.appName("CassandraConnectionTest")
    .config("spark.cassandra.connection.host", "127.0.0.1")
    .getOrCreate()
)


def test_cassandra_connection(spark, keyspace="elhub_data", table="production_raw"):
    """Check Spark–Cassandra connection and return row count."""
    try:
        df = (
            spark.read.format("org.apache.spark.sql.cassandra")
            .options(table=table, keyspace=keyspace)
            .load()
        )
        print(f"✅ Connection OK — found {df.count()} rows in {keyspace}.{table}")
    except Exception as e:
        print("❌ Connection failed:", e)


# Example:
test_cassandra_connection(spark)
