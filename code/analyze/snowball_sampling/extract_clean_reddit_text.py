"""
Purpose:
    Clean Reddit submission and comments from the given time period and return clean posts.

Inputs:
    - Project config.ini file with variable that points to the Meta posts data
    - Index of the interation
    - Start date of the time period
    - End date of the time period

Outputs:
    - A .parquet file that contain the following columns:

        - author: author name
        - author_fullname: author id
        - score : upvote - downvote
        - upvote ratio : the ratio of upvote
        - robot: robot indexable
        - subreddit: the name of the subreddit
        - url : url of the post
        - raw_text_field: the type of the raw_text: title or body or comment
        - raw_text : raw text body
        - clean_text: cleaned text body

Authors:
    Adopted from extract_clean_fb_ig_text.py Matthew R. Deverna,
    later adjusted for Reddit by Munjung Kim and Kaicheng Yang

"""

import argparse
import gzip
import json
import os
import sys
import pandas as pd

from midterm import load_config, get_logger, get_dict_val
from midterm.data import clean_text

SCRIPT_PURPOSE = (
    "Clean reddit posts from the given time period. "
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
    data_dir = PATHS["data_dir_reddit"]
    working_dir = os.path.join(PATHS["data_dir_intermediate"], "snowball", iteration)

    logger = get_logger(
        log_dir=working_dir,
        full_log_path=os.path.join(working_dir, "log.log"),
        also_print=True
    )
    logger.info("Reddit: extract clean submissions and comments")

    # Ensure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        logger.error(f"You not in the PROJECT_ROOT: {PROJECT_ROOT}")
        sys.exit(
            "All scripts must be run from the root directory of the project!"
        )

    # Ensure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        raise Exception(
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

    data_file_basenames = [
        f"{date.strftime('%Y-%m-%d')}/{date.strftime('%Y-%m-%d')}_comment_REDDIT.json.gz" for date in date_list
    ]
    data_file_basenames.extend([
        f"{date.strftime('%Y-%m-%d')}/{date.strftime('%Y-%m-%d')}_submission_REDDIT.json.gz" for date in date_list
    ])
    data_full_paths = [
        os.path.join(data_dir, basename) for basename in data_file_basenames
    ]

    logger.info("Begin extracting posts to be cleaned...")
    post_list = []

    for file in data_full_paths:
        logger.info(f"Working on {file}:")

        if not os.path.exists(file):
            logger.info(f"Skipping... \n\t {file} \n\t ...does not exist!")
            continue

        with gzip.open(file, "rb") as f:
            for line in f:

                # Convert post back into a dictionary
                post = json.loads(line.decode("utf-8"))


                if "comment" in file:
                    post_id = get_dict_val(post,["id"])
                    author = get_dict_val(post, ["author"])
                    author_fullname = get_dict_val(post,['author_fullname'])
                    score = get_dict_val(post,['score'])
                    subreddit = get_dict_val(post,['subreddit'])
                    url = get_dict_val(post,['permalink'])
                    raw_text = get_dict_val(post,['body'])
                    upvote_ratio = None
                    robot = None

                    post_list.append((
                        post_id,
                        author,
                        author_fullname,
                        score,
                        upvote_ratio,
                        robot,
                        subreddit,
                        url,
                        'comment',
                        raw_text
                        ))

                elif "submission" in file:
                    post_id = get_dict_val(post,["id"])
                    author = get_dict_val(post,['author'])
                    author_fullname = get_dict_val(post,['author_fullname'])
                    score = get_dict_val(post,['score'])
                    upvote_ratio = get_dict_val(post,['upvote_ratio'])
                    robot = get_dict_val(post,['is_robot_indexable'])
                    subreddit = get_dict_val(post,['subreddit'])
                    url = get_dict_val(post,['permalink'])
                    raw_title_text = get_dict_val(post,['title'])
                    raw_text =get_dict_val(post,['selftext'])

                    post_list.append((
                        post_id,
                        author,
                        author_fullname,
                        score,
                        upvote_ratio,
                        robot,
                        subreddit,
                        url,
                        'title',
                        raw_title_text
                        ))

                    post_list.append((
                        post_id,
                        author,
                        author_fullname,
                        score,
                        upvote_ratio,
                        robot,
                        subreddit,
                        url,
                        'body',
                        raw_text
                        ))


    min_date_dt = min(date_list)
    max_date_dt = max(date_list)
    min_date_str = min_date_dt.strftime("%Y-%m-%d")
    max_date_str = max_date_dt.strftime("%Y-%m-%d")
    num_posts = len(post_list)

    logger.info(
        f"Number of posts to clean between {min_date_str} and {max_date_str}:\n"
        f"\t - Reddit     : {num_posts}\n"
    )

    logger.info("Cleaning posts...")
    submission_df = pd.DataFrame(
        post_list,
        columns=[
            "id",
            "author",
            "author_fullname",
            "score",
            "upvote_ratio",
            "robot",
            "subreddit",
            "url",
            "raw_text_field",
            "raw_text"
        ],
    )

    submission_df["clean_text"] = submission_df.raw_text.map(clean_text)

    # This captures the scenario when a single post has an exact duplicate of
    # text across multiple text fields fields (e.g., message, description, etc.).
    logger.info("Removing any potential exact matches...")
    submission_df = submission_df.drop_duplicates(
        subset=["id", "raw_text"]
    ).reset_index(drop=True)

    # Create output paths for each file
    date_range_str = f"{min_date_str}--{max_date_str}"
    submission_output_basename = f"{date_range_str}__reddit_cleaned_posts.parquet"
    sub_full_outname = os.path.join(working_dir, submission_output_basename)

    logger.info(
        f"Saving data here:\n"
        f"\t - clean text : {sub_full_outname}\n"
    )
    submission_df.to_parquet(sub_full_outname)

    logger.info(f"Script {__file__} complete")
    logger.info("-"*50)