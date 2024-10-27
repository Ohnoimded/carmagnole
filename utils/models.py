from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.cache import cache
from django.core.exceptions import ValidationError

from django.contrib.postgres.fields import ArrayField

class DailyData(models.Model): # Retire this table
    id = models.AutoField(primary_key=True)
    url = models.TextField( unique=True)
    source = models.TextField(null=True, blank=True)
    author = models.TextField(null=True, blank=True)
    imageurl = models.TextField(null=True, blank=True)
    headline = models.TextField(null=True, blank=True)
    publishdate = models.DateTimeField( null=False)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'daily_data'
        unique_together = [['url','id']]





# class FrequentDataQuerySet(models.QuerySet):
#     def cached_queryset(self):
#         cached_objects = []
#         for obj in self:
#             cache_key = f"frequent_data_{obj.id}"
#             cached_obj = cache.get(cache_key)
#             if cached_obj is None:
#                 cache.set(cache_key, obj, timeout=60*60*24)
#                 cached_obj = obj
#             cached_objects.append(cached_obj)
#         # Create a new queryset from the cached objects
#         return self.model.objects.filter(id__in=[obj.id for obj in cached_objects]) 

# class FrequentDataManager(models.Manager):
#     def get_queryset(self):
#         return FrequentDataQuerySet(self.model, using=self._db).order_by('-id')

class FrequentData(models.Model):
    id = models.AutoField(primary_key=True)
    url = models.TextField(unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=False)
    shorturl = models.TextField(unique=True, null=True, blank=True)
    source = models.TextField(null=True, blank=True)
    section = models.TextField(null=True, blank=True)
    author = models.TextField(null=True, blank=True)
    imageurl = models.TextField(null=True, blank=True)
    headline = models.TextField(null=True, blank=True)
    wordcount = models.IntegerField(null=True, blank=True)
    publishdate = models.DateTimeField(null=False)
    htmlbody = models.CharField(null=True, blank=True)
    nohtmlbody = models.TextField(null=True, blank=True)

    # objects = FrequentDataManager()

    class Meta:
        db_table = 'frequent_data'
        unique_together = [['id','slug']]
        indexes = [
            models.Index(fields=[ 'id'], name='article_id_idx'),
            ]
        

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.generate_unique_slug(self.headline)
        super().save(*args, **kwargs)

    def generate_unique_slug(self, headline):
        slug = slugify(headline)
        unique_slug = slug
        num = 1
        while FrequentData.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{num}"
            num += 1
        return unique_slug
    
#########################################################################################

def betweenNegOneAndPosOneValidator(value:float):
    if -1 <= value <= 1:
        return value
    else:
        raise ValidationError('Value should be between -1 and 1.')
    
def betweenOneAndHundredValidator(value:float):
    if 1 <= value <= 100:
        return value
    else:
        raise ValidationError('Value should be between 1 and 100.')
    

class ArticleMetaAnalytics(models.Model):
    class Meta:
        db_table = 'article_meta_analytics'
        indexes = [
            models.Index(fields=[ 'id'], name='analytics_id_idx'),
            models.Index(fields=[ 'article'], name='analytics_article_id_idx'),
            ]
        
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(FrequentData, on_delete=models.CASCADE,to_field='id')
    
    created_at = models.DateTimeField( auto_now_add=True)
    
    polarity_pos=models.DecimalField(decimal_places=5,max_digits=6,validators=[betweenNegOneAndPosOneValidator])
    polarity_neu=models.DecimalField(decimal_places=5,max_digits=6,validators=[betweenNegOneAndPosOneValidator])
    polarity_neg=models.DecimalField(decimal_places=5,max_digits=6,validators=[betweenNegOneAndPosOneValidator])
    polarity_comp=models.DecimalField(decimal_places=5,max_digits=6,validators=[betweenNegOneAndPosOneValidator])
    
    wordcount = models.IntegerField(null=True, blank=True)
    n_sentences = models.IntegerField(null=False, blank=False, default=1)
    
    article_embedding = ArrayField(models.FloatField(), blank=True, null=True, default=list)
    article_embedding_norm = models.DecimalField(decimal_places=15, max_digits=30, null=True, blank=True)
    
    readability_flesch_reading_ease = models.DecimalField(decimal_places=2,max_digits=5,validators=[betweenOneAndHundredValidator] )
    readability_dale_chall_readability_score = models.DecimalField(decimal_places=2,max_digits=5,validators=[betweenOneAndHundredValidator] )
    readability_time_to_read = models.DecimalField(decimal_places=2,max_digits=4,) # in minutes
    
    ner_countries = models.JSONField(null=True, blank=True, default=dict)
    ner_keywords = models.JSONField(null=True, blank=True, default=dict)
    

#########################################################################################
  
