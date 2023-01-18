"""
Purpose:
    Clean Twitter posts from the given time period and return clean posts.

Inputs:
    - Project config.ini file with variable that points to the Twitter data
    - Index of the interation
    - Start date of the time period
    - End date of the time period

Outputs:
    All str type
    - One .parquet files that contain the following columns:
        - tweet_id : The tweet id_str of the tweet
        - retweeted_id : If retweet, then this returns the tweet id_str of the original tweet. Returns empty string if not a retweet.
        - raw_text : Full text of the tweet.
        - clean_text: the cleaned version of raw_text.

Authors:
   Rachith Aiyappa, Kaicheng Yang
"""
import argparse
import gzip
import json
import os
import sys
import fnmatch
import pandas as pd

from midterm import load_config, get_logger
from midterm.data import clean_text, Tweet

SCRIPT_PURPOSE = (
    "Clean Twitter posts from the given time period. "
)
PROJECT_ROOT = "midterm2022"

def parse_cl_args():
    """Set CLI Arguments."""
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=SCRIPT_PURPOSE)

        # Add arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file.",
            required=True,
        )

        parser.add_argument(
            "-i",
            "--iteration",
            metavar="Index of the iteration",
            help="Index of the iteration, also used as folder name",
            required=True,
        )

        parser.add_argument(
            "-sd",
            "--start_date",
            metavar="Date",
            help="The start date of the snowball. Format: YYYY-MM-DD",
            required=True,
        )

        parser.add_argument(
            "-ed",
            "--end_date",
            metavar="Date",
            help="The end date of the snowball. Format: YYYY-MM-DD",
            required=True,
        )

        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()
        print("Success.")
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)


