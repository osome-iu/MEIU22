"""
Purpose:
    Extract the most frequent unigrams and bigrams from the collected data

Inputs:
    - Project config.ini file with variable that points to the Meta posts data
    - Index of the interation
    - Start date of the time period
    - End date of the time period

Outputs:
    - A CSV file containing the top 50 most frequent unigrams and top 50 most frequent bigrams from different platforms. Those already in the keyword list are excluded.

Authors:
    Kaicheng Yang
"""
import argparse
import os
import sys
import pandas as pd
from midterm import get_logger, load_config

PROJECT_ROOT = "midterm2022"
SCRIPT_PURPOSE = "Extract the most frequent unigrams and bigrams from the collected data"

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
    working_dir = os.path.join(PATHS["data_dir_intermediate"], "snowball", iteration)
    keyword_path = PATHS['keywords_file']

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

    logger.info("Start to extract top grams")
    start_date = args.start_date
    end_date = args.end_date
    ngram_count_dfs = []
    # Load the phrases count from different platforms
    for platform in ['ig', 'fb', 'reddit', 'twitter']:
        logger.info(f"Loading data from {platform}")
        file_path = os.path.join(
            working_dir,
            f"{start_date}--{end_date}__{platform}_ngram_counts.parquet"
        )
        temp_df = pd.read_parquet(file_path)
        temp_df['platform'] = platform
        ngram_count_dfs.append(temp_df)

    logger.info("Start the extraction...")
    ngram_count_df = pd.concat(ngram_count_dfs)
    keywords = pd.read_csv(keyword_path, names=['keyword'])
    # Exclude those already in the keyword list
    keywords_set = set(keywords.keyword)
    new_ngram_count_df = ngram_count_df[~ngram_count_df.phrase.isin(keywords_set)].copy()
    # Seperate the unigrams and bigrams
    new_ngram_count_df['is_bigram'] = new_ngram_count_df.phrase.apply(lambda x: " " in x)
    # Identify the top 50 most frequent phrases
    top_bigram_df = new_ngram_count_df.query('is_bigram').sort_values(
        by=['platform', 'count'], ascending=False
    ).groupby('platform').head(50)
    top_unigram_df = new_ngram_count_df.query('not is_bigram').sort_values(
        by=['platform', 'count'], ascending=False
    ).groupby('platform').head(50)
    top_gram_df = pd.concat([top_bigram_df, top_unigram_df])

    output_path = os.path.join(working_dir, f"top_grams_{iteration}.csv")
    logger.info(f"Dump the result to: {output_path}")
    top_gram_df.to_csv(output_path, index=None)

    logger.info(f"Script {__file__} complete")
    logger.info("-"*50)