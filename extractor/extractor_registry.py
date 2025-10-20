from extractor.text_extractors import JinnewsExtractor, NuhevExtractor, XwebunExtractor


DOMAIN_TO_EXTRACTOR = {
    "xwebun2.org": XwebunExtractor,

    "nuhev.com": NuhevExtractor,
    "jinnews.net": JinnewsExtractor,
}
