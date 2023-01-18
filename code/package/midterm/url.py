import requests
import tldextract
from urlextract import URLExtract
from requests.exceptions import MissingSchema, ReadTimeout

_extractor = URLExtract()

_HEADERS = {"user-agent": "Mozilla/5.0 (compatible)"}
_HTTP_TIMEOUT = 20

# these domains need a redirect (Leon Yin + UnshortenIT 2018)
_short_domain_ad_redirects = [
    "sh.st",
    "adf.ly",
    "lnx.lu",
    "adfoc.us",
    "j.gs",
    "q.gs",
    "u.bb",
    "ay.gy",
    "atominik.com",
    "tinyium.com",
    "microify.com",
    "linkbucks.com",
    "www.linkbucks.com",
    "jzrputtbut.net",
    "any.gs",
    "cash4links.co",
    "cache4files.co",
    "dyo.gs",
    "filesonthe.net",
    "goneviral.com",
    "megaline.co",
    "miniurls.co",
    "qqc.co",
    "seriousdeals.net",
    "theseblogs.com",
    "theseforums.com",
    "tinylinks.co",
    "tubeviral.com",
    "ultrafiles.net",
    "urlbeat.net",
    "whackyvidz.com",
    "yyv.co",
    "href.li",
    "anonymz.com",
    "festyy.com",
    "ceesty.com",
    "tiny.cc",
]

# these are standard domain shorteners (Leon Yin 2018)
_short_domain = [
    "dlvr.it",
    "bit.ly",
    "buff.ly",
    "ow.ly",
    "goo.gl",
    "shar.es",
    "ift.tt",
    "fb.me",
    "washex.am",
    "smq.tc",
    "trib.al",
    "is.gd",
    "paper.li",
    "waa.ai",
    "tinyurl.com",
    "ht.ly",
    "1.usa.gov",
    "deck.ly",
    "bit.do",
    "lc.chat",
    "urls.tn",
    "soo.gd",
    "s2r.co",
    "clicky.me",
    "budurl.com",
    "bc.vc",
    "branch.io",
    "capsulink.com",
    "ux9.de",
    "fuck.it",
    "t2m.io",
    "shrt.li",
    "elbo.in",
    "shrtfly.com",
    "hiveam.com",
    "slink.be",
    "plu.sh",
    "cutt.ly",
    "zii.bz",
    "munj.pw",
    "t.co",
    "go.usa.gov",
    "on.fb.me",
    "j.mp",
    "amp.twimg.com",
    "ofa.bo",
]

# there are domain shorteners for common news outlets (Leon Yin 2018).
_short_domain_media = [
    "on.rt.com",
    "wapo.st",
    "hill.cm",
    "dailym.ai",
    "cnn.it",
    "nyti.ms",
    "politi.co",
    "fxn.ws",
    "usat.ly",
    "huff.to",
    "nyp.st",
    "cbsloc.al",
    "wpo.st",
    "on.wsj.com",
    "nydn.us",
    "on.wsj.com",
]

# there are link shorteners with the actual link appended on the end
_url_appenders = ["ln.is", "linkis.com"]

_kaicheng_paper = [
    "bit.ly",
    "dlvr.it",
    "liicr.nl",
    "tinyurl.com",
    "goo.gl",
    "ift.tt",
    "ow.ly",
    "fxn.ws",
    "buff.ly",
    "back.ly",
    "amzn.to",
    "nyti.ms",
    "nyp.st",
    "dailysign.al",
    "j.mp",
    "wapo.st" "reut.rs",
    "drudge.tw",
    "shar.es",
    "sumo.ly",
    "rebrand.ly",
    "covfefe.bz",
    "trib.al",
    "yhoo.it",
    "t.co",
    "shr.lc",
    "po.st",
    "dld.bz",
    "bitly.com",
    "crfrm.us",
    "flip.it",
    "mf.tt",
    "wp.me",
    "voat.co",
    "zurl.co",
    "fw.to",
    "mol.im",
    "read.bi",
    "disq.us",
    "tmsnrt.rs",
    "usat.ly",
    "aje.io",
    "sc.mp",
    "gop.cm",
    "crwd.fr",
    "zpr.io",
    "scq.io",
    "trib.in",
    "owl.li",
]

_ozgur_list = [
    "tiktok.com/t/",
    "link.chtbl.com",
    "zcu.io",
    "moms.ly",
    "t.ly",
    "youtu.be",
]


all_short_domains = list(
    set(
        _short_domain_ad_redirects
        + _short_domain
        + _short_domain_media
        + _url_appenders
        + _kaicheng_paper
        + _ozgur_list
    )
)


def expand_url(raw_url):
    """
    This function expands the url by sending a HTTP request to the raw_url

    Parameters:
        - raw_url (str): the raw url to be expanded

    Returns:
        - expanded_url (str): the expanded url
    """
    try:
        r = requests.head(
            raw_url, allow_redirects=True, headers=_HEADERS, timeout=_HTTP_TIMEOUT
        )
        expanded_url = r.url
        if not expanded_url.endswith("/"):
            expanded_url = expanded_url + "/"

    except MissingSchema:
        raw_url = "http://" + raw_url
        r = requests.head(
            raw_url, allow_redirects=True, headers=_HEADERS, timeout=_HTTP_TIMEOUT
        )
        expanded_url = r.url
        if not expanded_url.endswith("/"):
            expanded_url = expanded_url + "/"
    except ReadTimeout as e:
        # Sometimese the domain information is included in the readtimeout error message
        error_string = str(e)
        urls_in_error = _extractor.find_urls(error_string)
        if len([urls_in_error]) > 0:
            domain = urls_in_error[0]
            url = e.args[0].url
            expanded_url = domain + url
        else:
            expanded_url = raw_url
    except Exception as e:
        expanded_url = raw_url
    return expanded_url


def extract_domain(url):
    """
    Use the tldextract package to extract the domain of the url

    Parameters:
        - url (str): the url to extract domain from
    Returns:
        - domain (str): the domain of the url
    """
    subdomain, domain, suffix = tldextract.extract(url)

    if (subdomain == "") or (subdomain == "www"):
        domainAll = domain + "." + suffix
    else:
        domainAll = subdomain + "." + domain + "." + suffix

    return domainAll


def clean_url(url):
    """
    For a given url, this functions first expands it if it's a shortened link
    then extracts its domain

    Parameters:
        - url (str): the url to clean

    Returns:
        - expanded_url (str): the expanded url
        - domain (str): the domain extracted from the expanded url
    """
    domain = extract_domain(url)
    if domain in all_short_domains:
        expanded_url = expand_url(url)
        domain = extract_domain(expanded_url)
    else:
        expanded_url = url

    return expanded_url, domain
