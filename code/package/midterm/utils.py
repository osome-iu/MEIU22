"""
This script provides some convinient functions for the project.

This script is required by the data collection process, please try NOT add
any third party packages here.

"""
import argparse
import configparser
import datetime
import logging
import os
import sys

############################################################
############################################################
# Utilities
############################################################
def get_dict_val(dictionary: dict, key_list: list = []):
    """
    Return `dictionary` value at the end of the key path provided
    in `key_list`.
    Indicate what value to return based on the key_list provided.
    For example, from left to right, each string in the key_list
    indicates another nested level further down in the dictionary.
    If no value is present, a `None` is returned.
    Parameters:
    ----------
    - dictionary (dict) : the dictionary object to traverse
    - key_list (list) : list of strings indicating what dict_obj
        item to retrieve
    Returns:
    ----------
    - key value (if present) or None (if not present)
    Raises:
    ----------
    - TypeError
    Examples:
    ---------
    # Create dictionary
    dictionary = {
        "a" : 1,
        "b" : {
            "c" : 2,
            "d" : 5
        },
        "e" : {
            "f" : 4,
            "g" : 3
        },
        "h" : 3
    }
    ### 1. Finding an existing value
    # Create key_list
    key_list = ['b', 'c']
    # Execute function
    get_dict_val(dictionary, key_list)
    # Returns
    2
    ~~~
    ### 2. When input key_path doesn't exist
    # Create key_list
    key_list = ['b', 'k']
    # Execute function
    value = get_dict_val(dictionary, key_list)
    # Returns NoneType because the provided path doesn't exist
    type(value)
    NoneType
    """
    if not isinstance(dictionary, dict):
        raise TypeError("`dictionary` must be of type `dict`")

    if not isinstance(key_list, list):
        raise TypeError("`key_list` must be of type `list`")

    retval = dictionary
    for k in key_list:

        # If retval is not a dictionary, we're going too deep
        if not isinstance(retval, dict):
            return None

        if k in retval:
            retval = retval[k]

        else:
            return None
    return retval


def load_keywords(keywords_full_file_path, logger):
    """
    Load keywords file.

    Parameters:
    ----------
    - keywords_full_file_path (str) : full path to keywords.txt file.

    Returns:
    ----------
    - A list : a list of keywords where each element of the list
    corresponds to each line of the keywords.txt file.

    """
    logger.info("Attempting to load filter rules...")

    filter_terms = []

    try:
        with open(keywords_full_file_path, "r") as f:
            for line in f:
                logger.info("Loaded Filter Rule: {}".format(line.strip("\n")))
                filter_terms.append(line.rstrip())

        logger.info("[*] Filter rules loaded succesfully.")
        return filter_terms
    except:
        logger.exception("Problem loading keywords!")
        raise Exception("Problem loading keywords!")


############################################################
############################################################
# Loggers
############################################################
def get_logger(log_dir, full_log_path, also_print=False):
    """Create logger."""

    # Create log_dir if it doesn't exist already
    try:
        os.makedirs(f"{log_dir}")
    except:
        pass

    # Create logger and set level
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)

    # Configure file handler
    formatter = logging.Formatter(
        fmt="%(asctime)s-%(name)s-%(levelname)s-%(message)s",
        datefmt="%Y-%m-%d_%H:%M:%S",
    )
    fh = logging.FileHandler(f"{full_log_path}")
    fh.setFormatter(formatter)
    fh.setLevel(level=logging.INFO)
    # Add handlers to logger
    logger.addHandler(fh)

    # If also_print is true, the logger will also print the output to the
    # console in addition to sending it to the log file
    if also_print:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        ch.setLevel(level=logging.INFO)
        logger.addHandler(ch)

    return logger


def get_logger_print_only():
    """Create print only logger."""

    # Create logger and set level
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)

    # Configure format
    formatter = logging.Formatter(
        fmt="%(asctime)s-%(name)s-%(levelname)s-%(message)s",
        datefmt="%Y-%m-%d_%H:%M:%S",
    )

    # Configure stream handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(level=logging.INFO)
    logger.addHandler(ch)

    return logger


