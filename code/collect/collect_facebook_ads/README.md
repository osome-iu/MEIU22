# [Facebook Ads](https://www.facebook.com/ads/library/api/?source=archive-landing-page)

## Notification related to Facebook Ads
Original notification can be found [here](https://www.facebook.com/business/help/167836590566506?id=288762101909005).

Advertisers won’t be able to create and run new ads about social issues, elections or politics in the US from **Tuesday, November 1 until Tuesday, November 8, 2022**. [Learn more about the restriction period and additional prohibited ads](https://www.facebook.com/business/help/253606115684173). <br /><br />
Due to current events in Yemen, Ukraine and Myanmar, advertiser information is temporarily unavailable on disclaimers and in the Ad Library for ads about social issues, elections or politics. Disclaimers on ads will be shown as "Paid for by an advertiser in (country such as Yemen, Ukraine or Myanmar)". Please check back for further updates.


## Helpful links: <br />
- [Facebook Ad API Library Documentation](https://www.facebook.com/ads/library/api/?source=archive-landing-page)
- [Ads Library API Script Repository](https://github.com/facebookresearch/Ad-Library-API-Script-Repository)
- [Unique Metrics published on FaceBook](https://www.facebook.com/business/help/283579896000936)
- [Documentation on User Access Token](https://developers.facebook.com/docs/facebook-login/guides/access-tokens#usertokens)
- [Documentation on Rate Limits](https://developers.facebook.com/docs/graph-api/overview/rate-limiting/)
- [How searching is done](https://developers.facebook.com/docs/graph-api/reference/ads_archive/)

We are using https://github.com/facebookresearch/Ad-Library-API-Script-Repository repository as sub module in our fb-ad collection project. To add this sub-module to the project, do the following:

```sh
git submodule init
git submodule update
```

Further detail is found here:
https://git-scm.com/book/en/v2/Git-Tools-Submodules

## Information on some parameters & fields in API: <br />
Basic information on parameters and fields can be found in [Facebook Ad API Library Documentation](https://www.facebook.com/ads/library/api/?source=archive-landing-page).

### Parameters <br />
Parameters we are using.

| Name | Description |
| --- | ----------- |
| `ad_active_status` | ALL |
| `ad_delivery_date_min`|yesterday's date|
| `ad_type` | POLITICAL_AND_ISSUE_ADS |
| `media_type` | ALL |
| `country` | US |



### Fields <br />
The fields are the components we are getting from search results.

| Name | Description |
| --- | ----------- |
| `id` | Id of ads|
| `ad_creation_time` | UTC date and time when someone created the ad|
| `ad_creative_bodies` | A list of text which displays in each carousel card of ad if ad has multiple ad versions or carousel cards|
| `ad_creative_link_captions` | list of captions that appear in the call to action section for each unique ad card of the ad |
| `ad_creative_link_descriptions` | list of descriptions which appear in the call to action section for each unique ad card of the ad |
| `ad_creative_link_titles` | list of titles which appear in the call to action section for each unique ad card of the ad. |
| `ad_delivery_start_time` | Date and time when an advertiser wants Facebook to start delivering an ad . The time is in UTC time | 
| `ad_delivery_stop_time` | Time when advertiser wants to stop delivery of their ad. Time is in UTC time |
| `ad_snapshot_url` | String with URL link which displays the archived ad. |
| `currency` | The currency used to pay for the ad |
| `demographic_distribution` | The demographic distribution of people reached by the ad. |
| `delivery_by_region` | Regional distribution of people reached by the ad. Provided as a percentage and where regions are at a sub-country level |
| `impressions` | A string containing the number of times the ad created an impression. |
| `languages` | The list of languages contained within the ad |
| `page_id` | ID of the Facebook Page that ran the ad |
| `page_name` | Name of the Facebook Page that ran the ad |
| `publisher_platforms` | A list of platforms where the archived ad appeared such as Facebook or Instagram |
| `spend` | A string showing amount of money spent running the ad as specified in currency |
| `bylines`| Name of the person, company or entity that provided funding the ad. Provided by the purchaser of the ad.  (In version 14 on wards the funding_entity is replaced by bylines) |


Further details can be found here: [here](https://www.facebook.com/business/help/675615482516035?helpref=search&sr=1&query=impressions). <br />


## Backward search

We performed a backward search on Oct 3 using the following command:

```sh
python collect/collect_facebook_ads/fb_ads_collect.py  -c config.ini -d 2022-06-01
```

Here, -d specifies the start date parameter and the script collects the data between the start date and the day when the script is executed. <br />
