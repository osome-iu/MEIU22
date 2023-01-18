"""
Purpose:
    Data objects for all platforms.
Authors:
    Kaicheng Yang, Bao Tran Truong
"""
import requests

from cleantext import clean
from urlextract import URLExtract
from datetime import datetime, timezone, timedelta
from .utils import get_dict_val
import pandas as pd
import fnmatch
import os

############################################################
############################################################
# Utilities
############################################################
def clean_text(text):
    """
    A convenience function for cleantext.clean because it has an ugly amount
    of parameters.
    """
    return clean(
        text,
        fix_unicode=True,  # fix various unicode errors
        to_ascii=True,  # transliterate to closest ASCII representation
        lower=True,  # lowercase text
        no_line_breaks=True,  # fully strip line breaks as opposed to only normalizing them
        no_urls=True,  # replace all URLs with a special token
        no_emoji=True,  # remove emojis
        no_emails=True,  # replace all email addresses with a special token
        no_phone_numbers=True,  # replace all phone numbers with a special token
        no_numbers=False,  # replace all numbers with a special token
        no_digits=False,  # replace all digits with a special token
        no_currency_symbols=False,  # replace all currency symbols with a special token
        no_punct=True,  # remove punctuations
        replace_with_punct="",  # instead of removing punctuations you may replace them
        replace_with_url="",
        replace_with_email="",
        replace_with_phone_number="<PHONE>",
        replace_with_number="<NUMBER>",
        replace_with_digit="0",
        replace_with_currency_symbol="<CUR>",
        lang="en",  # set to 'de' for German special handling
    )


def get_available_files_matching_daterange(
    input_dir, file_pattern, start_date=None, end_date=None
):
    """
    Return a dictionary mapping date to a list of file names matching the specified pattern
    Pattern has to include a placeholder "DATE_STR" which will be replaced with the actual date within the (start_date, end_date) range
    If start_date=None and end_date=None, return file whose name contain yesterday's date str

    Parameters:
    ----------
    - input_dir (str): directory to read files from
    - start_date (str): None or date in "%Y-%m-%d" format
    - end_date (str): None or date in "%Y-%m-%d" format
    Returns:
    ----------
    - file_basenames (dict) : {date (str): filenames (list of str)}
    """

    all_file_names = os.listdir(input_dir)

    if start_date is None or end_date is None:
        # if dates not specified, expand yesterday
        yesterday = datetime.now() - timedelta(1)
        yesterday_str = datetime.strftime(yesterday, "%Y-%m-%d")
        start_date = yesterday_str
        end_date = yesterday_str

    date_list = list(pd.date_range(start=start_date, end=end_date))

    if len(date_list) == 0:
        raise ValueError(
            "Date range not valid. Hint: Check that date is in %Y-%m-%d format."
        )

    file_basenames = {}
    for date in date_list:
        date_str = date.strftime("%Y-%m-%d")
        file_name_pattern = file_pattern.replace("DATE_STR", f"{date_str}")
        files_found = fnmatch.filter(all_file_names, file_name_pattern)
        if len(files_found) > 0:
            file_basenames[date_str] = files_found
    return file_basenames


