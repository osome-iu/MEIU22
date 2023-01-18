# Introduction

Scipts used to collect data from Meta through CrowdTangle.

# [CrowdTangle](https://www.crowdtangle.com/)
"A tool from Meta to help follow, analyze, and report on what’s happening across social media." 

## Helpful links
- [Main documentation repo (see the wiki)](https://github.com/CrowdTangle/API)
- [Documentation for the endpoint we use repo (see the wiki): `searches/posts`](https://github.com/CrowdTangle/API/wiki/Search)

This is Meta's tool that allows users (with an access token provided by Meta) to download posts from groups/pages/accounts that are public. The tool works for Facebook, Instagram, and Reddit.

You can set up an account and then work on the CrowdTangle website (this is actually how they recommend people use it) but it is very hard to automate this process. Instead, Francesco requested and was provided with increased API limits (up to 10k posts). With his key, we can hit the [`posts/search`](https://github.com/CrowdTangle/API/wiki/Search) endpoint which searches posts for specific content. We can also send up to 6 requests per second.

### How the script works
Our script hits the `posts/search` endpoint asking for all posts that match any of the keywords we are interested in between a `start_time` and an `end_time`. We set these time bounds to capture only the previous day and the script continues making this call to the API endpoint until it gets all of the data it wants. Note that this endpoint returns a pagination link to access the next page of data when all of it cannot be returned at once — e.g., if there are more than 10k posts to download from the previous day — **but using pagination information does not work with increased limits and you will get an error.** As a result, we build a while-loop that updates the time bounds repeatedly. 

### Parameter details
The script makes use of a single function with multiple parameters, which are covered in detail in the [`posts/search`](https://github.com/CrowdTangle/API/wiki/Search) endpoint documentation and also in the script's function docstring (`ct_get_search_posts`).
