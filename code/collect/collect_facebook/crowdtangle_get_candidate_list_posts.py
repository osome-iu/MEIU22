"""
Purpose:
    Download Facebook posts from CrowdTangle based on a list of midterm candidates.
    NOTE:
        1. This list must be created manually in CrowdTangle prior to utilizing this script.
        2. The list ID is set manually at the top of this script
            - You can retrieve it by using `midterm.data.ct_get_lists()`

Inputs:
    Required: -c: config.ini file
    Optional:
        -s / --start_date (YYYY-MM-DD)
        -e / --end_date (YYYY-MM-DD) — Not inclusive!
    NOTE:
        - If neither `start_date` is nor `end_date` are included, we pull data for the
            previous UTC day
        - If `end_date` is included, `start_date` must also be included
        - If `start_date` is included but no `end_date` is included, the current UTC
            date is utilized as the `end_date` (i.e., all data from `start_date` up to
            but not including today (UTC) is gathered)

Outputs:
    One new-line delimited json.gz file with all posts from FB for the specified period.
    Output file name form:
        - start_date-end_date__candidate_fb_posts.json.gz
            - `start_date` and `end_date` take the following format: YYYY-MM-DD
            - Dates represent the date range of the downloaded data
            - NOTE: end_date is NOT inclusive. This means that a date range like
                2022-11-05-2022-11-06 indicates that the data was pulled for
                only 2022-11-05.

Authors:
    Matthew R. DeVerna
"""
import datetime
import gzip
import json
import os
import requests
import time
import sys

from midterm import load_config, parse_config_arg_w_start_end_dates, get_logger

SCRIPT_PURPOSE = (
    "Download Facebook posts from CrowdTangle based on a list of midterm candidates."
)

LOG_FILE_NAME = "fb_candidates.log"
NUMBER_OF_POSTS_TO_PULL = 100
PROJECT_ROOT = "midterm2022"

# Number of seconds to wait before every query, success or error
WAIT_BTWN_POSTS = 5

# Base number of seconds to wait after encountering an error, raised to the number of retry counts
WAIT_BTWN_ERROR_BASE = 2

# In order for the script to work, this must match the list name from which we want to pull posts.
# Use `midterm.data.ct_get_lists()` to find the right list ID
CROWDTANGLE_LIST_ID = 1726920


