from extractor.extractors import JinnewsExtractor, NuhevExtractor


DOMAIN_TO_EXTRACTOR = {
    "nuhev.com": NuhevExtractor,
    "jinnews.net": JinnewsExtractor,
}
