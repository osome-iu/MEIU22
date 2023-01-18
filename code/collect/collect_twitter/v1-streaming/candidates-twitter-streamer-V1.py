#!/usr/bin/env python3

"""
PURPOSE:
    - To create a real-time FILTERED stream of Twitter
    data, utilizing the Twitter V1 API.

INPUT:
    - A file with midterm candidate's twitter ID (one per line) that
    will be utilized as the filters to follow tweets in real-time.

OUTPUT:
    - One JSON file is created - per day - for all candidates where each
    line item represents one tweet object.

DEPENDENCIES:
    - Tweepy (https://www.tweepy.org/)

Author: Matthew R. DeVerna, Rachith Aiyappa and Zoher Kachwala
"""

# Import packages
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os
import sys
import time
from datetime import datetime as dt
import gzip

# Dependencies
from tweepy import OAuthHandler, Stream, StreamListener
from midterm import parse_config_only_cl_arg, load_config, get_logger, load_keywords

PROJECT_ROOT = "midterm2022"
SCRIPT_PURPOSE = (
    "This script takes a single config.ini file as input. It then reads a new-line "
    "delimited file of candidate's twitter IDs to stream tweets from Twitter."
)

# Build Functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Listener(StreamListener):
    """
    The Listener wraps tweepys StreamListener allowing customizable handling
    of tweets and errors received from the stream.

    This Listener does the following:
        - Writes raw tweet data to a file named for the day it is scraped.
    """

    def __init__(self, logger):
        self.logger = logger
        self.output_file = None
        self.output_day = ""
        self.file_version = None

    def get_file_version(self, today):
        """
        Identify a file version to output data
        """
        # Default version is 1
        counter = 1
        self.file_version = counter
        self.output_day = today

        # We now increment file version by one until we find the proper version,
        # but only if the file already exists
        full_file_path = os.path.join(
            PATHS["data_dir_candidates_twitter"],
            f"candidates_streaming_data--{today}--{self.file_version}.json.gz",
        )
        while os.path.isfile(full_file_path):
            counter += 1
            full_file_path = os.path.join(
                PATHS["data_dir_candidates_twitter"],
                f"candidates_streaming_data--{today}--{counter}.json.gz",
            )
        logger.info(f"Creating a new file for the fresh run: {full_file_path}")
        self.file_version = counter

    def get_output_file(self, today):
        # Handles new days
        if self.output_day != today:
            logger.info(f"Creating a new file for the new day: {today}")
            self.file_version = 1

        # Creates the proper version of the file based on the new day or what
        # was found via get_file_version()
        full_file_path = os.path.join(
            PATHS["data_dir_candidates_twitter"],
            f"candidates_streaming_data--{today}--{self.file_version}.json.gz",
        )

        # Open and return the gzip file
        self.output_file = gzip.open(full_file_path, "ab")
        return self.output_file

    def on_data(self, data):
        """Do this when we get data."""

        today = dt.strftime(dt.now(), "%Y-%m-%d")

        try:
            # self.file_version initializes to None so this is only called
            # when the script is started for the first time
            if self.file_version is None:
                logger.info("Getting file version...")
                self.get_file_version(today)
                logger.info(f"File version is: {self.file_version}")
        except Exception as e:
            logger.error(f"Error getting file version: {e}", exc_info=True)

        # Write data
        try:
            f = self.get_output_file(today)
            f.write(bytes(data, encoding="utf-8"))
        except Exception as e:
            logger.error("Error: " + str(e), exc_info=True)

        return True

    def on_error(self, status_code):
        """Do this if we get an error."""

        # Log error with exception info
        logger.error(f"Error, code {status_code}", exc_info=True)
        if status_code == 420:
            # Rate limit hit

            # Wait five minutes
            logger.info("Rate limit reached. Sleeping for five minutes.")
            time.sleep(300)
            return True

        elif status_code == 503:
            # Twitter Service Unavailable

            # Wait 60 seconds and retry
            # Connection retry limits are 5 connection attempts per 5 min
            # https://developer.twitter.com/en/docs/twitter-api/tweets/filtered-stream/migrate
            logger.info("Twitter service unavailable. Sleeping for one minute.")
            time.sleep(60)
            return True

        else:
            return True


# Execute main program.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    # Make sure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        raise Exception(
            "All scripts must be run from the root directory of the project!"
        )
    # Get current time
    start_time = dt.strftime(dt.now(), "%Y-%m-%d_%H-%M-%S")

    # Parse command line arguments
    # Load and parse the config file
    args = parse_config_only_cl_arg("A V1 Twitter Candidate Streamer Script")
    config_file_path = args.config
    project_config = load_config(config_file_path)
    PATHS = project_config["PATHS"]

    # Load the necessary credentials for Twitter Stream
    credentials_file = project_config["CREDENTIALS"]["file_path"]
    TWITTER_CREDS = load_config(credentials_file)["CANDIDATES_TWITTER_CREDS"]

    # Define full path to log file name and create logger named 'log'
    full_log_path = os.path.join(
        PATHS["log_dir_candidates_twitter"], f"{start_time}_stream.log"
    )
    logger = get_logger(
        log_dir=PATHS["log_dir_candidates_twitter"], full_log_path=full_log_path
    )

    # Log start time and directories being used
    logger.info(f"Script started {start_time}")
    logger.info(f"Following config parameters passed:")
    logger.info(f"[*] CANDIDATES_FILE  : {PATHS['candidates_file_twitter']}")
    logger.info(f"[*] DATA_DIRECTORY : {PATHS['data_dir_candidates_twitter']}")
    logger.info(f"[*] LOG_DIRECTORY  : {PATHS['log_dir_candidates_twitter']}")

    # Create data dir if it doesn't exist already
    try:
        os.makedirs(f"{PATHS['data_dir_candidates_twitter']}")
        logger.info("Successfully created data directory...")
    except Exception as e:
        logger.info(e)
        pass

    # Load file terms...
    filter_candidates = load_keywords(PATHS["candidates_file_twitter"], logger)

    # Set up the stream.
    logger.info("Intializing the stream...")
    listener = Listener(logger)
    auth = OAuthHandler(TWITTER_CREDS["api_key"], TWITTER_CREDS["api_key_secret"])
    auth.set_access_token(
        TWITTER_CREDS["access_token"], TWITTER_CREDS["access_token_secret"]
    )
    stream = Stream(auth, listener)
    logger.info("[*] Stream initialized succesfully.")

    # Begin the stream.
    logger.info("[*] Beginning stream...")
    while True:
        try:
            stream.filter(follow=filter_candidates)
        except KeyboardInterrupt:
            logger.info("User manually ended stream with a Keyboard Interruption.")
            sys.exit("\n\nUser manually ended stream with a Keyboard Interruption.\n\n")
        except Exception as e:
            logger.info(f"Unexpected exception: {e}")
            continue