def ct_get_posts(
    count=10,
    start_time=None,
    end_time=None,
    include_history=None,
    sort_by="date",
    types=None,
    search_term=None,
    min_interactions=0,
    offset=0,
    api_token=None,
    listIds=None,
):
    """
    Retrieve a set of posts for the given parameters from CrowdTangle using the
    `posts` endpoint with the `listIds` parameter.

    Parameters:
    - count (int, optional): The number of posts to return. Defaults to 100.
        - Options [1-100] (or higher, if you have additional access)
    - start_time (str, optional): The earliest time at which a post could be posted. Time zone is UTC.
        - Format: “yyyy-mm-ddThh:mm:ss” or “yyyy-mm-dd”
            - If date with no time is passed, default time granularity = 00:00:00
    - end_time (str, optional): The latest time at which a post could be posted. Time zone is UTC.
        - Format: “yyyy-mm-ddThh:mm:ss” or “yyyy-mm-dd”
            - If date with no time is passed, default time granularity = 00:00:00
        - Default time: "now"
    - include_history (str, optional): Includes time step data for the growth of each post returned.
        - Options: 'true'
        - Default: None (not included)
    - sort_by (str, optional): The method by which to filter and order posts.
        - Options:
            - 'date'
            - 'interaction_rate'
            - 'overperforming'
            - 'total_interactions'
            - 'underperforming'
        - Default: 'overperforming'
    - types (str, optional): The types of post to include. These can be separated by commas to
        include multiple types. If you want all live videos (whether currently or formerly live),
        be sure to include both live_video and live_video_complete. The "video" type does not
        mean all videos, it refers to videos that aren't native_video, youtube or vine (e.g. a
        video on Vimeo).
        - Options:
            - "episode"
            - "extra_clip"
            - "link"
            - "live_video"
            - "live_video_complete"
            - "live_video_scheduled"
            - "native_video"
            - "photo"
            - "status"
            - "trailer"
            - "video"
            - "vine"
            - "youtube"
        - Default: all
    - search_term (str, optional): Returns only posts that match this search term.
        Terms AND automatically. Separate with commas for OR, use quotes for phrases.
        E.g. CrowdTangle API -> AND. CrowdTangle, API -> OR. "CrowdTangle API" -> AND in that
        exact order. You can also use traditional Boolean search with this parameter.
        Default: None (no search term)
    - min_interactions (int, optional): If set, will exclude posts with total interactions
        below this threshold.
        - Options: int >= 0
        - Default: 0
    - offset (int, optional): The number of posts to offset (generally used for pagination).
        Pagination links will also be provided in the response.
    - api_token (str, optional): The API token needed to pull data. You can locate your API
        token via your CrowdTangle dashboard under Settings > API Access.
    - listIds: The IDs of lists or saved searches to retrieve. These can be separated by commas
        to include multiple lists.
        - Default: None (i.e posts from all Lists, not including saved searches or saved posts
            lists, in the Dashboard)

    Returns:
    [dict]: The Response contains both a status code and a result. The status will always
        be 200 if there is no error. The result contains an array of post objects and
        a pagination object with URLs for both the next and previous page, if they exist

    Example:
        ct_get_posts(include_history = 'true', api_token="AKJHXDFYTGEBKRJ6535")
    """

    # api-endpoint
    URL_BASE = "https://api.crowdtangle.com/posts"
    # defining a params dict for the parameters to be sent to the API
    PARAMS = {
        "count": count,
        "sortBy": sort_by,
        "token": api_token,
        "minInteractions": min_interactions,
        "offset": offset,
    }

    # add params parameters
    if start_time:
        PARAMS["startDate"] = start_time
    if end_time:
        PARAMS["endDate"] = end_time
    if include_history == "true":
        PARAMS["includeHistory"] = include_history
    if types:
        PARAMS["types"] = types
    if search_term:
        PARAMS["searchTerm"] = search_term
    if listIds:
        PARAMS["listIds"] = listIds

    # sending get request and saving the response as response object
    r = requests.get(url=URL_BASE, params=PARAMS)
    if r.status_code != 200:
        logger.info(f"status: {r.status_code}")
        logger.info(f"reason: {r.reason}")
        logger.info(f"details: {r.raise_for_status}")
    return r.json()


