import os
import shutil
from zipfile import *
import hashlib
#Helper methods for getting the subdirectories
import helper_methods as helper


# get the SHA256 hash of part of a file
def get_sha256_chunk(filepath, header_offset, next_header_offset):
    sha256_hash = None
    with open(filepath,"rb") as f:
        f.seek(header_offset)
        bytes = f.read(next_header_offset-header_offset) # read entire file as bytes
        sha256_hash = hashlib.sha256(bytes).hexdigest();
    
    return sha256_hash


# get the SHA256 hash of part of a file and store it in a separate file
def sha256_and_store_trunczip(filepath, header_offset, next_header_offset, tmp_folder="tmp/"):
    with open(filepath,"rb") as f:
        f.seek(header_offset)
        bytes = f.read(next_header_offset-header_offset)
        # print("Storing: ", header_offset, next_header_offset, len(bytes), "bytes")
        sha256_hash = hashlib.sha256(bytes).hexdigest()
        # Obtain file path in the new folder structure from helper methods
        tmp_tf_path = tmp_folder + sha256_hash + '.trunczip'
        tf_subdir = helper.get_subdirectory(sha256_hash)
        truncfile_path = tf_subdir + sha256_hash + '.trunczip'
        with open(tmp_tf_path, "wb") as bf:
            bf.write(bytes)
    
        # Create the subdirectory for the tf
        os.makedirs(os.path.dirname(tf_subdir), exist_ok=True)
        # Actually add tmp to the final archive
        if not os.path.isfile(truncfile_path):
            shutil.copy(tmp_tf_path, truncfile_path)   

        # #Removed at the end regardless
        # #Remove the tmp truncfile once it has been stored by its sha256 hash
        # if os.path.exists(tmp_tf_path):
        #     os.remove(tmp_tf_path)

    return sha256_hash


# Creates modzip file without the deleted truncated chunks
# Returns the new filename .modzip
def create_modzip_deleted_truncfiles(filepath, new_filename, truncfiles, tmp_folder="tmp/"):
    previous_offset = 0
    tmp_file_path = tmp_folder + new_filename.split('/')[-1]
    for truncfile in truncfiles:
        offset = truncfile[1:3]
        with open(filepath, "rb") as f:
            f.seek(previous_offset)
            bytes=None
            bytes = f.read(offset[0] - previous_offset)
            # print("Storing: ", previous_offset, offset[0], len(bytes), "bytes")
            with open(tmp_file_path, 'ab') as new_f:
                new_f.write(bytes)
        
        previous_offset = offset[1]
    
    #store from previous offset to the end of the file
    with open(filepath, 'rb') as f:
        f.seek(previous_offset)
        bytes = f.read()
        # print("Storing: ", previous_offset, "onwards", len(bytes), "bytes")
        with open(tmp_file_path, 'ab') as new_f:
            new_f.write(bytes)

    # Create the subdirectory for the tf
    os.makedirs(os.path.dirname(new_filename.rsplit('/',1)[0]), exist_ok=True)

    # Actually add tmp to the final archive
    if not os.path.isfile(new_filename):
        shutil.copy(tmp_file_path, new_filename)

    #Remove the tmp truncfile once it has been stored by its sha256 hash
    if os.path.isfile(new_filename):
        os.remove(tmp_file_path)
        
    # NB: recommended deletion after testing
    print(new_filename)

    return new_filename


# Rebuild a copy of the file based on the modzip file, the truncfiles, and the original offsets
# Returns the new filename
def rebuild_original_file(new_file, modzip_file, csv_file):
    previous_offset = 0
    previous_bytes = 0
    truncfiles = helper.read_csv(csv_file)

    with open(new_file, 'ab') as new_f:
        for truncfile in truncfiles:
            # Using new directory structure
            truncfile_path = helper.get_subdirectory(truncfile[0])+truncfile[0]+'.trunczip'
            offset = [int(truncfile[1]), int(truncfile[2])]
            with open(modzip_file, 'rb') as f:
                f.seek(previous_bytes)
                length_between_chunks = offset[0] - previous_offset
                bytes = f.read(length_between_chunks)
                # print("Storing: ", previous_bytes, previous_bytes+length_between_chunks, len(bytes), "bytes")
                new_f.write(bytes)
                previous_offset=offset[1]
                previous_bytes+=len(bytes)
            with open(truncfile_path, 'rb') as f:
                bytes = f.read()
                # print("Storing chunk", len(bytes), "bytes")
                new_f.write(bytes)

        # Store from previous offset to the end of the file
        with open(modzip_file, 'rb') as f:
            f.seek(previous_bytes)
            bytes = f.read()
            # print("Storing:", previous_bytes, "onwards", len(bytes), "bytes")
            new_f.write(bytes)

    return True


def get_all_truncfile_chunks(app_file_path, tmp_folder='tmp/'):
    #list and set instead of using the DB
    truncfiles = []
    prev_filename = None
    prev_header_offset = 0

    try:
    	# Obtain file size
        size_of_file = 0
        with open(app_file_path,"rb") as f:
            bytes = f.read() # read entire file as bytes
            size_of_file = len(bytes)

        with ZipFile(app_file_path, 'r') as app:            
            # for all files, src "https://stackoverflow.com/questions/44799018/how-to-get-offset-values-of-all-files-or-given-filename-in-a-zipfile-using-pyt"
            for zinfo in app.infolist():
                filename = zinfo.filename
                isdir = zinfo.is_dir()
                header_offset = zinfo.header_offset 
                # compressed_filesize = zinfo.compress_size # NB: not enough, as the header is not taken into account
         		# Not treating folders as truncfiles, looking inside them
                if isdir:
                    # skip
                    prev_filename = filename
                    prev_header_offset = header_offset
                elif prev_filename is None:
                    prev_filename = filename
                    prev_header_offset = header_offset
                else:
                    sha256_prev_file = sha256_and_store_trunczip(app_file_path, prev_header_offset, header_offset, tmp_folder=tmp_folder)
                    size_prev_file = header_offset - prev_header_offset
                    truncfiles.append([sha256_prev_file, prev_header_offset, header_offset, size_prev_file])

                    prev_filename = filename
                    prev_header_offset = header_offset
            
            # Final trunc doesn't have a next_header_offset
	        # Next offset = end of file+1:
            sha256_final_file = sha256_and_store_trunczip(app_file_path, prev_header_offset, size_of_file+1, tmp_folder=tmp_folder)
            final_offset = size_of_file + 1
            size_final_file = size_of_file + 1 - prev_header_offset
            truncfiles.append([sha256_final_file, prev_header_offset, final_offset, size_final_file])

    except Exception as e:
        # NB:: these ones cannot be saved using the storage saving implementation
        # If 'zipfile.BadZipFile: Bad magic number for central directory', check if corrupted ZIP
        print(app_file_path)
        print(repr(e))
        truncfiles = []
    
    return truncfiles 