################################################################
################################################################
# Data models
################################################################
class PostBase:
    """
    Base class for social media post.
    Classes for specific platforms can inheret it.
    It defines the common functions that the children classes
    should have.
    """

    def __init__(self, post_object):
        """
        This function initializes the instance by binding the post_object

        Parameters:
            - post_object (dict): the JSON object of the social media post
        """
        if post_object is None:
            raise ValueError("The post object cannot be None")
        self.post_object = post_object

    def is_valid(self):
        """
        Check if the data is valid
        """
        raise NotImplementedError

    def get_value(self, key_list: list = []):
        """
        This is the same as the midterm.get_dict_val() function
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
        """
        return get_dict_val(self.post_object, key_list)

    def extract_hashtag_from_string(self, text):
        """
        Get all hashtags from the post by matching the # symbol in the text
        Code modified to handle chains of #-separated hashtags
        https://stackoverflow.com/questions/2527892/parsing-a-tweet-to-extract-hashtags-into-an-array

        Returns:
            - A list of strings representing the hashtags, # symbols are not included
        """
        hashtags = []
        for part in text.split():
            if part.startswith("#"):
                hashtag_text = part[1:]
                if "#" in hashtag_text:
                    # hashtags might not be space-separated, in which case split by "#"
                    hashtags.extend(
                        [tag for tag in hashtag_text.split("#") if tag != ""]
                    )
                else:
                    hashtags.extend([hashtag_text])
        return hashtags

    def get_timestamp(self):
        """
        Return the post time-of-creation
        """
        raise NotImplementedError

    def get_post_ID(self):
        """
        Return the ID of the post as a string
        """
        raise NotImplementedError

    def get_link_to_post(self):
        """
        Return the link to the post so that one can click it and check
        the post in a web browser
        """
        raise NotImplementedError

    def get_user_ID(self):
        """
        Return the ID of the user as a string
        """
        raise NotImplementedError

    def get_URLs(self):
        """
        Return all URLs (list of dicts) embedded in the social media post
        Each element is a URL dict. Dict keys: {"raw_url", "expanded_url", "domain"}
        """
        raise NotImplementedError

    def get_hashtags(self):
        """
        Return the list of hashtags embedded in the social media post
        """
        raise NotImplementedError

    def get_text(self):
        """
        Return the text of the social media post
        """
        raise NotImplementedError

    def get_media(self):
        """
        Return the media (photo, video, etc.) embedded in the social media post
        """
        raise NotImplementedError

    def __repr__(self):
        """
        Define the representation of the object.
        """
        return f"<{self.__class__.__name__}() object>"


