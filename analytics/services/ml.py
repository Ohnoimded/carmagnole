import pandas as pd
import numpy as np
import spacy
import asent
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat
from country_named_entity_recognition import find_countries

from collections import Counter

from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler
from scipy.stats import entropy

pd.options.mode.copy_on_write = True


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
        article_wordcount = article['wordcount']
        
        del article # Tryna free up those mems ya know
        
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
                        ner_countries[_country[0][0].alpha_3] += 1
                    else:
                        ner_countries[_country[0][0].alpha_3] = 1
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
        
        # polarity_boost_factor = 5
        # polarity = {
        #     "positive": doc._.polarity.positive * polarity_boost_factor,
        #     "neutral": doc._.polarity.neutral * polarity_boost_factor,
        #     "negative": doc._.polarity.negative * polarity_boost_factor,
        #     "compound": doc._.polarity.compound * polarity_boost_factor,
        # }
        # polarity["positive"] =  polarity["positive"] / (polarity["positive"]+polarity["negative"] + polarity["neutral"])
        # polarity["neutral"] =  polarity["neutral"] / (polarity["positive"]+polarity["negative"] + polarity["neutral"])
        # polarity["negative"] =  polarity["negative"] / (polarity["positive"]+polarity["negative"] + polarity["neutral"])
        # polarity["compound"] =  polarity["compound"] / (polarity["positive"]+polarity["negative"] + polarity["neutral"])
        
        # #AI scam 101
        
        sentences = doc._.polarity.n_sentences

        category_counts = Counter([token.text.lower() for token in doc if 
                                   (token.pos_ in ['NOUN', 'ADJ', 'PROPN'] or token.like_num and len(token.text) == 4) and
                                   token.pos_ not in ['VERB', 'SYM', 'X','SPACE','INTJ'] and
                                   not token.is_stop and 
                                   not token.is_punct and 
                                   not token.is_digit 
                                   ])
        category_counts = dict(sorted(category_counts.most_common(100), key=lambda item: item[1], reverse=True))
        return {
            "article_id": int(id),
            "polarity_pos": polarity["positive"],
            "polarity_neu": polarity["neutral"],
            "polarity_neg": polarity["negative"],
            "polarity_comp": polarity["compound"],
            "wordcount": article_wordcount,
            "n_sentences": sentences,
            "article_embedding": doc.vector.tolist(),
            "article_embedding_norm": doc.vector_norm,
            "readability_flesch_reading_ease": readability['flesch_reading_ease'],
            "readability_dale_chall_readability_score": readability['dale_chall_readability_score'],
            "readability_time_to_read": article_wordcount/250,
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


class ArticleRanker:
    """ 
    Custom feature-based scoring and ranking algorithm that uses multiple methods 
    to evaluate articles based on sentiment analysis metrics.
    """
    
    @classmethod
    def score_articles(cls, raw_data_rows,raw_data_cols):
        
        raw_data =  pd.DataFrame(list(raw_data_rows), columns=raw_data_cols)
        
        data_that_matters = raw_data.loc[:, [
            'polarity_pos',
            'polarity_neu',
            'polarity_neg',
            'polarity_comp',
            'n_sentences',
            'article_embedding_norm',
            'readability_flesch_reading_ease',
            'readability_dale_chall_readability_score',
            'wordcount'
        ]].reset_index(drop=True).copy()

        scaler = MaxAbsScaler()
        data_scaled = scaler.fit_transform(data_that_matters)
        
        
        del data_that_matters # Tryna free up those mems ya know
        del scaler # Tryna free up those mems ya know
        
        raw_data.loc[:, 'polarity_difference'] = (raw_data.loc[:,'polarity_pos'] - raw_data.loc[:,'polarity_neg']).abs()
        raw_data.loc[:, 'sentiment_magnitude'] = raw_data.loc[:, 'polarity_pos'] + raw_data.loc[:,'polarity_neg']
        raw_data.loc[:, 'polarity_comp'] = raw_data['polarity_comp'].abs()

        num_clusters = 7  
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        clusters = kmeans.fit_predict(data_scaled)
        raw_data.loc[:, 'cluster'] = clusters

        del kmeans # Tryna free up those mems ya know
        del clusters # Tryna free up those mems ya know
        
        cluster_entropy = []
        for cluster in range(num_clusters):
            cluster_data = raw_data.loc[raw_data['cluster'] == cluster]
            if len(cluster_data) > 0:
                p_pos = (cluster_data.loc[:, 'polarity_pos'] > cluster_data.loc[:, 'polarity_neg']).sum() / len(cluster_data)
                p_neg = (cluster_data.loc[:, 'polarity_neg'] > cluster_data.loc[:, 'polarity_pos']).sum() / len(cluster_data)
                
                prob_distribution = np.array([p_pos, p_neg])
                entropy_value = entropy(prob_distribution + 1e-10, base=2)  
            else:
                entropy_value = 0  
            
            cluster_entropy.append(entropy_value)

        raw_data.loc[:, 'entropy'] = raw_data.loc[:, 'cluster'].map(lambda x: cluster_entropy[x])
        
        del cluster_entropy # Tryna free up those mems ya know

        raw_data.loc[:, 'final_score'] = ( pd.Series(raw_data.loc[:,'polarity_difference'], dtype='float64') +
                                     pd.Series(raw_data.loc[:,'sentiment_magnitude'], dtype='float64') +
                                     pd.Series(raw_data.loc[:,'polarity_comp'], dtype='float64') +
                                    0.9 * pd.Series(raw_data.loc[:,'entropy'], dtype='float64')
                                           )

        raw_data.loc[:, 'rank'] = raw_data.loc[:,'final_score'].rank(ascending=False, method='dense')
        # return raw_data.loc[:, ['article_id', 'polarity_difference', 'sentiment_magnitude', 
        #                  'polarity_comp', 'entropy', 'final_score', 'rank']].sort_values(by='rank')
        return raw_data.loc[:, ['article_id', 'final_score', 'rank']].sort_values(by='rank').reset_index(drop=True).loc[:,"article_id"].to_list()