############################################################
############################################################
# Config-file related
############################################################
def parse_config_only_cl_arg(script_purpose):
    """
    Set a single command-line flag (-c and --config). This is intended to be
    used ONLY when you are not using any other command-line flags in your script.
    In that case, you should make something similar to this and add other arguments.

    Parameters:
    -----------
    - script_purpose (str) : this is the script description of your script that
        will print above the command-line flags. Should be unique to each script.
    """
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=script_purpose)

        # Add arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file.",
            required=True,
        )

        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()
        print("Success.")
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)


def parse_config_arg_w_optional_date(script_purpose):
    """
    Set command-line arguments.

    Required:
        -c / --config

    Optional:
        -d / --date (YYYY-MM-DD)

    """
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=script_purpose)

        # Add optional arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file. ",
            required=True,
        )

        parser.add_argument(
            "-d",
            "--date",
            metavar="Date",
            help="The day on which to pull data. Format: YYYY-MM-DD",
            required=False,
        )

        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()
        print("Success.")
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)


def parse_config_arg_w_start_end_dates(script_purpose):
    """
    Set command-line arguments.

    Required:
        -c / --config

    Optional:
        -s / --start_date (YYYY-MM-DD)
        -e / --end_date (YYYY-MM-DD)

    """
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=script_purpose)

        # Add optional arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file. ",
            required=True,
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


def parse_config_arg_w_config_file(script_purpose):
    """
    Set command-line arguments.

    Required:
        -c / --config
        -f / --file

    """
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=script_purpose)

        # Add arguments

        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file. ",
            required=True,
        )

        parser.add_argument(
            "-f",
            "--file",
            metavar="File",
            help="The file name where ids exist",
            required=True,
        )

        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()
        print("Success.")
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)


def parse_config_arg_w_optional_date(script_purpose):
    """
    Set command-line arguments.

    Required:
        -c / --config

    Optional:
        -d / --date (YYYY-MM-DD)

    """
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=script_purpose)

        # Add optional arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file. ",
            required=True,
        )

        parser.add_argument(
            "-d",
            "--date",
            metavar="Date",
            help="The day on which to pull data. Format: YYYY-MM-DD",
            required=False,
        )

        # Read parsed arguments from the command line into "args"
        args = parser.parse_args()
        print("Success.")
        return args

    except Exception as e:
        print("Problem parsing command line input.")
        print(e)


def parse_config_arg_w_start_end_dates(script_purpose):
    """
    Set command-line arguments.

    Required:
        -c / --config

    Optional:
        -s / --start_date (YYYY-MM-DD)
        -e / --end_date (YYYY-MM-DD)

    """
    print("Attempting to parse command line arguments...")

    try:
        # Initialize parser
        parser = argparse.ArgumentParser(description=script_purpose)

        # Add optional arguments
        parser.add_argument(
            "-c",
            "--config",
            metavar="Configuration file",
            help="Full path to the project's config.ini file. ",
            required=True,
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


def load_config(config_file):
    """
    Read a standard python config.ini file (`config_file`) and return a
    configparser object with access to that file's variables.
    """

    # Initialize config parser
    config = configparser.ConfigParser()

    # Read in parameters
    config.read(config_file)

    return config


############################################################
############################################################
# Date-related
############################################################
def get_week_of_dates(most_recent, num_days):
    """
    Return a reverse-ordered list of datetime objects
    between `most_recent` and `most_recent` - `num_days`.
    Parameters:
    ----------
    - most_recent (datetime.date) : will represent the last (most recent) date
        in the returned list of datetime objects
    Returns:
    ----------
    - date_list (list) : reverse ordered date list from `most_recent` to
        `most_recent` - `num_days`
    """
    if not isinstance(most_recent, datetime.date):
        raise TypeError("`most_recent` must be a datetime.date object.")

    date_list = [most_recent - datetime.timedelta(days=x) for x in range(num_days)]
    return date_list


def pprint_today():
    """
    Return today (str) in %Y-%m-%d format.
    """
    current = datetime.datetime.now().strftime("%Y-%m-%d")
    return current
