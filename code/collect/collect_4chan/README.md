# Introduction

Scipts used to collect data from 4chan.

# About 4chan

## Basic concepts
4chan is an image-based bulletin board where users or original posters can create a thread by posting an image (required for original post) and a message to a board.
Others can reply to the original post thread with a message and image (not required).
Each original post and all its replies make up a thread.

4chan consists of various boards, which are the sections dedicated to specific topics including anime, manga, video, games, music literature, fitness, politics and sports.
As of August 2022, 4chan has 75 image boards and one Flash animation board.
Boards have their own set of rules.
Of all the boards, we are particularly interested in the `/po/`, i.e., the politically incorrect board.

## Anonymity
The main feature of 4chan is anonymity.
Users do not need to register to post the content and posts are anonymous.
Users have an option to enter a name along with their post.
4chan also provides an optional tripcode as a form of authenticating a poster's identity.
Though the posts are anonymous, 4chan maintains the IP logs and makes them available.

## Moderation
4chan has little moderation however users can volunteer to be moderators. Janitors are a class between 'end user' and 'moderator' who are given access to the report system and may delete posts on their assigned boards, and submit ban requests.

## Ephemerality
Another feature of 4chan is ephemerality.
Take `/pol/` as an example, threads that receive recent replies are bumped to the top of the board, pushing other older threads down.
The board has limited space (21 pages), and once a thread is pushed out of the board, it enters the archive.
Archived threads are locked, and can no longer be replied to. 
Archived threads are deleted after a certain amount of time, depending on the speed at which new threads are archived.

# Data collection

We are interested in the `/pol/` board and hope to collect all the data on it.
Due to the ephemerality, we have to collect the data periodically. 

## API

4chan has an API, for details, please refer to https://github.com/4chan/4chan-API.
The API is publicly available and can be queried without limitation (they only ask not to send more than one request per second).

## Approach 1

Our first approach `code/collect/collect_4chan/download_4chan.py` queries the [catalog endpoint](https://a.4cdn.org/pol/catalog.json) of the `/pol/` board and store the response.
This endpoint returns all the threads on the board at the moment.

The process needs to be repeated every, say, 5mins.
Based on some preliminary analysis, it takes at least 15 mins for the thread to be archived, therefore we should have obtained all the original posts this way.

But one problem with this approach is that we are not getting all the replies.
For each original post, its most recent five replies are attached as well.
However, if people reply to this thread more than five times in 10mins or 5mins, then we will miss some of them and this is quite common.


## Approach 2

Our second approach `code/collect/collect_4chan/download_archived_threads_4chan.py` uses the [archive endpoint](https://a.4cdn.org/pol/archive.json) and the [thread endpoint](https://a.4cdn.org/po/thread/570368.json).

The archive endpoint returns a list of threads in the archive at the moment.
By comparing the snapshot of the archive of the current moment with the snapshot of a previous moment (say, 10mins), we can find the threads that were archived recently.
Then using the thread endpoint, we can fetch the whole thread (the original post and all its replies).
Since the thread can no longer be changed, the result is final. 


# Some helpful links
[Link to 4chan](https://boards.4channel.org/lgbt/thread/27917137#p27917137) <br />
[Link to FAQ for 4chan](https://www.4channel.org/faq) <br />
[Link to 4chan API documentation](https://github.com/4chan/4chan-API) <br />
[Link to paper](https://ojs.aaai.org/index.php/ICWSM/article/view/7354/7208) <br />
[Link to image/static content](https://github.com/4chan/4chan-API/blob/master/pages/User_images_and_static_content.md)
