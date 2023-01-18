"""
Purpose:
    This script takes a new-line delimited .txt file of keywords as input and
downloads submissions/comments from Reddit that include
the keywords. Only posts from previous day would be collected.
(check params after and before)

Inputs:
    - A single config.ini file that has 1) path to a keywords.txt
    file with one keyword/phrase per line; 2) path to a data directory
    where all posts will be saved.

Output:
    - one new-line delimited json.gz files with all posts from Reddit
 for the previous day.
    Each file will be saved in a directory, indicating the type of posts, which
could be "submission" or "comment". The filename follow the foramt:
     YYYY-MM-DD__{type_of_post}_REDDIT.json.gz
     e.g. YYYY-MM-DD__submission_REDDIT.json.gz

Authors:
    Wanying Zhao, Matthew R. Deverna

"""
import os
import requests
import urllib
import json
import gzip
import argparse
import datetime
import time
from midterm import get_logger, load_config

SCRIPT_PURPOSE = (
    "This script collect posts for previous day, either submissions or comments, from "
    "Reddit using Pushshift. All retrieved posts would be save in one json.gzip file. "
    "Each line is a post in dictionary format."
)
NUMBER_OF_POSTS_TO_PULL = 250
PROJECT_ROOT = "midterm2022"


def parse_ps_args():
    """Set pushshift Arguments."""
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=SCRIPT_PURPOSE)

        # Add optional arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file. ",
            required=True,
        )

        parser.add_argument(
            "-t",
            "--content-type",
            metavar="Content type",
            help="options: submission, comment; submission by default",
            required=False,
        )

        parser.add_argument(
            "-s",
            "--start-date",
            metavar="Start date",
            help="format: YYYY-MM-DD",
            required=False,
        )

        parser.add_argument(
            "-e",
            "--end-date",
            metavar="End date",
            help="format: YYYY-MM-DD",
            required=False,
        )

        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()
        print("Success.")
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)


def ps_get_search_posts(
    content_type="submission",
    count=NUMBER_OF_POSTS_TO_PULL,
    search_terms=None,
    start_date=None,
    end_date=None,
):
    """
    Retrieve a set of submissions/comments for a given parameters using Pushshift
        Args:
            content_type (str, required): The type of content to retrieve, options: ["submission", "comment"]
            count (int, optional): the number of records to return. Defaults is 25. options: [1-250]
            search_term (str, required) : This could be AND or OR operations. e.g. q = radiohead+band; q = radiohead|nirvana

            after (str, optional): restrict the posts returned from a search by epoch time
            before (str, optional): return the posts made before the epoch time; e.g. after = 1d would return posts
                   from yesterday and after=2d before=1d would return posts made the day before yesterday

        Returns:
            [dict]: The Response contains only records. Each record contains a dictionary with all the
            features about a submission/comments
    """

    # API-endpoint
    URL_SUBMISSIONS = "https://api.pushshift.io/reddit/submission/search"
    URL_COMMENTS = "https://api.pushshift.io/reddit/comment/search"
    URL_BASE = URL_SUBMISSIONS

    if content_type == "comment":
        URL_BASE = URL_COMMENTS

    PARAMS = {"q": search_terms, "size": count}

    # Add params parameters
    if start_date:
        PARAMS["after"] = start_date
    if end_date:
        PARAMS["before"] = end_date

    # Sending request and saving the response as json
    PARAMS = urllib.parse.urlencode(PARAMS, quote_via=urllib.parse.quote)
    r = requests.get(url=URL_BASE, params=PARAMS)
    if r.status_code != 200:
        logger.error(f"status: {r}")
    return r.json()


