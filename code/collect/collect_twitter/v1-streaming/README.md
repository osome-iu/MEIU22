# v1 Twitter Streamer

This is a tweet streaming pipeline that can be set up to stream tweets from Twitter by following the [below steps](#setting-up-the-pipeline).

* [Setting up the Pipeline](#setting-up-the-pipeline)
    * [How to download tweets with `twitter-streamer-V1.py`](#how-to-download-tweets-with-twitter-streamer-v1py)
* [Using `supervisor` with `twitter-streamer-V1.py`](#using-supervisor-with-twitter-streamer-v1py)
    * [Killing `supervisor`](#killing-supervisor) 
    * [`supervisor` logs/files](#supervisor-logsfiles)
* [Details on Collected Tweets](#details-on-collected-tweets)

## Setting Up the Pipeline

This pipeline utilizes Python 3 so this needs to be installed before doing anything else. 
* [https://www.python.org/download/releases/3.0/](https://www.python.org/download/releases/3.0/)

**Follow these steps to get the stream started.**
1. `ssh` into your working directory
2. Clone this repository by entering 
3. Find `config.ini` in the root of the cloned directory, and edit the file with your credentials and path to store data
    ```
    # Your Twitter credentials
    [TWITTER_CREDS]
    access_token = INSERT_TOKEN_HERE
    access_token_secret = INSERT_TOKEN_HERE
    api_key = INSERT_KEY_HERE
    api_key_secret = INSERT_KEY_HERE

    # Important paths:
    #   - keywords_file = the path to a file with keywords to match within your streamer (this is central to the project and need not be changed)
    #   - data_dir = where tweets will be saved
    #   - log_dir = where your log file will be saved
    [PATHS]
    data_dir_twitter = /data_volume/midterm2022/data/twitter
    log_dir_twitter = /data_volume/midterm2022/logs/twitter
    ```

4. Do not forget to save the file but do **NOT** commit your credentials to the repository!!

5. This has been tested on tweepy package version 3.8.0. The recommended practice is to use a virtual environment by using the makefile which installs the necessary dependencies, including tweepy 3.8.0.   
If you are a rebel and want to torture yourself by not using the virtual enviornment, check if tweepy exists in your environment using `which tweepy` or `pip show tweepy` and its version.   
If it does not exist, use either of the following to install it. 
    * `pip3 install tweepy = 3.8.0`  
    or 
    * `conda install -c conda-forge tweepy = 3.8.0`

To check if this package is installed, you can type `pip show tweepy` which should then display something like below
```
    Name: tweepy
    Version: 3.8.0
    Summary: Twitter library for python
    Home-page: http://github.com/tweepy/tweepy
    Author: Joshua Roesslein
    Author-email: tweepy@googlegroups.com
    License: MIT
    Location: /home/racball/miniconda3/envs/midterms22/lib/python3.8/site-packages
    Requires: PySocks, requests, requests-oauthlib, six
    Required-by: 
    (midterms22)
```
### How to download tweets with `twitter-streamer-V1.py`
At this point your python script is ready to go and can be utilized by calling the function in the following way:
* `python3 twitter-streamer-V1.py -cf <path/to/config.ini>`
> Note: python3 twitter-streamer-V1.py -h for help

### Using `supervisor` with `twitter-streamer-V1.py`
In the repository, you will notice configuration files for `supervisor`. These files tell `supervisor`, a program monitoring package, how to behave. Should we want to collect tweets for a very long time, we can use `supervisor` to automatically restart the `twitter-streamer-V1.py` script in the event that it breaks.

6. Edit and save the `midterm_stream.conf` file by replacing `**YOUR_USERNAME**` with your own username 

7. Make sure you have supervisor installed (`sudo apt install supervisor`). Copy (using sudo) the `midterm_stream.conf` file to `/etc/supervisor/conf.d/`

8. Ensure that your account has access to `supervisorctl`.

9. Then you can enter start supervisord by using `sudo systemctl start supervisor`. A single supervisor can run multiple streamers. So once a supervisor session is started, all you need to do is start the desired streamer as per 10.  
    * To make supervisord automatically restart use `sudo systemctl enable supervisor`
    * You can use `supervisorctl status` to check the status of different streamers. 

10. Starting streamers
    * Starting a streamer: `sudo supervisorctl start <streamer_name>`
If your `<streamer>.conf` file changes or the files the .conf refers to changes, the safest pipeline to incorporate these changes is
    * Stopping current streamer: `sudo supervisorctl stop <streamer_name>` 
    * If there are changes to `<streamer>.conf` copy (using sudo) the `<streamer>.conf` file to `/etc/supervisor/conf.d/`. If there are only changes to the the files which `<streamer>.conf` refers to, then you don't have to copy it but it would not hurt to do so.

    * Rereading the `<streamer>.conf` file: `sudo supervisorctl reread <streamer_name>` 
    * Update: `sudo supervisorctl reread <streamer_name>` (this might be https://github.com/Supervisor/supervisor/issues/720 but safe to run it anyway)
    * Restart: `sudo supervisorctl start <streamer_name>`

The above command should have activated the `twitter-streamer-V1.py` script and, subsequently, our stream should have started. If no errors were returned, that is a good thing. You can check the path where where you are expecting the data to be stored

### Killing `supervisor` 
* If `supervisor` has been running for a while and you'd like to stop it you can run `sudo systemctl stop supervisor` and it will stop.

### `supervisor` logs/files
* Everything to do with `supervisor` is set up to use a standard `systemctl supervisord deamon`.
    * The logs **for `supervisor`** can be found here: `/var/log/supervisor`
