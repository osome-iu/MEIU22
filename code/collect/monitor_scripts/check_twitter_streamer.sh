#!/bin/bash
# This script checks if the twitter streamers for keyword and candidates are still running
# If not, it will send an email to Kevin
ps -aux | grep -v grep | grep "/home/midterm/miniconda3/envs/midterm22_collect/bin/python3 /home/midterm/midterm2022/collect/collect_twitter/v1-streaming/twitter-streamer-V1.py -c /home/midterm/midterm2022/config.ini" > /dev/null
if [ $? -eq 0 ]; then
    echo "Process is running."
else
    echo "$(date -u): Twitter streamer not running." | mail -s "Twitter streamer not running" your@email
fi

ps -aux | grep -v grep | grep "/home/midterm/miniconda3/envs/midterm22_collect/bin/python3 /home/midterm/midterm2022/collect/collect_twitter/v1-streaming/candidates-twitter-streamer-V1.py -c /home/midterm/midterm2022/config.ini" > /dev/null
if [ $? -eq 0 ]; then
    echo "Process is running."
else
    echo "$(date -u): Twitter streamer for candidates not running." | mail -s "Twitter streamer candidates not running" your@email
fi