class Tweet(PostBase):
    """
    Class to handle tweet object (V1 API)
    """

    def __init__(self, tweet_object):
        """
        This function initializes the instance by binding the tweet_object

        Parameters:
            - tweet_object (dict): the JSON object of a tweet
        """
        super().__init__(tweet_object)

        self.is_quote = "quoted_status" in self.post_object
        if self.is_quote:
            self.quote_object = Tweet(self.post_object["quoted_status"])

        self.is_retweet = "retweeted_status" in self.post_object
        if self.is_retweet:
            self.retweet_object = Tweet(self.post_object["retweeted_status"])

        self.is_extended = "extended_tweet" in self.post_object
        if self.is_extended:
            self.extended_object = Tweet(self.post_object["extended_tweet"])

    def is_valid(self):
        """
        Check if the tweet object is valid.
        A valid tweet should at least have the following attributes:
            [id_str, user, text, created_at]
        """
        attributes_to_check = ["id_str", "user", "text", "created_at"]
        for attribute in attributes_to_check:
            if attribute not in self.post_object:
                return False
        return True

    def get_timestamp(self):
        """
        Return tweet timestamp (int)
        """
        created_at = self.get_value(["created_at"])
        timestamp = datetime.strptime(
            created_at, "%a %b %d %H:%M:%S +0000 %Y"
        ).timestamp()
        return int(timestamp)

    def get_post_ID(self):
        """
        Return the ID of the tweet (str)
        This is different from the id of the retweeted tweet or
        quoted tweet
        """
        return self.get_value(["id_str"])

    def get_link_to_post(self):
        """
        Return the link to the tweet (str)
        so that one can click it and check the tweet in a web browser
        """
        return f"https://twitter.com/{self.get_user_sreenname()}/status/{self.get_post_ID()}"

    def get_user_ID(self):
        """
        Return the ID of the user (str)
        """
        return self.get_value(["user", "id_str"])

    def get_retweeted_post_ID(self):
        """
        Return the original post ID (str)
        This is retweeted tweet ID for retweet, quoted tweet ID for quote
        """
        if self.is_retweet:
            return self.retweet_object.get_post_ID()
        if self.is_quote:
            return self.quote_object.get_post_ID()
        return None

    def get_retweeted_user_ID(self):
        """
        Return the original user ID (str)
        This is retweeted user ID for retweet, quoted user ID for quote
        """
        if self.is_retweet:
            return self.retweet_object.get_user_ID()
        if self.is_quote:
            return self.quote_object.get_user_ID()
        return None

    def get_user_sreenname(self):
        """
        Return the screen_name of the user (str)
        """
        return self.get_value(["user", "screen_name"])

    def get_text(self, clean=False):
        """
        Extract the tweet text (str)
        It will return the full_text in extended_tweet in its presence

        Parameters:
            - clean (bool, default False):
                If True, return cleaned text (strip stopwords, emojis, URLs, etc. see clean_text() for more details)
                if False, return the raw text
        """

        if self.is_extended:
            text = self.extended_object.get_value(["full_text"])
        else:
            text = self.get_value(["text"])
        if clean:
            text = clean_text(text)
        return text

    def get_URLs(self, recursive=False):
        """
        Get all URLs from tweet, excluding links to the tweet itself.
        All URLs are guaranteed to be in the "entities" field (no need to extract from text)
        Prioritize extraction from "extended_tweet". This attribute always contains the superset of the Tweet payload.

        Parameters:
            - recursive (bool, default False): If True, the function will also
                extract URLs from any embedded quoted_status or retweeted_status
                object; if False, the function will ignore these objects

        Returns:
            - urls (list of str) : A list of URL strings
        """

        urls = []
        if self.is_extended:
            url_objects = self.extended_object.get_value(["entities", "urls"])
        else:
            url_objects = self.get_value(["entities", "urls"])

        if url_objects is not None:
            for item in url_objects:
                expanded_url = get_dict_val(item, ["expanded_url"])
                if (expanded_url is not None) and ("twitter.com" not in expanded_url):
                    url = expanded_url
                else:
                    url = get_dict_val(item, ["url"])
                urls.append(url)

        if recursive:
            # Also collect the URLs from the retweet and quote
            if self.is_retweet:
                urls.extend(self.retweet_object.get_URLs())
            if self.is_quote:
                urls.extend(self.quote_object.get_URLs())

        return urls

    def get_hashtags(self, recursive=False):
        """
        Get all hashtags from the tweet, '#' symbols are excluded.
        They can be found in the "entities" field.

        Parameters:
            - recursive (bool, default True): If True, the function will also
                extract URLs from any embedded quoted_status or retweeted_status
                object; if False, the function will ignore these objects

        Returns:
            - A list of strings representing the hashtags,
        """

        if self.is_extended:  # Prioritize values from "extended_tweet" if exists.
            raw_hashtags = self.extended_object.get_value(["entities", "hashtags"])
        else:
            raw_hashtags = self.get_value(["entities", "hashtags"])
        if raw_hashtags is not None:
            hashtags = [ht["text"] for ht in raw_hashtags]

        if recursive:
            # Also collect the hashtags from the retweet and quote
            if self.is_retweet:
                hashtags.extend(self.retweet_object.get_hashtags())
            if self.is_quote:
                hashtags.extend(self.quote_object.get_hashtags())

        return hashtags

    def get_media(self, recursive=False):
        """
        Get all media from the tweet.
        They can be found in the "extended_entities" field.

        Parameters:
            - recursive (bool, default True): If True, the function will also
                extract media from any embedded quoted_status or retweeted_status
                object; if False, the function will ignore these objects

        Returns:
            - media (list of dicts) : A list of media objects that take the following form:
                {
                    'media_url' : <url_str>,
                    'media_type' : <type_str> # E.g., 'photo', 'video', 'gif'
                }
        """

        # Sometimes the media in the original tweet is included in the retweet or quoting tweet.
        # Keep a set of known_media to avoid adding duplicates.
        known_media = set()
        media = []
        # Entities can be found in multiple places
        # See an example: https://twitter.com/i/web/status/1577811416794513408
        if self.is_extended:  # Prioritize values from "extended_tweet" if exists.
            media_list = self.extended_object.get_value(["extended_entities", "media"])
        else:
            media_list = self.get_value(["extended_entities", "media"])
        if media_list is not None:
            for item in media_list:
                media.append(
                    {"media_url": item["media_url"], "media_type": item["type"]}
                )

        if recursive:
            # Also collect the media from the retweet and quote
            if self.is_retweet:
                for temp_media in self.retweet_object.get_media():
                    media.append(temp_media)

            if self.is_quote:
                for temp_media in self.quote_object.get_media():
                    media.append(temp_media)

        return media

    def __repr__(self):
        """
        Define the representation of the object.
        """
        return "".join(
            [
                f"<{self.__class__.__name__}() object> from @{self.get_user_sreenname()}\n",
                f"Link: {self.get_link_to_post()}",
            ]
        )


