"""
Purpose:
    This script takes a new-line delimited .txt file of keywords and then downloads
    advertising information from Facebook's Ads Library that include those keywords.
    Information is scraped **only for the previous day**.

Inputs:
    A single config.ini file that has paths to a keywords.txt file with one
    keyword/phrase on each line as well as a paths for saving files.

Outputs:
    One new-line delimited json.gz file where each line item is one Facebook Ads
    data object for the previous day.
    Each file will be saved in the data directory provided as input and the
    filename name will include that date in the following form:
        - YYYY-MM-DD__fb_ads.json.gz

Authors:
    Manita Pote and Matthew R. DeVerna
"""
import argparse
import glob
import gzip
import json
import os
import requests
import sys
import time

from datetime import datetime, timedelta

from ad_library.python.fb_ads_library_api import FbAdsLibraryTraversal
from ad_library.python.fb_ads_library_api_operators import save_to_file
from midterm import load_config, get_logger

LOGGER_FILE = "fb_ads.log"
PROJECT_ROOT = "midterm2022"
ACCESS_KEY_FILENAME = "access_key.txt"
SLEEP_TIME = 30
NUMBER_OF_RESULTS = 300
SCRIPT_PURPOSE = "Retrieve Facebook Ads data based on a list of keywords."


def build_query_strings(keywords_file, max_len=100) -> list:
    """
    Construct query strings for FB ads API from a list of keywords, found in the
    `keywords_file` location, based on some maximum length.

    :param keywords_file (str): path to keyword file
    :param max_len (int): maximum length of query string. Default = 100.

    :return list of search terms
    """

    try:
        with open(keywords_file, "r") as file:
            keywords = [key.rstrip() for key in file.readlines()]
    except:
        raise Exception("Error in loading keyword file")

    count_list = [len(x) for x in keywords]

    i = 0
    sum_count = 0
    temp = []
    list_key = []
    total = len(count_list)

    while i < total:
        sum_count = sum_count + count_list[i]

        # Group keywords as long as their total length is <= max_len
        if sum_count <= max_len:
            temp.append(keywords[i])
            i = i + 1

        # Otherwise, add temp list to list key and reset temporary variables
        else:
            list_key.append(temp)

            temp = []
            sum_count = 0

        # Catches the last item
        if i == (total - 1):
            list_key.append(temp)

    return [",".join(key_list) for key_list in list_key]


def retrieve_new_access_key(
    access_key_path, access_key_filename, APP_ID, APP_SECRET
) -> str:
    """
    Retrieve a new Facebook access key.

    NOTE: Every sixty days Facebook will revoke our access to use the current
    API keys/tokens that we have. To stop this from happening, you can manually
    update the keys by hitting a certain endpoint (the one below). To make sure
    we never lose access, we update our keys every day. This is the purpose of
    this function.

    :param access_key_path: path where valid access key is located
    :param access_key_filename: name of file which has access key
    :param APP_ID: facebook ads app id
    :param APP_SECRET: facebook ads app secret

    :return access key
    """

    access_key_full_path = os.path.join(access_key_path, access_key_filename)

    try:
        with open(access_key_full_path, "r") as file:
            access_token = file.read().strip()
    except Exception as e:
        logger.error(e)
        logger.error(f"Error in reading access key file")

    BASE_URL = (
        "https://graph.facebook.com/v14.0/oauth/access_token?"
        + "grant_type=fb_exchange_token&"
        + f"client_id={APP_ID}&"
        + f"client_secret={APP_SECRET}&"
        + f"fb_exchange_token={access_token}"
    )

    logger.info("Start: Request Access Key")

    r = requests.get(url=BASE_URL)

    if r.status_code == 200:
        with open(access_key_full_path, "w") as f:
            new_access_token = r.json()["access_token"]
            f.write(new_access_token)
            logger.info("End: Request Access Key (success)")

    else:
        out = r.json()["error"]
        logger.error(f"status: {out['type']}")
        logger.error(f"Code error: {out['code']}")
        logger.error(f"Message: {out['message']}")
        sys.exit(
            "Error: Failed to get new FB Ads access key. "
            "Check log for specific error information."
        )

    return access_token


