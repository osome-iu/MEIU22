"""
Purpose:
    This script fetch the list of archived threads of /pol board from 4chan
    then download the full threads (including all replies) of the newly archived ones

Inputs:
    A single config.ini file with the data directory and log directory

Output:
    Multiple json.gz files containing the list of archived threads
    A one new-line delimited json.gz file containing the json of the archived threads

Author: Kaicheng Yang
"""
import requests
import json
import gzip
import time
import os
import datetime

from midterm import load_config, get_logger, parse_config_only_cl_arg

SCRIPT_PURPOSE = "This script fetches the archived threads of /pol board from 4chan"
PROJECT_ROOT = "midterm2022"
URL_ARCHIVE = "https://a.4cdn.org/pol/archive.json"
URL_THREAD = "https://a.4cdn.org/pol/thread/{thread_id}.json"

def fetch_archive_list():
    # This endpoint gives a list of ids of threads that have been pushed
    # out of the last page of the board.
    # These threads are not longer active and cannot be replied.
    r_archive = requests.get(URL_ARCHIVE)
    return r_archive.json()

def fetch_thread(thread_id):
    r = requests.get(URL_THREAD.format(thread_id=thread_id))
    return r.json()

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

    data_folder = project_config["PATHS"]["data_dir_4chan_archive"]
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    logger_dir = project_config["PATHS"]["log_dir_4chan"]
    logger_fname = "4chan_archive.log"
    full_path_logger = os.path.join(logger_dir, logger_fname)
    logger = get_logger(logger_dir, full_path_logger)

    logger.info("-" * 50)
    logger.info("Start to collect archive list from 4chan /pol")

    today = datetime.datetime.today().strftime('%Y-%m-%d')
    now = datetime.datetime.now()
    minute_of_day = now.hour * 60 + now.minute

    archive_list_folder = os.path.join(data_folder, "archive_list", f"{today}")
    if not os.path.exists(archive_list_folder):
        os.makedirs(archive_list_folder)
    # Identify all existing files
    all_files = os.listdir(archive_list_folder)

    archive_list_file = os.path.join(archive_list_folder, f"{minute_of_day}.json.gz")

    logger.info(f"\t|--> Data saved in this file: {archive_list_file}")
    archive_list = fetch_archive_list()
    with gzip.open(archive_list_file, "wb") as f:
        bytes_to_write = json.dumps(archive_list).encode("utf-8")
        f.write(bytes_to_write)

    # Now, compare with the previous one
    if len(all_files) > 0:
        # Sort the files based on the minute_of_day of that file
        last_file = sorted(all_files, key=lambda x: int(x.split(".")[0]))[-1]
        with gzip.open(os.path.join(archive_list_folder, last_file)) as f:
            archive_list_last = json.load(f)

        set_last = set(archive_list_last)
        set_new = set(archive_list)
        new_archived_ids = list(set_new - (set_new & set_last))
        logger.info(f"{len(new_archived_ids)} new thread id detected")
        logger.info("Start to download")

        new_archived_threads = []
        for new_archived_id in new_archived_ids:
            try:
                thread = fetch_thread(new_archived_id)
            except Exception as e:
                logger.exception(e)
            else:
                new_archived_threads.append(thread)
            finally:
                time.sleep(0.5)

        logger.info(f"{len(new_archived_threads)} new threads downloaded")
        archive_thread_folder = os.path.join(data_folder, "archive_threads")
        if not os.path.exists(archive_thread_folder):
            os.makedirs(archive_thread_folder)
        archive_thread_file = os.path.join(archive_thread_folder, f"{today}__4chan_archived_threads.json.gz")
        logger.info(f"\t|--> Threads saved in this file: {archive_thread_file}")
        with gzip.open(archive_thread_file, "ab") as f:
            for thread in new_archived_threads:
                bytes_to_write = f"{json.dumps(thread)}\n".encode("utf-8")
                f.write(bytes_to_write)

    logger.info("Script complete")
    logger.info("-" * 50)