class FbIgPost(PostBase):
    """
    Class to handle Facebook/Instagram post obtained from CrowdTangle
    """

    def __init__(self, fb_ig_post):
        """
        This function initializes the instance by binding the fb_ig_post object

        Parameters:
            - fb_ig_post (dict): the JSON object of a post
        """
        super().__init__(fb_ig_post)

    def get_post_ID(self):
        """
        Return the ID of the post as a string.
        """
        post_id = self.get_value(["id"])
        if post_id is None:
            return None
        else:
            return str(post_id)

    def get_link_to_post(self):
        """
        Return the link to the FB/IG post so that one can click it and check
        the post in a web browser
        """
        return self.get_value(["postUrl"])

    def get_platform(self):
        """
        Return the platform of a post. {Facebook, Instagram}
        """
        return self.get_value(["platform"])

    def get_post_type(self):
        """
        Return the type of a post. {status, photo, album, link, live_video_complete, video, native_video, youtube}
        """
        return self.get_value(["type"])

    def convert_to_timestamp(self, date):
        """
        Convert date (str) of format "%Y-%m-%d %H:%M:%S" to timestamp (int)
        """

        return int(
            datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )

    def get_timestamp(self):
        """
        Return post timestamp (int)
        """
        date = self.get_value(["date"])
        if date is not None:
            return self.convert_to_timestamp(date)
        else:
            return None

    def get_update_timestamp(self):
        """
        Return post update timestamp (int)
        """
        date = self.get_value(["updated"])
        if date is not None:
            return self.convert_to_timestamp(date)
        else:
            return None

    def get_user_ID(self):
        """
        Return the ID of the account as a string.
        """
        user_id = self.get_value(["account", "id"])
        if user_id is None:
            return None
        else:
            return str(user_id)

    def get_text(self, clean=False, struct=False):
        """
        Extract the text of the post.
        The text could appear in multiple places:
            message, title, description, imageText

        Parameters:
            - clean (bool, default False): If True, the text will be cleaned;
                if False, return the raw text
            - struct (bool, default False): If True, return a dict;
                if False, return a string (concatenation of all the fields)

        Returns:
            - Depending on the value of struct, a string or a dict is returned.
                - If struct == False, the function will return the concatenation
                    of all text fields indicated above
                - If struct == True, the returned dictionary will contain each
                    field indicated above as a key, and its value will be the
                    text string from that field
        """
        text_obj = {}
        for text_field in ["message", "title", "description", "imageText"]:
            temp_text = self.get_value([text_field])
            if temp_text is not None:
                if clean:
                    temp_text = clean_text(temp_text)
                text_obj[text_field] = temp_text
        if struct:
            return text_obj
        else:
            return " ".join(text_obj.values())

    def get_hashtags(self):
        """
        Get all hashtags in text of the post

        Returns:
            - A list of strings representing the hashtags, # symbols are not included
        """

        text_string = self.get_text()
        return self.extract_hashtag_from_string(text_string)

    def get_URLs(self):
        """
        Get all urls from the post.
        They can be found in the "expandedLinks" field.

        Returns:
            - A list of strings representing the URLs
        """
        urls = []
        expandedUrls = self.get_value(["expandedLinks"])
        if expandedUrls is not None:
            urls = [item["expanded"] for item in expandedUrls]
        return urls

    def get_media(self):
        """
        Get all media from the post.
        They can be found in the "extended_entities" field.

        Returns:
            - media (list of dicts) : A list of media objects that take the following form:
                {
                    'media_url' : <url_str>,
                    'media_type' : <type_str> # E.g., 'photo', 'video', 'gif'
                }
        """
        media = []
        media_list = self.get_value(["media"])
        if media_list is not None:
            for item in media_list:
                media_obj = {"media_url": item["url"], "media_type": item["type"]}
                if "full" in item:
                    media_obj["media_full_url"] = item["full"]
                media.append(media_obj)
        return media

    def __repr__(self):
        """
        Define the representation of the object.
        """
        return "".join(
            [
                f"<{self.__class__.__name__}() object> {self.get_value(['platform'])} post from @{self.get_value(['account', 'handle'])}\n",
                f"Link: {self.get_link_to_post()}",
            ]
        )


