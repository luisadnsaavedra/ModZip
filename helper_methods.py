import csv
import os
import shutil
import hashlib
import requests

DEFAULT_TIMEOUT = 7
IPAS_BY_HASH_FOLDER = "HASHED_IPAS/"
FOLDER_DEPTH = [3,2] # To achieve a structure HASHED_IPAS/123/ab/123ab........modzip based on the SHA256 hashes.


def download_to(url, folder, filename, timeout=DEFAULT_TIMEOUT):
    try:
        r = requests.get(url, allow_redirects=True, timeout=timeout)
        if r.status_code == 405:
            return r.status_code
        else:
            with open(os.path.join(folder, filename), 'wb') as f:
                f.write(r.content)
    except Exception as e:
        raise e
    
    return True


# get the SHA256 hash of a file
def get_hash256(filepath):
    sha256_hash = None
    with open(filepath,"rb") as f:
        bytes = f.read() # read entire file as bytes
        sha256_hash = hashlib.sha256(bytes).hexdigest();
    
    return sha256_hash


# Return subdirectory for IPA and other hashed files
def get_subdirectory(sha256_hash, ipas_folder=IPAS_BY_HASH_FOLDER, folder_depth=FOLDER_DEPTH):
    # # Old implementation
    # subdirectory = ipas_folder + '/'.join(sha256_hash[i:i+2] for i in range(0, 2*folder_depth, 2)) + '/'
    subdirectory = ipas_folder + sha256_hash[0:3] + '/' + sha256_hash[3:5] + '/'

    return subdirectory


# Create and delete folders
def create_folder(folder_path):
    try:
        os.makedirs(os.path.dirname(folder_path), exist_ok=True)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


def remove_folder(folder_path):
    try:
        shutil.rmtree(folder_path) 
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


# Store and read list of lists csv files:
def write_list_of_lists_to_csv(list_of_lists, csv_file):
    with open(csv_file, 'w') as f:
        writer = csv.writer(f)
        for row in list_of_lists:
            writer.writerow(row)

    return True


# Read CSV only taking the first item per row, i.e. a list file
def read_csv(csv_file):
    result = []
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        for i in reader:
            result.append(i)

    return result
