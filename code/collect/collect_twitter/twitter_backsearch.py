"""
Purpose:
    Collect 3,200 tweets from each candidate's timeline.
Inputs:
    - config.ini that contains a `candidates_file_twitter` variable with path to
    user IDs for each candidate
Output:
    .json.gz file with all the tweets data.
"""
import datetime
import gzip
import json
import os
import sys

import tweepy

from tweepy import OAuthHandler
from midterm import load_config, get_logger, parse_config_only_cl_arg

SCRIPT_PURPOSE = "Fetch tweets from midterm candidates timeline"
PROJECT_ROOT = "midterm2022"


if __name__ == "__main__":
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        raise Exception(
            "All scripts must be run from the root directory of the project!"
        )

    # Load and parse the config file
    args = parse_config_only_cl_arg(SCRIPT_PURPOSE)
    config_file_path = args.config
    project_config = load_config(config_file_path)
    PATHS = project_config["PATHS"]
    credentials_file = project_config["CREDENTIALS"]["file_path"]
    TWITTER_CREDS = load_config(credentials_file)["CANDIDATES_TWITTER_CREDS"]

    # Define full path to log file name and create logger named 'log'
    full_log_path = os.path.join(PATHS["log_dir_candidates_twitter"], f"backsearch.log")
    logger = get_logger(
        log_dir=PATHS["log_dir_candidates_twitter"], full_log_path=full_log_path
    )

    # Log start time and directories being used
    logger.info("Begin collecting candidate timeline data")
    logger.info(f"Following config parameters passed:")
    logger.info(f"[*] CANDIDATES_FILE  : {PATHS['candidates_file_twitter']}")
    logger.info(f"[*] DATA_DIRECTORY : {PATHS['data_dir_candidates_twitter']}")
    logger.info(f"[*] LOG_DIRECTORY  : {PATHS['log_dir_candidates_twitter']}")

    # Create data dir if it doesn't exist already
    if not os.path.exists(PATHS["data_dir_candidates_twitter"]):
        os.makedirs(f"{PATHS['data_dir_candidates_twitter']}")
        logger.info("Successfully created data directory...")

    # Set up Tweepy API authorization
    auth = tweepy.OAuthHandler(
        TWITTER_CREDS["api_key"], TWITTER_CREDS["api_key_secret"]
    )
    auth.set_access_token(
        TWITTER_CREDS["access_token"], TWITTER_CREDS["access_token_secret"]
    )
    api = tweepy.API(
        auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, compression=False
    )

    try:
        api.verify_credentials()
        print("Successful Authentication")
    except:
        print("Failed authentication")

    with open(PATHS["candidates_file_twitter"], "r") as f:
        user_ids = [line.rstrip() for line in f]

    today = datetime.datetime.now().strftime("%Y_%m_%d")
    full_file_path = os.path.join(
        PATHS["data_dir_candidates_twitter"],
        f"{today}_candidate_tweets.json.gz",
    )

    logger.info("[*] Beginning collection...")
    with gzip.open(full_file_path, "wb") as f_out:
        for user in user_ids:

            try:
                logger.info(f"Collecting user: {user}")
                tmpTweets = tweepy.Cursor(
                    api.user_timeline,
                    exclude_replies=False,
                    include_rts=True,
                    user_id=user,
                    count=200,
                ).items(3200)

                if tmpTweets:
                    for tweet in tmpTweets:
                        tweet_in_bytes = f"{json.dumps(tweet._json)}\n".encode(
                            encoding="utf-8"
                        )
                        f_out.write(tweet_in_bytes)

            except tweepy.error.TweepError as ex:
                if ex.reason == "Not authorized.":
                    logger.error(f"[*] NOT AUTHORIZED!\n{ex}")
                    sys.exit("")
                else:
                    logger.error(f"[*] Unknown error! Skipping user: {user}\n{ex}")
                    continue

            except Exception as ex:
                logger.error(f"Skipping user due to problem. User: {user}")
                logger.error(f"{ex}")
                continue

    logger.info("[*] Script complete.")
