import spacy
import asent
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat
from country_named_entity_recognition import find_countries

from collections import Counter

class NLPProcessor:
    _nlp = None
    _vader = None

    @classmethod
    def load_model(cls):
        if cls._nlp is None:
            cls._nlp = spacy.load("en_core_web_md")
            cls._nlp.add_pipe('asent_en_v1', last=True)

        if cls._vader is None:
            cls._vader = SentimentIntensityAnalyzer()

    @classmethod
    def process_article(cls, article):
        id = article['id']
        article_content = article['nohtmlbody']
        # load
        if cls._nlp is None or cls._vader is None:
            cls.load_model()

        doc = cls._nlp(article_content)
        
        ner_countries = {}
        for ent in doc.ents:
            if ent.label_ == "GPE":
                _country = find_countries(ent.text)
                if _country:
                    if _country[0][0].alpha_3 in ner_countries.keys():
                        ner_countries[_country[0][0].alpha_3]+=1
                    else:
                        ner_countries[_country[0][0].alpha_3]=1
        # vader_sentiment = cls._vader.polarity_scores(article_content)
        
        readability = {
            'flesch_reading_ease': textstat.flesch_reading_ease(article_content),
            'dale_chall_readability_score': textstat.dale_chall_readability_score(article_content)
        }

        polarity = {
            "positive": doc._.polarity.positive,
            "neutral": doc._.polarity.neutral,
            "negative": doc._.polarity.negative,
            "compound": doc._.polarity.compound,
        }
        sentences = doc._.polarity.n_sentences
        
        category_counts = Counter([token.text.lower() for token in doc if not token.is_stop and not token.is_punct and token.pos_ != 'VERB' and (token.pos_ in ['NOUN', 'ADJ', 'PROPN'] or token.like_num )])
        category_counts = dict(sorted(category_counts.items(), key=lambda item: item[1],reverse=True))
        return {
            "article_id": int(id),
            "polarity_pos": polarity["positive"],
            "polarity_neu": polarity["neutral"],
            "polarity_neg": polarity["negative"],
            "polarity_comp": polarity["compound"],
            "wordcount": article['wordcount'],
            "n_sentences" : sentences,
            "article_embedding" : doc.vector.tolist(),
            "article_embedding_norm" : doc.vector_norm,
            "readability_flesch_reading_ease": readability['flesch_reading_ease'],
            "readability_dale_chall_readability_score": readability['dale_chall_readability_score'],
            "readability_time_to_read": article['wordcount']/250,
            "ner_countries": ner_countries,
            "ner_keywords": category_counts,
        }

    @classmethod
    def process_batch(cls, articles):
        results = []
        for article in articles:
            result = cls.process_article(article)
            results.append(result)
        return results