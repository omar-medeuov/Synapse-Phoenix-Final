from django.db import models


class Transaction(models.Model):
    transaction_id = models.CharField(max_length=255)
    transaction_timestamp = models.DateTimeField()
    card_id = models.BigIntegerField()
    expiry_date = models.CharField(max_length=50, blank=True, null=True)
    issuer_bank_name = models.CharField(max_length=255, blank=True, null=True)
    merchant_id = models.BigIntegerField(blank=True, null=True)
    merchant_mcc = models.BigIntegerField(blank=True, null=True)
    mcc_category = models.CharField(max_length=255, blank=True, null=True)
    merchant_city = models.CharField(max_length=255, blank=True, null=True)
    transaction_type = models.CharField(max_length=100, blank=True, null=True)
    transaction_amount_kzt = models.FloatField(blank=True, null=True)
    original_amount = models.FloatField(blank=True, null=True)
    transaction_currency = models.CharField(max_length=10, blank=True, null=True)
    acquirer_country_iso = models.CharField(max_length=10, blank=True, null=True)
    pos_entry_mode = models.CharField(max_length=50, blank=True, null=True)
    wallet_type = models.CharField(max_length=100, blank=True, null=True)
    index_level_0 = models.BigIntegerField(blank=True, null=True, db_column='__index_level_0__')

    class Meta:
        db_table = 'transaction'
        ordering = ['-transaction_timestamp']

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.transaction_timestamp}"
