# Databricks notebook source
# Define the source directory containing CSV files
source_directory = "/mnt/simulation/unzippedfromdatabricks/"
# Define the output directory for split files
output_directory = "/mnt/simulation/files-48/"
# Use Databricks utilities to list files in the source directory
file_info = dbutils.fs.ls(source_directory)




# COMMAND ----------


# Iterate through all files in the source directory
for file in file_info:
    if file.path.endswith(".csv"):  # Check if the file is a CSV
        df = spark.read.csv(file.path, header=True)
        df.repartition(48).write.csv(output_directory, header=True)

print("All CSV files have been split and saved.")


