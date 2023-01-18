# Introduction

Here we release the data.

# Facebook candidate posts

See [/facebook_candidate](/facebook_candidate).
We share the IDs of the posts in CSV files with the following schema:

| Column    | Note            |
|-----------|-----------------|
| post_id   | ID of the post  |
| post_url  | URL of the post |

# Facebook and Instagram posts based on keywords

See [/facebook_instagram_keyword](/facebook_instagram_keyword).
We share the IDs of the posts in CSV files with the following schema:

| Column    | Note            |
|-----------|-----------------|
| post_id   | ID of the post  |
| platform  | facebook or instagram |
| post_url  | URL of the post |
| relevant* | 1=related to midterm; 0=irrelevant |

**Post relevance label**: see the paper for details. The procedure is not perfect, use with discretion.

# Reddit submissions and comments based on keywords

See [/reddit_keyword](/reddit_keyword).

We share the data from each day in json files.
Each line of the file is an object.
We add a `relevant` label to each object.

# Candidate tweets

See [/twitter_candidate](/twitter_candidate).
We share the IDs of the tweets in CSV files with the following schema:

| Column    | Note            |
|-----------|-----------------|
| tid       | ID of the tweet |

# Tweets based on keywords

See [/twitter_keyword](/twitter_keyword).
We share the IDs of the tweets in CSV files with the following schema:

| Column    | Note            |
|-----------|-----------------|
| tid       | ID of the tweet |
| relevant* | 1=related to midterm; 0=irrelevant |

**Post relevance label**: see the paper for details. The procedure is not perfect, use with discretion.

# Facebook ads

See `facebook_ads_ids.csv.gz `.
We share the IDs of the ads in CSV files with the following schema:

| Column    | Note            |
|-----------|-----------------|
| id        | ID of the ad |


# 4chan data

Since the 4chan data is too large for GitHub, we host it on [zenodo](https://doi.org/10.5281/zenodo.7546057).

For the archive files, each line is a thread.
For the snapshot files, each line is a json object containing the snapshots of 4chan's `catalog` endpoint.



