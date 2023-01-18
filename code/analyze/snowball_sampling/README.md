# Introduction

This folder contains the scripts used to perform the snowball sampling procedure to expand the keyword list.
Please refer to the paper for details.

# Commands

Take `trial_1` as an example, it uses the data from 2022-09-16 to 2022-09-19 (inclusive).
To extract the most frequent grams, use the following commands in the project root in combination with the `Makefile`:

```sh
make extract_clean_text iteration=trial_1 start_date=2022-09-16 end_date=2022-09-19
make count_phrases iteration=trial_1 start_date=2022-09-16 end_date=2022-09-19
make extract_top_grams iteration=trial_1 start_date=2022-09-16 end_date=2022-09-19
```

The result can be found in `/data_volume/midterm2022/intermediate_files/snowball/{trial_index}/top_grams.csv`

The `top_grams.csv` file contains the top 50 most frequent unigrams and top 50 most frequent bigrams from different platforms.
Those already in the keyword list are excluded.