if __name__ == "__main__":
    # Load and parse the config file
    args = parse_cl_args()
    config_file_path = args.config
    project_config = load_config(config_file_path)
    iteration = args.iteration
    PATHS = project_config["PATHS"]
    data_dir = os.path.join(PATHS["data_dir_intermediate"], "cleaned_raw_data", "twitter")
    working_dir = os.path.join(PATHS["data_dir_intermediate"], "snowball", iteration)

    logger = get_logger(
        log_dir=working_dir,
        full_log_path=os.path.join(working_dir, "log.log"),
        also_print=True
    )
    logger.info("Twitter: extract clean tweets")

    # Ensure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        logger.error(f"You not in the PROJECT_ROOT: {PROJECT_ROOT}")
        sys.exit(
            "All scripts must be run from the root directory of the project!"
        )

    # Log directories being used
    logger.info(f"Following config parameters passed:")
    logger.info(f"[*] Working directory: {working_dir}")


    # Create a list of formatted date-containing filenames for the given time range
    # that matches the format of the data created by `twitter-streamer-V1.py`
    start_date = args.start_date
    end_date = args.end_date
    date_list = list(pd.date_range(start=start_date, end=end_date))
    if len(date_list) == 0:
        logger.error("Date range not valid")
        sys.exit("Date range not valid")

    all_file_names = os.listdir(data_dir)
    data_file_basenames = []
    for date in date_list:
        # Match the data files with suffix such as --1 and --2
        file_name_pattern = f"streaming_data--{date.strftime('%Y-%m-%d')}*.json.gz"
        data_file_basenames.extend(fnmatch.filter(all_file_names, file_name_pattern))

    data_full_paths = [
        os.path.join(data_dir, basename) for basename in data_file_basenames
    ]
    logger.info("Begin extracting posts to be cleaned...")
    twitter_raw_text = []  # stores either raw full text or the quoted/retweeted text
    is_quote_tweet = []  # stores True or False where True means the
    tweet_id = []  # tweet id_str of the tweet
    retweeted_id = [] # if retweet, tweet id_str of the tweet it is retweeting. If not, stores empty string.

    for file in data_full_paths:
        logger.info(f"Working on {file}:")

        if not os.path.exists(file):
            logger.info(f"Skipping... \n\t {file} \n\t ...does not exist!")
            continue
        try:
            with gzip.open(file, "rb") as f:
                for line in f:

                    # Convert post back into a dictionary
                    post = json.loads(line.decode("utf-8"))
                    # Initialize the Tweet object
                    tweet = Tweet(post)
                    if not tweet.is_valid():
                        continue

                    # Get full text
                    # 1. If it is a retweet, get text from retweeted_status object either via extended tweet's full text or just the text.
                    # 2. Consider the case C retweets B who in turn has quote tweeted A.
                    #    If we are reading C's tweet objects, in this first if block, A's text is NOT captured.
                    #    Just B's text is captured.
                    # .  In simple terms: we just check one level deep
                    # None of the belows conditional blocks capture A's text in such a case.
                    if tweet.is_retweet:
                        retweeted_id.append(tweet.retweet_object.get_post_ID())
                        tweet_id.append(tweet.get_post_ID())
                        twitter_raw_text.append(tweet.retweet_object.get_text())
                        # to keep dimensions of dataframe lists consistent since quoted text is not present.
                        is_quote_tweet.append(False)

                    # If it is a quoted_tweet, extract the information from the quote
                    # And add the information for the tweet as well
                    if tweet.is_quote:
                        retweeted_id.append(tweet.quote_object.get_post_ID())
                        tweet_id.append(tweet.get_post_ID())
                        twitter_raw_text.append(tweet.quote_object.get_text())
                        is_quote_tweet.append(True)

                        retweeted_id.append(None)
                        tweet_id.append(tweet.get_post_ID())
                        twitter_raw_text.append(tweet.get_text())
                        is_quote_tweet.append(False)

                    # If it is not a retweet nor a quote tweet, search if extended tweet exists or not to grab the full text from
                    if not (tweet.is_retweet or tweet.is_quote):
                        retweeted_id.append(None)
                        tweet_id.append(tweet.get_post_ID())
                        twitter_raw_text.append(tweet.get_text())
                        is_quote_tweet.append(False)




        except Exception as e:
            logger.info(f"File name which FAILED to parse : {file}")
            logger.exception(e)
            raise Exception("Problem reading and parsing twitter data")

    twitter_df = pd.DataFrame()
    twitter_df["tweet_id"] = tweet_id
    twitter_df["retweeted_id"] = retweeted_id
    twitter_df["raw_text"] = twitter_raw_text
    twitter_df["is_quote_tweet"] = is_quote_tweet

    min_date_dt = min(date_list)
    max_date_dt = max(date_list)
    min_date_str = min_date_dt.strftime("%Y-%m-%d")
    max_date_str = max_date_dt.strftime("%Y-%m-%d")

    logger.info(
        f"Number of posts to clean between {min_date_str} and {max_date_str}:\n"
        f"\t - Twitter : {len(twitter_raw_text):,}\n"
    )

    logger.info("Cleaning Twitter posts...")

    twitter_df["clean_text"] = twitter_df.raw_text.map(clean_text)

    # This captures the scenario when a single post has an exact duplicate
    # Ideally, this should not happen.
    logger.info("Removing any potential exact matches...")
    twitter_df = twitter_df.drop_duplicates(
        subset=["tweet_id", "retweeted_id", "raw_text", "is_quote_tweet"]
    ).reset_index(drop=True)

    # Create output paths for each file
    date_range_str = f"{min_date_str}--{max_date_str}"
    twitter_output_basename = f"{date_range_str}__twitter_cleaned_posts.parquet"
    twitter_full_outname = os.path.join(working_dir, twitter_output_basename)

    logger.info(f"Saving data here:\n")
    logger.info(f"\t - Twitter clean text : {twitter_full_outname}\n")

    twitter_df.to_parquet(twitter_full_outname)

    logger.info(f"Script {__file__} complete")
    logger.info("-"*50)