if __name__ == "__main__":
    # Make sure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        raise Exception(
            "All scripts must be run from the root directory of the project!"
        )

    args = parse_ps_args()
    config_file_path = args.config
    project_config = load_config(config_file_path)

    data_folder = project_config["PATHS"]["data_dir_reddit"]
    keywords_file_path = project_config["PATHS"]["keywords_file"]
    logger_dir = project_config["PATHS"]["log_dir_reddit"]

    # ensure the content_type is
    # either submissions or comments
    content_type = args.content_type
    if content_type not in ["submission", "comment"]:
        raise Exception("content_type can only be submission or comment")

    logger_name = f"Reddit_{content_type}.log"
    full_path_logger = os.path.join(logger_dir, logger_name)

    # get logger
    logger = get_logger(logger_dir, full_path_logger, also_print=True)
    logger.info("Start to collect data for Reddit")

    try:
        with open(keywords_file_path, "r") as f:
            search_terms = [f'"{l.rstrip()}"' for l in f.readlines()]
            logger.info("{} search terms found".format(len(search_terms)))
            search_terms = "|".join(search_terms)
    except:
        logger.exception("Problem loading keywords!")
        raise Exception("Problem loading keywords!")

    logger.info("The Query is {}".format(search_terms))

    logger.info("Setting start and end time...")

    # The combine method is utilized to remove the hours, minutes, and seconds
    start = datetime.datetime.combine(
        datetime.datetime.today(), datetime.datetime.min.time()
    ) - datetime.timedelta(days=1)
    utc_start = int(start.timestamp())
    start = start.strftime("%Y-%m-%d")

    end = datetime.datetime.combine(
        datetime.datetime.today(), datetime.datetime.min.time()
    )
    utc_end = int(end.timestamp())
    end = end.strftime("%Y-%m-%d")

    if args.start_date:
        start = args.start_date
        utc_start = int(
            datetime.datetime.combine(
                datetime.datetime.strptime(start, "%Y-%m-%d").date(),
                datetime.datetime.min.time(),
            ).timestamp()
        )

    if args.end_date:
        end = args.end_date
        utc_end = int(
            datetime.datetime.combine(
                datetime.datetime.strptime(end, "%Y-%m-%d").date(),
                datetime.datetime.min.time(),
            ).timestamp()
        )

    logger.info("Collecting data for the period: {} - {}".format(start, end))

    data_folder = os.path.join(data_folder, start)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    logger.info("Data will be saved in :\n\t {}".format(data_folder))

    logger.info("begin collecting data")

    # the filename follows format:
    # "YYYY-MM-DD_{type_of_post}_REDDIT.json.gz"
    fname = f"{start}_{content_type}_REDDIT.json.gz"
    logger.info(f"{content_type} will be saved in file: {fname}")
    full_output_path = os.path.join(data_folder, fname)

    with gzip.open(full_output_path, "wb") as f:

        query_count = 0
        retry_count = 0
        max_retries = 10
        while True:
            try:
                results = ps_get_search_posts(
                    content_type=content_type,
                    search_terms=search_terms,
                    count=NUMBER_OF_POSTS_TO_PULL,
                    start_date=utc_start,
                    end_date=utc_end,
                )
                # Count = 250 only if you request it, otherwise it is 25
                posts = results["data"]

                # If we get no results, we try a few more times and then break the loop
                num_posts = len(posts)

                # wait a bit before next request
                logger.info("Waiting for ten seconds for next request.. ")
                time.sleep(10)

            except Exception as e:
                logger.exception(e)
                logger.error(f"Start: {utc_start}")
                logger.error(f"End: {utc_end}")

                # Handle the retries...
                logger.info(f"There are {max_retries-retry_count} retries left.")
                retry_count += 1
                if (max_retries - retry_count) <= 0:
                    break
                else:
                    logger.error("Waiting for half second.. ")
                    time.sleep(0.5)
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
                        logger.error("Waiting for half second.. ")
                        time.sleep(0.5)
                        logger.info(f"Retrying...")
                        continue

                # If found posts
                else:
                    # Reset the retry count to zero
                    retry_count = 0

                    utc_start_date = posts[0]["created_utc"]
                    utc_last_date = posts[-1]["created_utc"]

                    oldest_date = datetime.datetime.utcfromtimestamp(
                        utc_start_date
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    most_recent_date = datetime.datetime.utcfromtimestamp(
                        utc_last_date
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    logger.info(
                        "collecting data from {} - {} : {} posts".format(
                            oldest_date, most_recent_date, num_posts
                        )
                    )

                    for post in posts:
                        post_in_bytes = f"{json.dumps(post)}\n".encode(encoding="utf-8")
                        f.write(post_in_bytes)

                    # Update the time period for searching
                    # ------------------------------------
                    # Reddit returns posts in forwards order. The tops are the oldest
                    # posts which are right after `utc_start`. If we do not have all data
                    # is means we are missing the RECENT data. Therefore, we update
                    # `utc_start` (which is the starting timestamp) with the most recent posts,
                    #  which is `utc_last_date`. And we ensure no overlap is being pull by
                    # adding one second from `utc_last_date`.

                    utc_start = utc_last_date + 1
                    most_recent_date = datetime.datetime.utcfromtimestamp(
                        utc_last_date
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    logger.info("New start date:{}".format(most_recent_date))

                if utc_start >= utc_end:
                    logger.info("collected all data from start --> end")
                    break

                query_count += 1
                if query_count >= 20_000:
                    break

    logger.info("All data downloaded.")
    logger.info("-" * 50)
