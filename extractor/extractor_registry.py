from extractor.text_extractors import (
    JinnewsExtractor,
    NuhevExtractor,
    XwebunExtractor,
    LotikxaneExtractor,
    RojevaKurdExtractor,
    AjansawelatExtractor,
    BianetExtractor,
    AnfKurmanciExtractor,
)


DOMAIN_TO_EXTRACTOR = {
    "xwebun2.org": XwebunExtractor,
    "https://kurmanci.anf-news.com": AnfKurmanciExtractor,
    "nuhev.com": NuhevExtractor,
    "jinnews.net": JinnewsExtractor,
    "lotikxane.com": LotikxaneExtractor,
    "rojevakurd.com": RojevaKurdExtractor,
    "ajansawelat.com": AjansawelatExtractor,
    "bianet.org": BianetExtractor,
}