class ArticleAccess(models.Model):
    id = models.AutoField(primary_key=True)
    article = models.ForeignKey(FrequentData, on_delete=models.CASCADE, to_field='id')
    accessed_ip = models.CharField(max_length=39, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'article_access'
        
class UserTracker(models.Model):
    id = models.AutoField(primary_key=True)
    accessed_ip = models.CharField(max_length=39, blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_tracker'


# class NewsAPIServeCache(models.Model):
#     id = models.AutoField(primary_key=True)
#     original_url = models.TextField(unique=True)
#     source = models.TextField(null=True, blank=True)
#     section = models.TextField(null=True, blank=True)
#     author = models.TextField(null=True, blank=True)
#     imageurl = models.TextField(null=True, blank=True)
#     headline = models.TextField(null=True, blank=True)
#     wordcount = models.IntegerField(null=True, blank=True)
#     publishdate = models.DateTimeField( null=False)
#     htmlbody = models.TextField(null=True, blank=True)

#     class Meta:
#         db_table = 'NewsAPIServeCache'
#         unique_together = [['url','id']]





###############################################################################

# I think this can be used for thinks unrelated to stocks. Maybe for tracking users, recommendations, and a standardised data format. 
# Cities should also be there. But that requires more reading. So, fuck that.
    """
          There is sql queries txt file. check that for all mat views, crons, db confs, etc
    """
    
class MarketDataMatView(models.Model):
    '''
    Materialized View only designed for SSE
    '''
    id = models.BigIntegerField(primary_key=True)
    ticker_symbol = models.CharField(max_length=20)
    ticker_desc = models.CharField(max_length=120)
    ticker_short = models.CharField(max_length=20)
    current_time_utc = models.DateTimeField()
    current_time_ltz = models.DateTimeField()
    timezone_name = models.CharField(max_length=34)
    current_price = models.DecimalField(max_digits=10, decimal_places=3)
    last_price = models.DecimalField(max_digits=10, decimal_places=3)
    last_traded_date = models.DateField()
    currency_name = models.CharField(max_length=120)
    currency_code = models.CharField(max_length=3)
    # currency_char = models.TextField()
    html_code = models.CharField(max_length=10)
    currency_prefix = models.CharField(max_length=3)
    currency_unicode = models.CharField(max_length=8)

    class Meta:
        managed = False  # DO NOT CHANGE TO TRUE. THIS NEED NO MIGRATIONS
        db_table = 'stock_prices_matview'
    
class MarketDataHistoric(models.Model):
    '''
    Historic data: OHLC, 
    '''
    id = models.AutoField(primary_key=True) # Add BigAutoField if needed after a month's test
    symbol_id = models.ForeignKey('StockSymbolsModel', on_delete=models.PROTECT, blank=False, to_field='google')
    trading_date = models.DateField(blank=False)
    open_price = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    high_price = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    low_price = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    close_price = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)

    class Meta:
        db_table = 'stock_market_prices_historic'
        constraints = [
            models.UniqueConstraint(fields=['symbol_id', 'trading_date'], name='unique_symbol_id_trading_date')
            ]
        indexes = [
            # models.Index(fields=['id', 'symbol'], name='id_symbol_idx'),
            # models.Index(fields=['symbol_id'], name='smp_historic_symbol_id_idx'),
            models.Index(fields=['trading_date'], name='smp_historic_trading_date_idx'),
            ]


class MarketData(models.Model):
    '''
    Current prices
    '''
    id = models.AutoField(primary_key=True) # Add BigAutoField if needed after a month's test
    symbol = models.ForeignKey('StockSymbolsModel', on_delete=models.PROTECT, blank=False, to_field='google')
    price = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True, blank=False)

    class Meta:
        db_table = 'stock_market_prices'
        indexes = [
            models.Index(fields=['id'], name='stock_market_prices_id_idx'),
            # models.Index(fields=['symbol'], name='stock_market_prices_symbol_idx'),
            ]


class SymbolType(models.TextChoices):
    COMMON = 'COM', 'Common Stock'
    PREFERRED = 'PRF', 'Preferred Stock'
    INDEX = 'IND', 'Market Index'
    ETF = 'ETF', 'Exchange Traded Fund'
    OTHER = 'OTH', 'Other'
    