class RedditPost(PostBase):
    """
    Base class for Reddit post
    """

    def __init__(self, reddit_post):
        """
        This function initializes the instance by binding the reddit_post object
        """
        super().__init__(reddit_post)

    def get_post_ID(self):
        """
        Return the ID of the post as a string.
        """
        post_id = self.get_value(["id"])
        if post_id is None:
            return None
        else:
            return str(post_id)

    def get_user_ID(self):
        """
        Return the ID of the account as a string.
        """
        user_id = self.get_value(["author_fullname"])
        if user_id is None:
            return None
        else:
            return str(user_id)

    def get_URLs(self):
        extractor = URLExtract()
        urls = list(extractor.gen_urls(self.get_text()))
        return urls

    def __repr__(self):
        """
        Define the representation of the object.
        """
        return "".join(
            [
                f"<{self.__class__.__name__}() object> from @{self.get_value(['author'])}\n",
                f"Link: {self.get_link_to_post()}",
            ]
        )


class RedditSubmission(RedditPost):
    """
    Class to handle Reddit submission obtained from pushshift
    """

    def __init__(self, reddit_submission):
        """
        This function initializes the instance by binding the reddit_submission object

        Parameters:
            - reddit_submission (dict): the JSON object of a submission
        """
        super().__init__(reddit_submission)

    def get_link_to_post(self):
        """
        Return the link to submission so that one can click it and check
        the post in a web browser
        """
        return self.get_value(["full_link"])

    def get_text(self, clean=False, struct=False):
        """
        Extract the text of the submission.
        The text could appear in multiple places:
            title,  selftext

        Parameters:
            - clean (bool, default False): If True, the text will be cleaned;
                if False, return the raw text
            - struct (bool, default False): If True, return a dict;
                if False, return a string (concatenation of all the fields)

        Returns:
            - Depending on the value of struct, a string or a dict is returned.
                - If struct == False, the function will return the concatenation
                    of all text fields indicated above
                - If struct == True, the returned dictionary will contain each
                    field indicated above as a key, and its value will be the
                    text string from that field
        """
        text_obj = {
            "title": self.get_value(["title"]),
            "message": self.get_value(["selftext"]),
        }
        if clean:
            for key, value in text_obj.items():
                text_obj[key] = clean_text(value)
        if struct:
            return text_obj
        else:
            return " ".join(text_obj.values())


class RedditComment(RedditPost):
    """
    Class to handel Reddit comment obtained from pushshift
    """

    def __init__(self, reddit_comment):
        """
        This function initializes the instance by binding the reddit_comment object

        Parameters:
            - reddit_comment (dict): the JSON object of a comment
        """
        super().__init__(reddit_comment)

    def get_link_to_post(self):
        """
        Return the link to comment so that one can click it and check
        the post in a web browser
        """
        return f"https://www.reddit.com{self.get_value(['permalink'])}"

    def get_text(self, clean=False):
        """
        Extract the text of the comment.

        Parameters:
            - clean (bool, default False): If True, the text will be cleaned;
                if False, return the raw text

        Returns:
            - A string of the text
        """
        text = self.get_value(["body"])
        if text is None:
            text = ""
        if clean:
            text = clean_text(text)
        return text


