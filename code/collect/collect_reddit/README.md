# Introduction

Although Reddit has an official API, the Pushshift Reddit dataset and its corresponding API endpoints are much easier to use. 
Therefore, we use Pushshit to collect data from Reddit.


# Endpoints

The official document of the Pushshit Reddit API can be found [here](https://reddit-api.readthedocs.io/en/latest/).
There is also a [dataset paper](https://ojs.aaai.org/index.php/ICWSM/article/view/7347) describing it.

Here we briefly describe them.
Reddit data consists of two major components: comments and submissions.
Their corresponding endpoints are:

| Data type | Endpoint |
|------|------|
| comments  | https://api.pushshift.io/reddit/comment/search |
| submission| https://api.pushshift.io/reddit/submission/search |

These API endpoints are publicly available.

These two endpoints share some important parameters:

| Parameter | Description |
|------|------|
| `size` | Number of posts that are returned within a search. The official document says the range is [1, 500]. But according to our tests, the actual maximum limit is **250**. The default value is 25. |
| `q` | The query. It would return posts matching the keyword or phrase. The value is case-insensitive. With multiple keywords, one could use OR or AND operation to combine them into a phrase. e.g. OR: `q=radiohead\|band`; AND: `q=randiohead+band`. |
| `after` | It restricts the returned posts from a starting timestamp. It could be utc unix, or abbreviations such "24h", "90s", "7d", etc. |
| `before` | It restricts the returned posts before an ending timestamp. The format is the same as `after`. |

Here is an example API query: https://api.pushshift.io/reddit/comment/search/?q=quantum&after=24h&before=1h&size=250

# Data collection script 
Our data collection script can be found at `midterm2022/collect_facebook/pushshift_search.py`

## Functions:
`parse_ps_arg()`: takes args from terminal. Args include:  
 > `-c` : path of config.ini file.
 > `-t` : type of posts to collect. Options include: "submission" or "comment".  
 > `-s` : not required. starting date to collect posts. Format follows: "YYYY-MM-DD".
 > `-e` : not required. ending date to stop collect posts. Format follows: "YYYY-MM-DD".

`ps_get_search_posts()`: this function sends requests based on given parameters, collect posts matching the query, and save data in data directory. 
parameters are:
> `content_type` : str. type of posts to collect. It could be "submission" or "comment".    
> `search_terms` : str. query. It follows format defined in Pushshift api. It can combine multiple keywords using AND or OR operation.     
> `count` : int. It determines the amount of posts to retrieve in a single search. Range from [1, 250].    
> `start_date`: str. It determines the earliest post to collect. A request would return maximum 250 posts after `start_date` util now. Same as 'after' in api.    
> `end_date`: str. It restricts the most recent post to collect. A request would return maximum 250 before `end_date`. Same as 'before' in api.  

standard way to use it under `root` directory:  
` python collect/collect_reddit/pushshift_search.py -c config.ini  -t submission
`   
and it would return posts created in the previous day. 

# Data collection process
1. Once all parameters are given, the script would send a request to Reddit and return at most 250 posts starting from `start_date`. The posts would be saved to `data_dir`. And the file name follows format `start_date_part_{id}.json.gzip`. 
2. Then we set the new `start_date` to the most recent date of the returned posts and ensure adding extra one second to avoid collecting duplicates.
3. With the new `start_date`, the script send a new request to Reddit and return other posts. 
4. And we repeat step 2 and 3 until there is no other posts or `start_date` meets `end_date`.


# Data structure and schema

The data is stored in JSON format.
It should be noted that the `score` in both comments and submissions collected by Pushshift are not accurate. The actual value would be collected using `pmaw`.
The schema is listed below:

## Comment

| Attribute | Note |
|-----------|------|
|`body` | content of the comment |
| `link_id` | the identifier of the submission that the comment is in |
| `id` | the identifier's of the comment |
| `author` | author name|
| `created_utc` | time of creation, in utc unix format |
| `subreddit` | the subreddit the comment belongs to |
| `permalink` | the relative URL for the comment |
| `score` | the number of upvotes minus the number of downvotes received by the comment. To avoid spam bots, Reddit fuzzies the real score of comments |


## Submission

| Attribute | Note |
|-----------|------|
| `selftext` | content of the submission |
| `title` | title of the submission |
| `num_comments` | the number of comments related to the submission |
| `id` | the identifier's of the comment |
| `author` | author name |
| `created_utc` | time of creation, in utc unix format |
| `subreddit` | the subreddit the comment belongs to |
| `permalink` | the relative URL for the comment |
| `score` | the number of upvotes minus the number of downvotes received by the comment. To avoid spam bots, Reddit fuzzies the real score of comments |