class StockSymbolsModel(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=120, blank=False)
    symbol_type = models.CharField(max_length=3, choices=SymbolType.choices, default=SymbolType.COMMON)
    google = models.CharField(max_length=20, null=True, blank=True)
    ticker = models.CharField(max_length=20, null=True, blank=True)
    bbg = models.CharField(max_length=12, null=True, blank=True)
    cusip = models.CharField(max_length=9, null=True, blank=True)
    isin = models.CharField(max_length=12, null=True, blank=True)
    sedol = models.CharField(max_length=7, null=True, blank=True)
    exchange_mic = models.ManyToManyField('StockMarketsModel', related_name='symbols' )
    currency = models.ForeignKey(
        'CurrencyModel', on_delete=models.PROTECT, blank=False, to_field='code')

    class Meta:
        db_table = 'stock_symbols'
        constraints = [
            # models.UniqueConstraint(fields=['isin','cusip','sedol', 'symbol_type'], name='unique_isin_cusip_sedol_exchange_mic_type'),
            # models.UniqueConstraint(fields=['bbg'], name='unique_bbg'),
            models.UniqueConstraint(fields=['google'], name='unique_google'),
        ]
        indexes = [
            models.Index(fields=[ 'google'], name='google_idx'),
            ]

    def clean(self):
        super().clean()
        if not any([self.google, self.bbg, self.cusip, self.isin, self.sedol]):
            raise ValidationError(
                "At least one of google, bbg, cusip, isin, or sedol should be present")
        if StockSymbolsModel.objects.filter(
            isin=self.isin,
            cusip=self.cusip,
            sedol=self.sedol,
            symbol_type=self.symbol_type
        ).exclude(id=self.id).exists():
            raise ValidationError(
                "A record with this combination of isin, cusip, sedol, and symbol_type already exists."
            )

class StockMarketsModel(models.Model):
    '''
    based on ISO 10383
    https://www.iso20022.org/market-identifier-codes

    lei is based on ISO 17442-2:2020
    https://www.iso.org/standard/79917.html
    '''
    id = models.AutoField(primary_key=True)
    mnemonic = models.CharField(max_length=7)
    mic = models.CharField(max_length=6, unique=True, blank=False)
    operating_mic = models.CharField(max_length=6, blank=False)
    mcc = models.CharField(max_length=4, blank=False)
    lei = models.CharField(max_length=20)
    lei_name = models.CharField(max_length=255)
    market_name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.ForeignKey(
        'CountryModel', on_delete=models.PROTECT, blank=False,to_field='alpha_2')
    timezone_name = models.CharField(max_length=34, null=True)

    class Meta:
        db_table = 'stock_exchanges'
        unique_together = [['mnemonic', 'mic','operating_mic', 'lei','mcc','city']]


        
class CurrencySymbolModel(models.Model):
    '''
    Currently there are 62 unicode characters associated with currency
    '''
    id = models.AutoField(primary_key=True)
    character = models.CharField(max_length=6, unique=True, blank=False)
    decimal_value = models.PositiveIntegerField(unique=True, blank=False)
    unicode_value = models.CharField(max_length=8, unique=True, blank=False) 
    html_entity = models.CharField(max_length=10, blank=True, null=True) 
    html_code = models.CharField(max_length=10, blank=True, null=True) 
    name = models.CharField(max_length=50, unique=True, blank=False) 

    class Meta:
        db_table = 'currency_symbols'
        unique_together = [['character', 'decimal_value', 'unicode_value']]

class CurrencyModel(models.Model):
    '''
    currency_code is based on ISO 4217
    https://www.iso.org/iso-4217-currency-codes.html

    name: currency name
    code: iso 3 digit currency code
    symbol: id of currency_symbols
    prefix: When symbol char is not available. eg: Kronor (KR).
    '''
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120, blank=False)
    code = models.CharField(max_length=3, unique=True, blank=False)
    symbol = models.ManyToManyField(CurrencySymbolModel, blank=True)
    prefix = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        db_table = 'currencies'
        unique_together = [['name', 'code']]

class CountryModel(models.Model):
    '''
    country codes are based on ISO 3166 
    https://www.iso.org/iso-3166-country-codes.html

    id field is same as numeric(3) in ISO 3166. So no autofield. 

    NB: Always use alpha_3 (3 digit code). eg: USA, IND
    '''
    id = models.IntegerField( primary_key=True)
    name = models.CharField(max_length=120, blank=False)
    alpha_2 = models.CharField(max_length=2, unique=True, blank=False)
    alpha_3 = models.CharField(max_length=3, unique=True, blank=False)

    class Meta:
        db_table = 'countries'
        unique_together = [['id', 'name', 'alpha_2', 'alpha_3']]





################################################################################


class NewsletterSubscriberModel(models.Model):
    id = models.AutoField( primary_key=True)
    email = models.EmailField(unique=True)
    subscribed = models.BooleanField(default=True)
    subscription_date = models.DateTimeField(auto_now=True)
    unsubscription_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "newsletter_subscribers"
        
    def unsubscribe(self):

        self.subscribed = False
        self.unsubscription_date = timezone.now()
        self.save()

    def subscribe(self):
    
        self.subscribed = True
        self.unsubscription_date = None
        self.save()