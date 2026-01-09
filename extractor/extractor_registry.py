from extractor.text_extractors import (
    JinnewsExtractor,
    NuhevExtractor,
    XwebunExtractor,
    LotikxaneExtractor,
    RojevaKurdExtractor,
    AjansawelatExtractor,
    BianetExtractor,
    AnfKurmanciExtractor,
    MezopotamyaExtractor,
    DengeEmerikaExtractor,
    RupelanuExtractor,
    SemakurdExtractor,
    CandnameExtractor,
)


DOMAIN_TO_EXTRACTOR = {
    "xwebun2.org": XwebunExtractor,
    "kurmanci.anf-news.com": AnfKurmanciExtractor,
    "nuhev.com": NuhevExtractor,
    "jinnews.net": JinnewsExtractor,
    "lotikxane.com": LotikxaneExtractor,
    "rojevakurd.com": RojevaKurdExtractor,
    "ajansawelat.com": AjansawelatExtractor,
    "bianet.org": BianetExtractor,
    "mezopotamyaajansi.com": MezopotamyaExtractor,
    "dengeamerika.com": DengeEmerikaExtractor,
    "rupelanu.com": RupelanuExtractor,
    "semakurd.net": SemakurdExtractor,
    "candname.com": CandnameExtractor,
}
