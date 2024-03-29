from django.db import models

class TwoInputFields(models.Model):
    str1 = models.CharField(max_length=50)
    str2 = models.CharField(max_length=50)


class Transaction(models.Model):
    """
    A transaction balance must be zero
    """
    tdate = models.DateField()
    desc = models.CharField(max_length=200)

class TransactionRecord(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.RESTRICT)
    record_num = models.SmallIntegerField()
    account = models.CharField(max_length=200)
    amount = models.PositiveBigIntegerField()
