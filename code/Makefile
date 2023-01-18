# Prepare enviroments
install_package:
	pip install -e ./package/

create_collection_env:
	conda create -n midterm22_collect -c bioconda -c conda-forge python=3.8

export_collection_env:
	conda env export > collect/environment_collect.yml

build_collection_env:
	conda env create --prefix $(path) --file collect/environment_collect.yml

create_analysis_env:
	conda create -n midterm22_analysis -c bioconda -c conda-forge python=3.8 nltk=3.7 scikit-learn=1.1.2 pandas=1.3.5 numpy=1.21.5

export_analysis_env:
	conda env export > analyze/environment_analysis.yml

build_analysis_env:
	conda env create --prefix $(path) --file analyze/environment_analysis.yml


SNOWSAMPLE_ROOT := analyze/snowball_sampling
COUNT_PHRASE_SCRIPT := count_clean_text_phrases.py
INTER_FILE_PATH := /data_volume/midterm2022/intermediate_files
PYTHON_PATH := /data_volume/home/midterm/miniconda3/envs/midterm22_analysis/bin/python

# Prepare snowball sampling
extract_clean_text:
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/extract_clean_twitter_text.py -c config.ini -i $(iteration) -sd $(start_date) -ed $(end_date)
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/extract_clean_fb_ig_text.py -c config.ini -i $(iteration) -sd $(start_date) -ed $(end_date)
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/extract_clean_reddit_text.py -c config.ini -i $(iteration) -sd $(start_date) -ed $(end_date)

count_phrases:
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/$(COUNT_PHRASE_SCRIPT) -c config.ini -i $(iteration) -cp "$(INTER_FILE_PATH)/snowball/$(iteration)/$(start_date)--$(end_date)__twitter_cleaned_posts.parquet" -p twitter
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/$(COUNT_PHRASE_SCRIPT) -c config.ini -i $(iteration) -cp "$(INTER_FILE_PATH)/snowball/$(iteration)/$(start_date)--$(end_date)__fb_cleaned_posts.parquet" -p fb
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/$(COUNT_PHRASE_SCRIPT) -c config.ini -i $(iteration) -cp "$(INTER_FILE_PATH)/snowball/$(iteration)/$(start_date)--$(end_date)__ig_cleaned_posts.parquet" -p ig
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/$(COUNT_PHRASE_SCRIPT) -c config.ini -i $(iteration) -cp "$(INTER_FILE_PATH)/snowball/$(iteration)/$(start_date)--$(end_date)__reddit_cleaned_posts.parquet" -p reddit

extract_top_grams:
	$(PYTHON_PATH) $(SNOWSAMPLE_ROOT)/extract_top_grams.py -c config.ini -i $(iteration) -sd $(start_date) -ed $(end_date)