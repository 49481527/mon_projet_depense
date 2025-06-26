from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    CATEGORY_TYPES = (
        ('expense', 'Dépense'),
        ('income', 'Revenu'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES)
    icon = models.CharField(max_length=10, blank=True, default='')
    color = models.CharField(max_length=20, default='#FF69B4')

    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('expense', 'Dépense'),
        ('income', 'Revenu'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)  # <-- Correction ici
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} F CFA - {self.category.name}"

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    alerts = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.amount} F CFA"
