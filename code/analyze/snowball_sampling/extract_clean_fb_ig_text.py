"""
Purpose:
    Clean Facebook and Instagram posts from the given time period and return clean posts.

Inputs:
    - Project config.ini file with variable that points to the Meta posts data
    - Index of the interation
    - Start date of the time period
    - End date of the time period

Outputs:
    - Two .parquet files (one for each platform) that contain the following columns:
        - crowdtangle_id: unique identified for the CT platform
        - platform: "Facebook" or "Instagram"
        - post_type: one of a handful, depends on the platform
        - raw_text_field: some post types can have multiple text fields
            see CROWDTANGLE_TEXT_FIELDS below for options
        - raw_text: the raw text that was found within the raw_text_field
        - clean_text: the cleaned version of raw_text

Authors:
    Matthew R. DeVerna, Kaicheng Yang
"""
import argparse
import gzip
import json
import os
import sys
import pandas as pd

from midterm import load_config, get_logger
from midterm.data import clean_text, FbIgPost

SCRIPT_PURPOSE = (
    "Clean Facebook and Instagram posts from the given time period. "
)
PROJECT_ROOT = "midterm2022"
CROWDTANGLE_TEXT_FIELDS = ["message", "title", "description", "imageText"]


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
    data_dir = PATHS["data_dir_meta"]
    working_dir = os.path.join(PATHS["data_dir_intermediate"], "snowball", iteration)

    logger = get_logger(
        log_dir=working_dir,
        full_log_path=os.path.join(working_dir, "log.log"),
        also_print=True
    )
    logger.info("Facebook/Instagram: extract clean posts")

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

    data_file_basenames = [
        f"{date.strftime('%Y-%m-%d')}__posts_FB_IG.json.gz" for date in date_list
    ]
    data_full_paths = [
        os.path.join(data_dir, basename) for basename in data_file_basenames
    ]

    logger.info("Begin extracting posts to be cleaned...")
    fb_posts = []
    ig_posts = []
    unclassified_posts = []

    for file in data_full_paths:
        logger.info(f"Working on {file}:")

        if not os.path.exists(file):
            logger.info(f"Skipping... \n\t {file} \n\t ...does not exist!")
            continue

        with gzip.open(file, "rb") as f:
            for line in f:

                # Convert post back into a dictionary
                post_json = json.loads(line.decode("utf-8"))
                # Initialize the FbIgPost object
                post = FbIgPost(post_json)

                # Get important identification information (always present)
                platform = post.get_value(["platform"])
                post_id = post.get_post_ID()
                post_type = post.get_value(["type"])
                post_url = post.get_value(["postUrl"])

                text_obj = post.get_text(struct=True)
                for field, text in text_obj.items():
                    # If we have no text, we skip this field.
                    # We do this because certain text fields
                    # are only present for certain types of posts.
                    if text is None:
                        continue

                    if platform == "Facebook":
                        fb_posts.append(
                            (post_id, platform, post_type, post_url, field, text)
                        )

                    elif platform == "Instagram":
                        ig_posts.append(
                            (post_id, platform, post_type, post_url, field, text)
                        )

                    else:
                        unclassified_posts.append(
                            (post_id, platform, post_type, field, post_url, text, file)
                        )

    # If there are weird posts, we save them to check later
    if len(unclassified_posts) > 0:
        logger.error(f"Error! There are {len(unclassified_posts):,} unclassified posts!!")
        cwd = os.getcwd()
        logger.info(f"Saving these posts here:\n\t {cwd}/unclassified_posts.csv")
        unclassified_posts_df = pd.DataFrame(
            unclassified_posts,
            columns=["post_id", "platform", "post_type", "field", "text", "file_path"],
        )
        unclassified_posts_df.to_csv("unclassified_posts.csv", index=False)

    else:
        logger.info("There are no unclassified posts.")

    min_date_dt = min(date_list)
    max_date_dt = max(date_list)
    min_date_str = min_date_dt.strftime("%Y-%m-%d")
    max_date_str = max_date_dt.strftime("%Y-%m-%d")
    num_fb_posts = len(fb_posts)
    num_ig_posts = len(ig_posts)

    logger.info(
        f"Number of posts to clean between {min_date_str} and {max_date_str}:\n"
        f"\t - Facebook : {num_fb_posts:,}\n"
        f"\t - Instagram: {num_ig_posts:,}\n"
        f"\t - Total    : {num_fb_posts + num_ig_posts:,}\n"
    )

    logger.info("Cleaning Facebook posts...")
    facebook_df = pd.DataFrame(
        fb_posts,
        columns=[
            "crowdtangle_id",
            "platform",
            "post_type",
            "post_url",
            "raw_text_field",
            "raw_text",
        ],
    )
    facebook_df["clean_text"] = facebook_df.raw_text.map(clean_text)

    logger.info("Cleaning Instagram posts...")
    instagram_df = pd.DataFrame(
        ig_posts,
        columns=[
            "crowdtangle_id",
            "platform",
            "post_type",
            "post_url",
            "raw_text_field",
            "raw_text",
        ],
    )
    instagram_df["clean_text"] = instagram_df.raw_text.map(clean_text)

    # This captures the scenario when a single post has an exact duplicate of
    # text across multiple text fields fields (e.g., message, description, etc.).
    logger.info("Removing any potential exact matches...")
    facebook_df = facebook_df.drop_duplicates(
        subset=["crowdtangle_id", "raw_text"]
    ).reset_index(drop=True)
    instagram_df = instagram_df.drop_duplicates(
        subset=["crowdtangle_id", "raw_text"]
    ).reset_index(drop=True)

    # Create output paths for each file
    date_range_str = f"{min_date_str}--{max_date_str}"
    fb_output_basename = f"{date_range_str}__fb_cleaned_posts.parquet"
    ig_output_basename = f"{date_range_str}__ig_cleaned_posts.parquet"
    fb_full_outname = os.path.join(working_dir, fb_output_basename)
    ig_full_outname = os.path.join(working_dir, ig_output_basename)

    logger.info(
        f"Saving data here:\n"
        f"\t - Facebook clean text : {fb_full_outname}\n"
        f"\t - Instagram clean text: {ig_full_outname}"
    )
    facebook_df.to_parquet(fb_full_outname)
    instagram_df.to_parquet(ig_full_outname)

    logger.info(f"Script {__file__} complete")
    logger.info("-"*50)