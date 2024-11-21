import os
from tqdm import tqdm
import hashlib
import shutil
import argparse
import storage_saving_helper as storage
import helper_methods as helper

parser = argparse.ArgumentParser()
parser.add_argument('-m', default='webarchive', help='Hash IPAs (apps) for a particular market only')
parser.add_argument('-ipas', default='IPAS', help='IPAs folder name, default')
parser.add_argument('-r', action='store_true') # Rebuild flag
parser.add_argument('-sha256', help='The SHA256 hash of the app we want to rebuild (i.e. the hash in the filename {sha256}.modzip)')
parser.add_argument('-o', default='tmp/', help='Output folder for rebuilt apps')

args = vars(parser.parse_args())


def get_apps_list_market(market):
	ipas_folder = market+'/'+args['ipas']+'/'
	ipas_list = []
	for filename in os.listdir(ipas_folder):
		file = ipas_folder + filename
		#if less than 500KB, possibly an error, html page or config file instead of actual IPA
		file_size = os.stat(file).st_size
		if file_size >= 500000:
			ipas_list.append([file, filename])

	return ipas_list


# inputs: [file_location, filename], market - used to update the market-specific table
def store_by_hash(file, market):
	tmp_folder = 'tmp/'
	sha256_hash = ""
	file_location = file[0]
	filename = file[1]
	with open(file_location, "rb") as f:
		bytes = f.read()
		sha256_hash = hashlib.sha256(bytes).hexdigest()
		# Create tmp folder
		tmp_folder += sha256_hash + '/'
		helper.create_folder(tmp_folder)

	# Obtain the correct subdirectory with the correct depth e.g. 01/aa/23/bc/9f/
	subdirectory = helper.get_subdirectory(sha256_hash)
	new_file_name = subdirectory + sha256_hash + '.modzip' 

	# Storage savings with .trunczip, .trunc OR .modzip, .trunczip
	# Create the subdirectory for the IPA
	os.makedirs(os.path.dirname(subdirectory), exist_ok=True)
	csv_filename = subdirectory + sha256_hash + '.csv'
	modzip_file_filename = ''

	try:
		if not os.path.isfile(new_file_name):
			# Create truncfiles, modzip skeleton file, and csv files
			truncfiles = storage.get_all_truncfile_chunks(file_location, tmp_folder=tmp_folder)
			# If truncfiles is empty... do not call them modzip and truncfiles etc.
			if len(truncfiles)==0:
				# NB: choose whether to store these as normal (the version below), or somewhere else instead for further checks
				shutil.copy(file_location, new_file_name)
				os.remove(file_location)

			else:
				helper.write_list_of_lists_to_csv(truncfiles, csv_filename)
				modzip_file_filename = storage.create_modzip_deleted_truncfiles(file_location, new_file_name, truncfiles, tmp_folder=tmp_folder)

			# We recheck every single truncfile and the csv file as well
			# Remove the IPA once it has been stored by its sha256 hash
			if os.path.isfile(file_location):
				if os.path.isfile(csv_filename) and os.path.isfile(modzip_file_filename):
					# Check each truncfile
					all_truncfiles_exist = True
					for tf in truncfiles:
						# tf[0] constains the truncfile's sha256 hash
						tf_filename = helper.get_subdirectory(tf[0]) + tf[0] + '.trunczip'
						if not os.path.isfile(tf_filename):
							all_truncfiles_exist = False

					if all_truncfiles_exist:
						os.remove(file_location)

	except Exception as e:
		print(e, filename)

	# Remove tmp folder in any case
	helper.remove_folder(tmp_folder)

	return True



if __name__ == '__main__':
	rebuild = args['r']
	if not rebuild:
		market = args['m']
		test_folder = 'webarchive/IPAS/'
		os.makedirs(market, exist_ok=True)
		os.makedirs(test_folder, exist_ok=True)
		helper.download_to("https://archive.org/download/ios-ipa-collection/1Password%20Pro%203.5.4.ipa", test_folder, "1PasswordPro_v3.5.4.ipa")

		print("*** Processing the hashes from " + market)
		apps_list = get_apps_list_market(market)

		# NB: cannot be simply parallelised due to the modzip generation
		for app in tqdm(apps_list):
			store_by_hash(app, market)

	else:
		app_sha256 = args['sha256']
		output_folder = args['o']
		os.makedirs(output_folder, exist_ok=True)
		# Rebuilding the app
		rebuilt_app = output_folder + app_sha256 + '/'
		os.makedirs(rebuilt_app, exist_ok=True)

		# Get modzip and csv files
		subdirectory = helper.get_subdirectory(app_sha256)
		modzip_file_original = subdirectory + app_sha256 + '.modzip'
		csv_file_original = subdirectory + app_sha256 + '.csv'

		modzip_file = rebuilt_app + app_sha256 + '.modzip'
		csv_file = rebuilt_app + app_sha256 + '.csv'

		try:
			# Copy modzip and csv file to the tmp folder
			shutil.copy(modzip_file_original, modzip_file)
			shutil.copy(csv_file_original, csv_file)

			# Rebuild the app into the tmp folder
			new_file = rebuilt_app + app_sha256 + '.ipa'
			storage.rebuild_original_file(new_file, modzip_file, csv_file)

			# Check the sha256 of the rebuilt app is correct
			if helper.get_hash256(new_file) == app_sha256:
				print("App rebuilt correctly at:", new_file)
				print("Now this copy can be analysed as a normal IPA, then discarded and the ModZip and TruncZip files are retained in the dataset")

			else:
				print("Incorrectly stored/ rebuilt app", app_sha256)

		except Exception as e:
			print(repr(e), app_sha256, "could not be analysed")

		# # Remove app tmp folder
		# helper.remove_folder(tmp_folder_app)
