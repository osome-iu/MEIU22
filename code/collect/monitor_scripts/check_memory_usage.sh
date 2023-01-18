#!/bin/bash
# This script checks the memory usage of the machine
# If it's above 50%, it will send an email to Kevin
threshold=50
mem_usage=$(free -t | awk 'NR == 2 {printf("%.0f"), $3/$2*100}')
if [ $mem_usage -lt $threshold ]; then
    echo "$mem_usage small than $threshold"
else
    echo "$mem_usage Bigger than $threshold"
    echo "$(date -u): Collection machine memory usage at $mem_usage %." | mail -s "Collection machine memory usage too high" your@email
fi
