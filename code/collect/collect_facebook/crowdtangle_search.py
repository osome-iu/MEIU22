"""
Purpose:
    This script takes a new-line delimited .txt file of keywords and then downloads
    posts from Facebook/Instagram that include those keywords. Posts are scraped
    from the date range provide by the `start_time` and `end_time` parameters.

Inputs:
    A single config.ini file that has paths to a keywords.txt file with one
    keyword/phrase on each line as well as a data directory where files will be saved.

Outputs:
    One new-line delimited json.gz file with all posts from FB and IG for the previous day.
    Each file will be saved in the data directory provided as a CL input and the
    filename name will include that date in the following form: YYYY-MM-DD__posts_FB_IG.json.gz
    - Date in the filename will reflect the start date provided

Authors:
    Matthew R. DeVerna
"""
import datetime
import gzip
import json
import os
import requests
import time


from midterm import load_config, parse_config_arg_w_optional_date, get_logger

SCRIPT_PURPOSE = (
    "This script takes a single config.ini file as input. It then reads a new-line "
    "delimited file of keywords to download posts from Facebook & Instagram that "
    "include those keywords from the past day."
)
NUMBER_OF_POSTS_TO_PULL = 10_000
PROJECT_ROOT = "midterm2022"


def ct_get_search_posts(
    count=NUMBER_OF_POSTS_TO_PULL,
    start_time=None,
    end_time=None,
    include_history=None,
    sort_by="date",
    types=None,
    search_term=None,
    account_types=None,
    min_interactions=0,
    offset=0,
    api_token=None,
    platforms="facebook,instagram",
    lang=None,
):
    """
    Retrieve posts from Facebook/Instagram based on the passed parameters.
    REF: https://github.com/CrowdTangle/API/wiki/Search

    Parameters:
        - count (int, optional): The number of posts to return.
            Options: [1-100]
            Default: 10
        - start_time (str, optional): The earliest time at which a post could be posted. Time zone
            is UTC.
            Format: “yyyy-mm-ddThh:mm:ss” or “yyyy-mm-dd”
                - If date with no time is passed, default time granularity = 00:00:00
        - end_time (str, optional): The latest time at which a post could be posted. Time zone is
            UTC.
            Format: “yyyy-mm-ddThh:mm:ss” or “yyyy-mm-dd”
                - If date with no time is passed, default time granularity = 00:00:00
            Default time: "now"
        - include_history (str, optional): Includes time step data for the growth of each post returned.
            Options: 'true'
            Default: null (not included)
        - sort_by (str, optional): The method by which to filter and order posts.
            Options:
                - 'date'
                - 'interaction_rate'
                - 'overperforming'
                - 'total_interactions'
                - 'underperforming'
            Default: 'overperforming'
        - types (str, optional): The types of post to include. These can be separated by commas to
            include multiple types. If you want all live videos (whether currently or formerly live),
            be sure to include both live_video and live_video_complete. The "video" type does not
            mean all videos, it refers to videos that aren't native_video, youtube or vine (e.g. a
            video on Vimeo).
            Options:
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
                -  "youtube"
            Default: all
        - search_term (str, optional): Returns only posts that match this search term.
            Terms AND automatically. Separate with commas for OR, use quotes for phrases.
            E.g. CrowdTangle API -> AND. CrowdTangle, API -> OR. "CrowdTangle API" -> AND in that
            exact order. You can also use traditional Boolean search with this parameter.
            Default: null
        - account_types: Limits search to a specific Facebook account type. You can use more than
            one type. Requires "platforms=facebook" to be set also. If "platforms=facebook" is not
            set, all post types including IG will be returned. Only applies to Facebook.
            Options:
                - facebook_page
                - facebook_group
                - facebook_profile
            Default: None (no restrictions, all platforms)
        - min_interactions (int, optional): If set, will exclude posts with total interactions
            below this threshold.
            Options: int >= 0
            Default: 0
        - offset (int, optional): The number of posts to offset (generally used for pagination).
            Pagination links will also be provided in the response.
        - api_token (str, optional): The API token needed to pull data. You can locate your API
            token via your CrowdTangle dashboard under Settings > API Access.
        - platforms: the platform to collect data from
            Options: "facebook", "instagram", or "facebook,instagram" (both)
            Default: "facebook,instagram"
        - lang: language of the posts to collect (str)
            Default: None (no restrictions)
            Options: 2-letter code found in reference below. See ref above for some exceptions.
            REF:https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    Returns:
        [dict]: The Response contains both a status code and a result. The status will always
            be 200 if there is no error. The result contains an array of post objects and a
            pagination object with URLs for both the next and previous page, if they exist
    Example:
        ct_get_posts(include_history = 'true', api_token="AKJHXDFYTGEBKRJ6535")
    """

    # API-endpoint
    URL_BASE = "https://api.crowdtangle.com/posts/search"
    # Defining a params dict for the parameters to be sent to the API
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
    if account_types:
        PARAMS["accountTypes"] = account_types
    if search_term:
        PARAMS["searchTerm"] = search_term
    if platforms:
        PARAMS["platforms"] = platforms
    if lang:
        PARAMS["language"] = lang

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
    args = parse_config_arg_w_optional_date(SCRIPT_PURPOSE)
    config_file_path = args.config
    start_date = args.date
    project_config = load_config(config_file_path)

    keywords_file_path = project_config["PATHS"]["keywords_file"]
    data_folder = project_config["PATHS"]["data_dir_meta"]
    logger_dir = project_config["PATHS"]["log_dir_meta"]
    logger_fname = "meta.log"
    full_path_logger = os.path.join(logger_dir, logger_fname)

    # Get logger
    logger = get_logger(logger_dir, full_path_logger, also_print=True)
    logger.info("Start to collect data for Facebook and Instagram")

    # Load the necessary credentials for CrowdTangle
    credentials_file = project_config["CREDENTIALS"]["file_path"]
    credentials_config = load_config(credentials_file)
    api_token = credentials_config["META_CREDS"]["ct_access_token"]

    logger.info(f"Keywords file: {keywords_file_path}")
    logger.info(f"Data directory: {data_folder}")

    logger.info("Converting keywords file into CrowdTangle query...")
    try:
        with open(keywords_file_path, "r") as f:
            track = [l.rstrip() for l in f.readlines()]
        track = ",".join(track)
    except Exception as e:
        logger.exception(e)
        raise Exception("Problem loading keywords!")

    logger.info(f"\t - Query is: {track}")

    logger.info("Setting start and end time...")
    if start_date is not None:
        logger.info(f"Collecting data from the user-input date: {start_date}")
        start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        start = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_dt = start_dt + datetime.timedelta(days=1)
        end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    else:
        logger.info(f"Using the current UTC date as our start date.")
        start_dt = datetime.datetime.today().date() - datetime.timedelta(days=1)
        start = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_dt = datetime.datetime.today().date()
        end = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

    logger.info(f"\t - Collecting data for the period: {start}<--->{end}")
    logger.info(
        "\t - Note: If exact times are not provided query defaults to 00:00:00."
    )

    # Create output data folder if it doesn't exist
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    logger.info("Begin collecting data")
    logger.info("-" * 50)

    fname = f"{start_dt.strftime('%Y-%m-%d')}__posts_FB_IG.json.gz"
    logger.info(f"\t|--> Posts saved in this file: {fname}")
    full_output_path = os.path.join(data_folder, fname)
    with gzip.open(full_output_path, "wb") as f:

        query_count = 0
        retry_count = 0
        max_retries = 10  # Accommodates the 6 calls/minute rate limit
        while True:
            try:
                # count = 10000 only if you request it, otherwise it's 100
                # NOTE: This is more than the function says is allowed because we requested
                # increased API limits from CrowdTangle folks.
                results = ct_get_search_posts(
                    count=NUMBER_OF_POSTS_TO_PULL,
                    start_time=start,
                    end_time=end,
                    include_history="true",
                    sort_by="date",
                    search_term=track,
                    api_token=api_token,
                    platforms="facebook,instagram",
                    lang="en",
                )
                # Returns a list of dictionaries where each dict represents one post.
                # We sort by `date` so the MOST RECENT post will be at the first index.
                posts = results["result"]["posts"]

                # If we get no results, we try a few more times and then break the loop
                num_posts = len(posts)

            except Exception as e:  # 6 calls/minute limit if you request them
                logger.exception(e)
                logger.error(f"Start: {start}")
                logger.error(f"End: {end}")

                # Handle the retries...
                logger.info(f"There are {max_retries-retry_count} retries left.")
                retry_count += 1
                if (max_retries - retry_count) <= 0:
                    break
                else:
                    logger.error("Waiting ten seconds...")
                    time.sleep(10)
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
                        logger.info("Sleeping for 10 seconds...")
                        time.sleep(10)
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

                    # Update the time period we're searching.
                    # ---------------------------------------
                    # Facebook returns data in backwards order, meaning more recent posts are
                    # provided first. If we do not have all data it means that we are missing
                    # OLDER data. So we update the `end` time period (which is the most recent
                    # time parameter) with the oldest/earliest post we find and ensure we do
                    # not pull the same data twice by subtracting by one second to make sure
                    # there is no overlap.
                    # ---------------------------------------
                    oldest_date_dt = datetime.datetime.strptime(
                        oldest_date_str, "%Y-%m-%d %H:%M:%S"
                    )
                    oldest_date_dt = oldest_date_dt - datetime.timedelta(seconds=1)

                # If this is true, we have a bad query. (start_dt is a date object)
                empty_time = datetime.time(0, 0, 0)
                if oldest_date_dt <= datetime.datetime.combine(start_dt, empty_time):
                    logger.info(f"\t|--> end <= start so we have all data.")
                    break

                # More than 500 queries (~5M posts), we break the script.
                query_count += 1
                if query_count > 500:
                    break

                # If all conditionals are passed, we update the date string for query
                end = oldest_date_dt.strftime("%Y-%m-%dT%H:%M:%S")
                logger.info(f"\t|--> New end date: {end}")
                logger.info(f"\t|--> {'-'*50}")

    logger.info("All data downloaded.")
    logger.info("-" * 50)
