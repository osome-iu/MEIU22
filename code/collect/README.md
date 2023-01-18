# Introduction

This folder contains the scripts we use to collect data from different social media platforms.

For Twitter's streaming data, we use [`supervisor`](http://supervisord.org/) to run the scripts.
For the rest of platforms, we use `cron job` to run the scripts periodically.

# Folder structure

- [/collect_4chan](/collect_4chan): scripts to collect data from 4chan's `/pol` board
- [/collect_facebook](/collect_facebook): script to collect data from Facebook and Instagram
- [/collect_facebook_ads](/collect_facebook_ads): script to collect ads from Facebook
- [/collect_reddit](/collect_reddit): script to collect data from Reddit
- [/collect_twitter](/collect_twitter): scripts to collect data from Twitter
- [/monitor_scripts](/monitor_scripts): scripts to monitor the status of the data collection processes
- [credentials_template.ini](credentials_template.ini): template of the credential file
- [crontab.bak](crontab.bak): crontab, schedule and commands to run the scripts periodically
- [environment_collect.yml](environment_collect.yml): python envrionment specifications
