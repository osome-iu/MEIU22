"""
Purpose:
    Count the number of unigrams and bigrams in cleaned posts.

    NOTE: As we know that at least one of our existing keywords must be present
    in the post somewhere, we can simply count the occurrence of ALL unigrams and
    bigrams and this serves as a co-occurence analysis.

Inputs:
    Full path to the file with cleaned posts.

    NOTE: This file must:
        1. Be .parquet pandas dataframe
        2. Contain the columns `clean_text` which contains the clean text that
            you would like to count unigram/bigram for

Outputs:
    - UPDATE ME

Authors:
    Matthew R. DeVerna
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

from nltk.corpus import stopwords
from sklearn.feature_extraction.text import CountVectorizer
from midterm import get_logger, load_config

PROJECT_ROOT = "midterm2022"
SCRIPT_PURPOSE = "Count the number of unigrams and bigrams in cleaned posts."


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

        # Add arguments
        parser.add_argument(
            "-cp",
            "--clean-posts-filepath",
            metavar="Clean posts file",
            help="Full path to the cleaned posts in which you want to count unigrams/bigrams.",
            required=True,
        )

        platform_msg = (
            "For specifying the platform data to clean. Must be one of: "
            "[fb, fb_ads, ig, reddit, tiktok, twitter, twitter_politicians]."
        )
        parser.add_argument(
            "-p",
            "--platform",
            metavar="Platform",
            help=platform_msg,
            required=True,
            choices=[
                "fb",
                "fb_ads",
                "ig",
                "reddit",
                "tiktok",
                "twitter",
                "twitter_politicians",
            ],
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
    clean_posts_fp = args.clean_posts_filepath
    platform = args.platform
    project_config = load_config(config_file_path)
    iteration = args.iteration
    PATHS = project_config["PATHS"]
    working_dir = os.path.join(PATHS["data_dir_intermediate"], "snowball", iteration)

    logger = get_logger(
        log_dir=working_dir,
        full_log_path=os.path.join(working_dir, "log.log"),
        also_print=True
    )

    # Ensure we are in a project folder
    cwd = os.getcwd()
    if os.path.basename(cwd) != PROJECT_ROOT:
        logger.error(f"You not in the PROJECT_ROOT: {PROJECT_ROOT}")
        sys.exit(
            "All scripts must be run from the root directory of the project!"
        )

    # Create a list of strings where each string represents one cleaned post.
    logger.info("Start to load the cleaned text file")
    clean_posts_df = pd.read_parquet(clean_posts_fp)
    if "clean_text" not in clean_posts_df:
        raise Exception("`clean_posts_df` does not contain a 'clean_text' column!")
    list_of_clean_posts = list(clean_posts_df["clean_text"])
    logger.info(f"Loaded {len(list_of_clean_posts):,} cleaned posts")

    # Initialize the CountVectorizer class
    # REF: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html#sklearn.feature_extraction.text.CountVectorizer
    logger.info("Start to vectorize the texts")
    vectorizer = CountVectorizer(
        strip_accents="unicode",
        lowercase=True,
        analyzer="word",
        stop_words=set(stopwords.words("english")),
        ngram_range=(1, 2),  # (min_ngram, max_ngram) -> Consider unigrams and bigrams
    )

    # X is a count matrix where each row represents a document in
    # list_of_clean_posts and each column represents a unigram/bigram
    # extracted by the .fit_transform() method
    X = vectorizer.fit_transform(list_of_clean_posts)

    # The index of each keyword in `keyword_list` == the index of that
    # keyword in the count matrix X
    keyword_list = vectorizer.get_feature_names_out()
    logger.info(f"Extracted {len(keyword_list):,} phrases")

    # So we take the sum along the zero axis and know that the sum
    # of column ii represents the number of times the unigram/bigram
    # in the ii_th position of keyword_list (i.e., keyword_list[ii])
    # represents how many times keyword_list[ii] is in all posts
    logger.info("Start to generate the phrase-count data frame")
    counts_per_feature = np.asarray(X.sum(axis=0))[0, :]

    # Create a label df sorted from most to least counts
    n_gram_df = pd.DataFrame(
        zip(keyword_list, counts_per_feature),
        columns=["phrase", "count"]
        ).sort_values(
            by="count", ascending=False
        ).reset_index(drop=True)

    ### Create output name and save in same place as input file
    input_file_directory = os.path.dirname(clean_posts_fp)
    input_file_basename = os.path.basename(clean_posts_fp)

    # Get date range. Format will be like...
    #  - '%Y-%m-%d--%Y-%m-%d__fb_cleaned_posts.parquet'
    # ... where the first date is the older of the two
    date_range_from_input = input_file_basename.split("__")[0]

    # Create full path and save frame
    logger.info("Start dump the output")
    output_fname = f"{date_range_from_input}__{platform}_ngram_counts.parquet"
    full_output_path = os.path.join(input_file_directory, output_fname)
    n_gram_df.to_parquet(full_output_path)

    logger.info(f"Script {__file__} complete")
    logger.info("-"*50)