def make_requests(save_dir, access_token, query_list, start_date):
    """
    Makes request to facebook ad archive

    :param save_dir: directory where data to be saved
    :param access_token: valid access token
    :param query_list: list of queries to make
    :param start_date: date from which search starts
    """

    COUNTRY = "US"

    returned_fields = ",".join(
        [
            "id",
            "ad_creation_time",
            "ad_creative_bodies",
            "ad_creative_link_captions",
            "ad_creative_link_descriptions",
            "ad_creative_link_titles",
            "ad_delivery_start_time",
            "ad_delivery_stop_time",
            "ad_snapshot_url",
            "currency",
            "demographic_distribution",
            "delivery_by_region",
            "impressions",
            "languages",
            "page_id",
            "page_name",
            "publisher_platforms",
            "spend",
            "bylines",
        ]
    )

    if start_date is None:
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    today_date = datetime.now().strftime("%Y-%m-%d")

    for index, search_term in enumerate(query_list):
        logger.info(f"Starting data collection")
        logger.info(f"Search term: {search_term}")
        api = FbAdsLibraryTraversal(access_token, returned_fields,
                                    search_term, COUNTRY)
        api.page_limit = NUMBER_OF_RESULTS
        api.after_date = start_date

        i = 1
        while True:
            try:
                logger.info(f"Number of attempts: {i}")
                generator_ad_archives = api.generate_ad_archives()
                output_file = [
                    f"{os.path.join(save_dir, today_date)}_fb_ads_{index}.json"
                ]

                save_to_file(generator_ad_archives, output_file, is_verbose=True)

                logger.info(f"Ending data collection")

                break
            except Exception as e:
                logger.error(e)
                logger.error(f"Requesting data for {i} time, waiting for {SLEEP_TIME} seconds.")
                time.sleep(SLEEP_TIME)

                i = i + 1

                if i == 6:
                    logger.info(f"{i-1} calls tried and failed. Ending data collection")
                    break

                continue


def append_all_json(data_path, temp_data_path, start_date, filename):
    """
    Appends all temporary json files to one single data file for this day.

    :param data_path: path where appended file to be stored
    :param temp_data_path: path where temporary json file are present
    :param start_date: date from which search starts
    :param filename: name for the file after appending the json
    """

    try:
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Get all temporary data files created for yesterday's data
        file_list = glob.glob(f"{temp_data_path}/*")
        
        if filename is None:
            filename = f"{start_date}_fb_ads.json.gz"
            
        # This file will house all data from all temporary files
        output_file = os.path.join(data_path, filename)
        with gzip.open(output_file, "wb") as zipfile:

            for filename in file_list:

                # If the file is empty, skip it
                if os.stat(filename).st_size == 0:
                    continue

                with open(filename, "r") as file:
                    for line in file:
                        data = json.loads(line)
                        zipfile.write(f"{json.dumps(data)}\n".encode(
                            encoding="utf-8"))

    except Exception as e:
        logger.exception(e)
        raise Exception("Error in merging json files")


def remove_temp_files(temp_data_path):
    """
    Removes all temporary json files

    :param temp_data_path: path where temporary json file are present
    """

    try:
        for filename in glob.glob(f"{temp_data_path}/*"):
            os.remove(filename)
    except Exception as e:
        logger.error(f"Failed deleting temporary files: {e}")
        
        
def parse_config_arg_w_optional_date_filename(script_purpose):
    """
    Set command-line arguments.

    Required:
        -c / --config

    Optional:
        -d / --date (YYYY-MM-DD)
        -f / --filename (filename)

    """
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=script_purpose)

        # Add optional arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file. ",
            required=True,
        )

        parser.add_argument(
            "-d",
            "--date",
            metavar="Date",
            help="The day on which to pull data. Format: YYYY-MM-DD",
            required=False,
            default=None
        )

        parser.add_argument(
            "-f",
            "--filename",
            metavar="Filename",
            help="The filename for the new file. Example: 2022-06-01.json.gz",
            required=False,
            default=None,
        )

        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()
        print("Success.")
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)



if __name__ == "__main__":
    cwd = os.getcwd()

    if os.path.basename(cwd) != PROJECT_ROOT:
        raise Exception(
            "All scripts must be run from the root directory of the project!"
        )

    # Load config path
    args = parse_config_arg_w_optional_date_filename(SCRIPT_PURPOSE)
    start_date = args.date
    config_file_path = args.config
    filename = args.filename
    config_file = load_config(config_file_path)

    # Extract key files and paths from config
    keywords_file = config_file["PATHS"]["keywords_file"]
    temp_data_dir = config_file["PATHS"]["data_dir_fb_ads_temp"]
    if not os.path.exists(temp_data_dir):
        os.makedirs(temp_data_dir)

    data_path = config_file["PATHS"]["data_dir_fb_ads"]
    logger_path = config_file["PATHS"]["log_dir_fb_ads"]

    # Retrieve credentials
    credential_file = load_config(config_file["CREDENTIALS"]["file_path"])
    app_id = credential_file["FB_ADS_CREDS"]["app_id"]
    app_secret = credential_file["FB_ADS_CREDS"]["app_secret"]

    # Initialize logger
    full_path_logger = os.path.join(logger_path, LOGGER_FILE)
    logger = get_logger(logger_path, full_path_logger, also_print=True)

    query_list = build_query_strings(keywords_file, max_len=90)

    try:
        fb_ads_access_token = retrieve_new_access_key(
            credential_file["PATHS"]["access_key_path"],
            ACCESS_KEY_FILENAME,
            app_id,
            app_secret,
        )

        make_requests(temp_data_dir, fb_ads_access_token,
                      query_list, start_date)

        append_all_json(data_path, temp_data_dir, start_date, filename)

        remove_temp_files(temp_data_dir)
    except Exception as e:
        logger.error(e)

    logger.info("Script complete")
    logger.info("-" * 50)
