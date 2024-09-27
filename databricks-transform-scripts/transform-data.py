# Databricks notebook source
# Databricks notebook source

# Define your storage account details 
storage_account_name = "storageforcapstone"  # Your Azure Storage account name
container_name = "bronze"  # Your container name
storage_account_key = "D2HcwRbF+p2kZ9wEeLYkVrhdLK4JpZPhrMFpu6gpBeGDnQzxwweYr5mbXEBHjJmvqU+6/9WZqzR5+AStVtKrlw=="  # Replace this with your actual key

# Check if the storage is already mounted
mount_point = f"/mnt/{container_name}"
if not any(mount.mountPoint == mount_point for mount in dbutils.fs.mounts()):
    # Mount the Azure Storage using the account key
    dbutils.fs.mount(
        source = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net/",
        mount_point = mount_point,
        extra_configs = {f"fs.azure.account.key.{storage_account_name}.blob.core.windows.net": storage_account_key}
    )
    print(f"Mounted {container_name} successfully.")
else:
    print(f"{container_name} is already mounted.")

# Verify that the storage is mounted
display(dbutils.fs.ls(mount_point))

# COMMAND ----------

# Databricks notebook source

# Define your storage account details 
storage_account_name = "storageforcapstone"  # Your Azure Storage account name
container_name = "silver"  # Your container name
storage_account_key = "D2HcwRbF+p2kZ9wEeLYkVrhdLK4JpZPhrMFpu6gpBeGDnQzxwweYr5mbXEBHjJmvqU+6/9WZqzR5+AStVtKrlw=="  # Replace this with your actual key

# Check if the storage is already mounted
mount_point = f"/mnt/{container_name}"
if not any(mount.mountPoint == mount_point for mount in dbutils.fs.mounts()):
    # Mount the Azure Storage using the account key
    dbutils.fs.mount(
        source = f"wasbs://{container_name}@{storage_account_name}.blob.core.windows.net/",
        mount_point = mount_point,
        extra_configs = {f"fs.azure.account.key.{storage_account_name}.blob.core.windows.net": storage_account_key}
    )
    print(f"Mounted {container_name} successfully.")
else:
    print(f"{container_name} is already mounted.")

# Verify that the storage is mounted


# COMMAND ----------

# Configuration to avoid extra files (_SUCCESS, _started, _committed)
spark.conf.set("mapreduce.fileoutputcommitter.marksuccessfuljobs", "false")
spark.conf.set("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
spark.conf.set("spark.hadoop.mapreduce.fileoutputcommitter.cleanup-failures.ignored", "true")
spark.conf.set("spark.sql.sources.commitProtocolClass", "org.apache.spark.sql.execution.datasources.SQLHadoopMapReduceCommitProtocol")
spark.conf.set("spark.sql.parquet.output.committer.class", "org.apache.spark.sql.execution.datasources.SQLHadoopMapReduceCommitProtocol")
spark.conf.set("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2")
spark.conf.set("spark.hadoop.fs.azure.committer.delete-on-success", "true")
spark.conf.set("spark.hadoop.fs.azure.committer.delete-temporary-files", "true")



# COMMAND ----------

import os
source_directory="/mnt/bronze/raw_data/"
destination_directory="/mnt/silver/intermidiate/"
failed_files="/mnt/bronze/failed_files"
archived_files="/mnt/bronze/archived"

if not os.path.exists(destination_directory):
    os.makedirs(destination_directory)
if not os.path.exists(failed_files):
    os.makedirs(failed_files)
if not os.path.exists(archived_files):
    os.makedirs(archived_files)

# COMMAND ----------

file_info = dbutils.fs.ls(source_directory)

# COMMAND ----------

file_info

# COMMAND ----------

from pyspark.sql import DataFrame
file_info = dbutils.fs.ls(source_directory)

# Initialize an empty DataFrame
combined_df = None
df=None

for file in file_info:

    if file.path.endswith(".csv"):  # Check if the file is a CSV
        try:
            # Read the CSV file
            df = spark.read.csv(file.path, header=True)
            
            # If combined_df is empty, assign the current DataFrame to it
            if combined_df is None:
                combined_df = df
            else:
                # Union the current DataFrame with the combined DataFrame
                combined_df = combined_df.unionAll(df)
        
        except Exception as e:
            # If processing fails, move the file to failed_files
            dbutils.fs.mv(file.path, failed_files + "/" + file.name)
            print(f"Failed to process: {file.name}. Error: {str(e)}")


    

df=combined_df

# COMMAND ----------

df.show(5)

# COMMAND ----------

from pyspark.sql.functions import from_utc_timestamp, min as min_col
# Convert the event_time column from UTC to IST (Indian Standard Time)
df = df.withColumn("event_time_IST", from_utc_timestamp("event_time", "Asia/Kolkata"))
df = df.drop("event_time")
df = df.withColumnRenamed("event_time_IST", "event_time")

# COMMAND ----------

df.show(5)

# COMMAND ----------

# Select category-related columns and drop duplicates
categories = df.select("category_id", "category_code").dropDuplicates()

# Fill missing values in category_code with 'UnknownCategory'
categories = categories.fillna({"category_code": "UnknownCategory"})

# Show the resulting DataFrames
print("Categories DataFrame:")
categories.show()

# COMMAND ----------

# Select product-related columns and drop duplicates
products = df.select("product_id", "brand").dropDuplicates()

# Fill missing values in brand with 'UnknownBrand'
products = products.fillna({"brand": "UnknownBrand"})

print("Products DataFrame:")
products.show()

# COMMAND ----------

users = df.groupBy("user_id").agg(min_col("event_time").alias("first_transaction_time"))

# Show the resulting DataFrame with first transaction time
print("Users DataFrame with first transaction time:")
users.show()

# COMMAND ----------

# Drop the columns category_code and brand
df = df.drop("category_code", "brand")

# COMMAND ----------

categories.write.mode("append").option("header", "true").csv(f"/mnt/silver/intermidiate/categories/")
products.write.mode("append").option("header", "true").csv(f"/mnt/silver/intermidiate/products/")
users.write.mode("append").option("header", "true").csv(f"/mnt/silver/intermidiate/users/")
df.write.mode("append").option("header", "true").csv(f"/mnt/silver/intermidiate/events/")

# COMMAND ----------

dbutils.fs.ls("/mnt/silver/intermidiate/")

# COMMAND ----------

# If everything is successful, delete all processed files from the source
# Archive the successfully processed file
            
for file in file_info:
    dbutils.fs.mv(file.path, archived_files + "/" + file.name)
    print(f"Archived: {file.name}")
    dbutils.fs.rm(file.path, True)
    print(f"Deleted: {file.name}")
