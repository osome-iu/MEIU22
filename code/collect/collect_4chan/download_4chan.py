"""
Purpose:
    This script fetch the catalog and archive of /pol board from 4chan

Inputs:
    A single config.ini file with the data directory and log directory

Output:
    One new-line delimited json.gz file with the collected data.
    Each line contain the following information:
    {
        "time": unix_time,
        "catalog": catalog_json,
        "archive": archive_json
    }

Author: Kaicheng Yang
"""
import requests
import json
import gzip
import time
import os
import datetime

from midterm import load_config, get_logger, parse_config_only_cl_arg

SCRIPT_PURPOSE = "This script fetch the catalog and archive of /pol board from 4chan"
PROJECT_ROOT = "midterm2022"
URL_CATALOG = "https://a.4cdn.org/pol/catalog.json"
URL_ARCHIVE = "https://a.4cdn.org/pol/archive.json"

def fetch_pol():
    # This endpoint gives a snapshot of the /pol.
    # It contains 11 pages of threads.
    r_catalog = requests.get(URL_CATALOG)
    catalog_json = r_catalog.json()

    # This endpoint gives a list of ids of threads that have been pushed
    # out of the last page of the board.
    # These threads are not longer active and cannot be replied.
    r_archive = requests.get(URL_ARCHIVE)
    archive_json = r_archive.json()

    unix_time = int(time.time())

    return {
        "time": unix_time,
        "catalog": catalog_json,
        "archive": archive_json
    }

if __name__ == "__main__":
    # Ensure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        raise Exception(
            "All scripts must be run from the root directory of the project!"
        )

    # Load and parse the config file
    args = parse_config_only_cl_arg(SCRIPT_PURPOSE)
    config_file_path = args.config
    project_config = load_config(config_file_path)

    data_folder = project_config["PATHS"]["data_dir_4chan"]
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    logger_dir = project_config["PATHS"]["log_dir_4chan"]
    logger_fname = "4chan.log"
    full_path_logger = os.path.join(logger_dir, logger_fname)
    logger = get_logger(logger_dir, full_path_logger)

    logger.info("-" * 50)
    logger.info("Start to collect data from 4chan /pol")

    today = datetime.datetime.today().strftime('%Y-%m-%d')
    fname = f"{today}__threads_4chan.json.gz"
    logger.info(f"\t|--> Data saved in this file: {fname}")
    full_output_path = os.path.join(data_folder, fname)


    with gzip.open(full_output_path, "ab") as f:
        # Will try at most 5 times
        for i in range(5):
            try:
                pol_obj = fetch_pol()
            except Exception as e:
                logger.exception(e)
                logger.error("Waiting ten seconds...")
                time.sleep(10)
                continue
            else:
                bytes_to_write = f"{json.dumps(pol_obj)}\n".encode(encoding="utf-8")
                f.write(bytes_to_write)
                break
    logger.info("Script complete")
    logger.info("-" * 50)