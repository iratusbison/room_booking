# models.py
from django.db import models

class Room(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    available = models.BooleanField(default=True)  
    unavailable = models.BooleanField(default=False)  


class Booking(models.Model):
    rooms = models.ManyToManyField(Room)
    start_date = models.DateField()
    end_date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
