# Databricks notebook source

# Define your storage account details 
storage_account_name = "storageforcapstone"  # Your Azure Storage account name
container_name = "simulation"  # Your container name
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

import zipfile
import os
import shutil

# Define the source directory and zip file
source_directory = "/dbfs/mnt/simulation/zippedfile/"
# Define the destination directory where unzipped files will be saved
destination_directory = "/dbfs/mnt/simulation/unzippedfromdatabricks"

if not os.path.exists(destination_directory):
    os.makedirs(destination_directory)

for file_name in os.listdir(source_directory):
    zip_file_path = os.path.join(source_directory, file_name)
    
    # Unzipping the file
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            member_path = os.path.join(destination_directory, member.filename)
            with zip_ref.open(member) as source, open(member_path, 'wb') as target:
                shutil.copyfileobj(source, target, length=1024*1024)  # 1MB buffer
    print(f"Unzipped '{file_name}' to '{destination_directory}'")

print("All zip files have been unzipped.")