# ModZips and TruncZips
This project contains code to convert ZIP files (in this case .IPA files too) into: a ModZip (.modzip) file, a CSV .csv file, and as many TruncZip (.trunczip) files as needed.

To explain these files and what they contain we need to explain ZIP files: ZIP files can contain compressed folder structures and files. So they contain an 'end of central directory record' located at the end of the archive, on top of this, each of the files and folders included starts with a 'local file header'. We leverage this information to get all the subfiles (not the folders) included in the ZIP file and store them separately based on their hash for easy retrieval. 

Thus, the resulting files are:
* A single ModZip file per ZIP ({file_sha256}.modzip) which contains all the structure and subfolders (still compressed), minus
* A lot of TruncZip files per ZIP ({file_portion_sha256}.trunczip) which contains a single compressed file.
* Finally, a single CSV file per ZIP ({file_sha256}.csv) which contains the list of all TruncZip files with their SHA256s i.e. filenames and original position in the compressed file.

This is done with the hopes that many of these files are present within multiple ZIP files and this can save us enough storage. This has been shown to work for medium datasets of iOS apps (IPAs) with many versions of the same apps. 


# How to run
In order to run the storage saving we need to download the example app and store it using the storage saving method by running:

* `python3 store_and_rebuild_apps.py`

The default values for the arguments market `-m` and IPAS folder `-ipas` do not need to be changed to run the example
`python3 store_and_rebuild_apps.py -m webarchive -ipas IPAS` would be the complete call

This script includes the download of a test app, and calls `storage_saving_helper.py` to convert the app into the (1) ModZip, (1) CSV and multiple TruncZip files. As mentioned in the previous section, the ModZip and CSV file are stored based on the original app SHA256 hash named `{file_sha256}.modzip` and `{file_sha256}.csv`, and the TruncZips are stored based on their individual hashes. This is what allows saving storage when they are present in more than one app.

`storage_saving_helper.py` automatically creates the needed subdirectories in `HASHED_IPAS` automatically for convenience, but a full implementation would already have the desired folder structure and depth ready and save the time needed to recheck these folders exist.
(The same is true for printing the .modzip file destination, only included here for convenience but not recommended at scale).


Then, when we want to rebuild the apps we can run the `store_and_rebuild_apps.py` script with the rebuild flag `-r` set, and the app's hash we are interested in. Optionally we can also set an output folder with the argument `-o`, the default is `tmp/`. Rebuilding the example app with hash `731fd133ba9b233504db4c729d154f334c30a79b2937a7f846b2199dabb2f8f8` can be done with:
* `python3 store_and_rebuild_apps.py -r -sha256 731fd133ba9b233504db4c729d154f334c30a79b2937a7f846b2199dabb2f8f8`

This script copies the ModZip and CSV files to the output folder (in this case `tmp/731fd133ba9b233504db4c729d154f334c30a79b2937a7f846b2199dabb2f8f8`) and then uses the information in the CSV file to inflate again the ModZip from all the extracted TruncZip files in the dataset.

At this point the app is checked against the original SHA256 hash to confirm it has been rebuilt correctly, after which point it can be treated as the original for any analysis and processing pipelines. 


# Dependencies
`pip install -r requirements.txt`, or manually:
- tqdm (`pip install tqdm`)
- requests (`pip install requests`)

# Future work
This technique has not been tested yet with a wider range of ZIP files and their extensions, e.g. APKs. We welcome any contributions on this. 