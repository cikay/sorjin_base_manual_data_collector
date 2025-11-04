from extractor.text_extractors import (
    JinnewsExtractor,
    NuhevExtractor,
    XwebunExtractor,
    LotikxaneExtractor,
    RojevaKurdExtractor,
    AjansawelatExtractor,
    BianetExtractor,
)


DOMAIN_TO_EXTRACTOR = {
    "xwebun2.org": XwebunExtractor,

    "nuhev.com": NuhevExtractor,
    "jinnews.net": JinnewsExtractor,
    "lotikxane.com": LotikxaneExtractor,
    "rojevakurd.com": RojevaKurdExtractor,
    "ajansawelat.com": AjansawelatExtractor,
    "bianet.org": BianetExtractor,
}