class FourChanThread(PostBase):
    """
    Class to handle 4chan thread.
    It works for original posts and replies.
    """

    def __init__(self, post_object):
        """
        This function initializes the instance by binding the post_object object

        Parameters:
            - post_object: the JSON object of an original post or a reply
        """
        super().__init__(post_object)
        self.is_reply = self.get_value(["resto"]) != 0

    def get_post_ID(self):
        """
        Return the ID of the tweet as a string.
        """
        post_id = self.get_value(["no"])
        if post_id is None:
            return None
        else:
            return str(post_id)

    def get_link_to_post(self):
        """
        Return the link to the thread archive so that one can click it and check
        the post in a web browser.
        """
        if self.is_reply:
            thread_id = f"{self.get_value(['resto'])}#{self.get_post_ID()}"
        else:
            thread_id = self.get_post_ID()
        return f"https://boards.4chan.org/pol/thread/{thread_id}"

    def get_user_ID(self):
        """
        Return the ID of the user as a string.
        Most of the time it's anonymous
        """
        user_id = self.get_value(["name"])
        if user_id is None:
            return None
        else:
            return str(user_id)

    def get_URLs(self):
        """
        Get all urls from the post.

        Returns:
            - A list of strings representing the URLs
        """
        extractor = URLExtract()
        urls = list(extractor.gen_urls(self.get_text()))
        return urls

    def get_text(self, clean=False, struct=False):
        """
        Extract the text of the post.
        For original posts, the text could appear in multiple places:
            subject, comment
        For reply, the text is just in the comment

        Parameters:
            - clean (bool, default False): If True, the text will be cleaned;
                if False, return the raw text
            - struct (bool, default False): If True, return a dict;
                if False, return a string (concatenation of all the fields)

        Returns:
            - Depending on the value of struct, a string or a dict is returned.
                - If struct == False, the function will return the concatenation
                    of all text fields indicated above
                - If struct == True, the returned dictionary will contain each
                    field indicated above as a key, and its value will be the
                    text string from that field
        """
        if self.is_reply:
            # For replies, only comment is present
            text = self.get_value(["com"])
            if text is None:
                text = ""
            if clean:
                text = clean_text(text)
            return text
        else:
            # For original post, text can be found in subject and comment
            text_obj = {}
            for text_field in ["sub", "com"]:
                temp_text = self.get_value([text_field])
                if temp_text is not None:
                    if clean:
                        temp_text = clean_text(temp_text)
                    text_obj[text_field] = temp_text
            if struct:
                return text_obj
            else:
                return " ".join(text_obj.values())

    def get_media(self):
        """
        Get the image from the post.
        An image is required to post an original post, but optional
        for replies.
        The link to the image can be reconstructed using the information
        in the post object.

        Returns:
            - media (list of dicts) : A list of media objects that take the following form:
                {
                    'media_url' : <url_str>,
                    'media_type' : <type_str> # E.g., 'photo'
                }
        """
        tim = self.get_value(["tim"])
        ext = self.get_value(["ext"])
        if tim is not None and ext is not None:
            image_url = f"https://i.4cdn.org/pol/{tim}{ext}"
            return [{"media_url": image_url, "media_type": "photo"}]
        else:
            return []

    def __repr__(self):
        """
        Define the representation of the object.
        """
        return "".join(
            [
                f"<{self.__class__.__name__}() object> @{self.get_user_ID()}\n",
                f"Link: {self.get_link_to_post()}",
            ]
        )


############################################################
############################################################
# CrowdTangle-related
############################################################
def ct_get_lists(api_token=None):
    """
    Retrieve all CrowdTangle lists, saved searches, and saved post lists
        associated with the the input API token.

    Parameters:
    - api_token (str, optional): A valid CrowdTangle API Token. You can locate your API token
        via your Crowdtangle dashboard by clicking the Gear icon in the top right ("Settings")
        and then selecting "API Access".

    Returns:
    response (dict): The response from CrowdTangle which contains both a status code and a result.
        The status will always be 200 if there is no error.
        Inside of `response["result"]["lists"]` is an array of dictionaries, each for an individual
        list in your dashboard.
        One list item looks like the below:
            {
                'id': 34083,                 # The list ID number (int)
                'title': 'US General Media', # Name of list in your dashboard
                'type': 'LIST'               # Options: ["LIST", "SAVED_SEARCH", "SAVED_POST"]
            }
        Example of full response payload: https://github.com/CrowdTangle/API/wiki/lists#response

    Errors:
    - ValueError

    Example:
        ct_get_lists(api_token="AKJHXDFYTGEBKRJ6535")
    """
    if api_token is None:
        raise ValueError("No API token was provided!")

    # api-endpoint
    URL_BASE = "https://api.crowdtangle.com/lists"
    # defining a params dict for the parameters to be sent to the API
    PARAMS = {"token": api_token}

    # sending get request and saving the response as response object
    r = requests.get(url=URL_BASE, params=PARAMS)
    if r.status_code != 200:
        out = r.json()
        print(f"status: {out['status']}")
        print(f"Code error: {out['code']}")
        print(f"Message: {out['message']}")
    return r.json()