if __name__ == "__main__":
    # Ensure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        raise Exception(
            "All scripts must be run from the root directory of the project!"
        )

    # Load and parse the config file
    args = parse_config_arg_w_start_end_dates(SCRIPT_PURPOSE)
    config_file_path = args.config
    start_date = args.start_date
    end_date = args.end_date
    project_config = load_config(config_file_path)

    data_folder = project_config["PATHS"]["data_dir_fb_candidates"]

    # Set up the logger
    logger_dir = project_config["PATHS"]["log_dir_meta"]
    full_path_logger = os.path.join(logger_dir, LOG_FILE_NAME)
    logger = get_logger(logger_dir, full_path_logger, also_print=True)
    logger.info("Start to collect data for Facebook and Instagram")

    # Load the necessary credentials for CrowdTangle
    try:
        logger.info("Loading credentials...")
        credentials_file = project_config["CREDENTIALS"]["file_path"]
        credentials_config = load_config(credentials_file)
        api_token = credentials_config["META_CREDS"]["ct_osome_access_token"]
    except Exception as e:
        logger.exception("Problem loading credentials!")

    # Catch start/end date input error
    if (end_date is not None) and (start_date is None):
        logger.error("`end_date` was provided but `start_date` was not!!")
        sys.exit("`end_date` was provided but `start_date` was not!!")

    logger.info("Setting start time...")
    if start_date is not None:
        logger.info(f"User-input start date: {start_date}")
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        start = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        start_dt = datetime.datetime.today().date() - datetime.timedelta(days=1)
        start = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        logger.info(f"Using yesterday's UTC date as start date: {start}")

    logger.info("Setting end time...")
    if end_date is not None:
        logger.info(f"User-input end date: {end_date}")
        end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        end_dt = datetime.datetime.today().date()
        end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
        logger.info(f"Using current UTC date as end date: {start}")

    logger.info(f"CrowdTangle List ID  : {CROWDTANGLE_LIST_ID}")
    logger.info(f"Data output directory: {data_folder}")

    # Create output data folder if it doesn't exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    start_str = start_dt.strftime("%Y-%m-%d")
    end_str = end_dt.strftime("%Y-%m-%d")
    fname = f"{start_str}-{end_str}__candidate_fb_posts.json.gz"
    full_output_path = os.path.join(data_folder, fname)
    logger.info(f"Posts will be saved here: {full_output_path}")

    logger.info("Begin collecting data")
    logger.info("-" * 50)
    logger.info(f"\t|--> Collecting data for the period: {start}<--->{end}")

    with gzip.open(full_output_path, "wb") as f:

        total_posts = 0
        query_count = 0
        retry_count = 0
        max_retries = 10

        first_call = True
        more_data = False
        while first_call or more_data:
            try:
                if first_call:
                    time.sleep(WAIT_BTWN_POSTS)
                    results = ct_get_posts(
                        count=NUMBER_OF_POSTS_TO_PULL,
                        start_time=start,
                        end_time=end,
                        include_history="true",
                        sort_by="date",
                        api_token=api_token,
                        listIds=CROWDTANGLE_LIST_ID,
                    )

                else:
                    # This is the full URL returned by CT to continue pulling data
                    # from the next page. See block below.
                    time.sleep(WAIT_BTWN_POSTS)
                    response = requests.get(next_page_url)
                    results = response.json()

                # Returns a list of dictionaries where each dict represents one post.
                posts = results["result"]["posts"]
                num_posts = len(posts)

                # Flip first_call if we get a successful first call with posts
                # NOTE: repeated first calls with no data will break after too many attempts
                if first_call:
                    if (results["status"] == 200) and (num_posts != 0):
                        logger.info("Successful first call.")
                        logger.info("Setting first_call = False")
                        first_call = False

                # Reset and then grab the pagination url if it is there
                next_page_url = None
                if "pagination" in results["result"]:
                    if "nextPage" in results["result"]["pagination"]:
                        next_page_url = results["result"]["pagination"]["nextPage"]
                        logger.info(f"Found next page: {next_page_url}")
                        more_data = True

                if next_page_url is None:
                    more_data = False

            # TODO: Check the rate limit without fpierri's increase. Matt added wait time
            # between calls to be safe.
            except Exception as e:  # 6 calls/minute limit if you request them
                logger.exception(e)

                # Handle the retries...
                logger.info(f"There are {max_retries-retry_count} retries left.")
                retry_count += 1
                if (max_retries - retry_count) <= 0:
                    break
                else:
                    wait_time = WAIT_BTWN_ERROR_BASE**retry_count
                    if wait_time > 60:
                        wait_time = wait_time / 60
                        logger.error(f"Waiting {wait_time} minutes...")
                    else:
                        logger.error(f"Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    logger.info(f"Retrying...")
                    continue

            else:
                if num_posts == 0:
                    logger.info("Zero posts were returned.")
                    logger.info(f"There are {max_retries-retry_count} retries left.")
                    retry_count += 1

                    if (max_retries - retry_count) <= 0:
                        break
                    else:
                        wait_time = WAIT_BTWN_ERROR_BASE**retry_count
                        if wait_time > 60:
                            wait_time = wait_time / 60
                            logger.error(f"Waiting {wait_time} minutes...")
                        else:
                            logger.error(f"Waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        logger.info(f"Retrying...")
                        continue

                else:
                    # Reset the retry count to zero
                    retry_count = 0

                    most_recent_date_str = posts[0]["date"]
                    oldest_date_str = posts[-1]["date"]
                    logger.info(
                        f"\t|--> {oldest_date_str} - {most_recent_date_str}"
                        f": {num_posts:,} posts."
                    )

                    # Convert each post into bytes with a new-line (`\n`)
                    for post in posts:
                        post_in_bytes = f"{json.dumps(post)}\n".encode(encoding="utf-8")
                        f.write(post_in_bytes)

                    total_posts += num_posts
                    logger.info(f"Total posts collected: {total_posts:,}")

                # More than 50_000 queries (~5M posts), we break the script.
                query_count += 1
                if query_count > 50_000:
                    break

    logger.info("All data downloaded.")
    logger.info("-" * 50)
