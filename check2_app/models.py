from django.db import models
from django.contrib.auth.models import User
from geopy.geocoders import Nominatim
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

geolocator = Nominatim(user_agent="geo_food_app")


class Location(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def _str_(self):
        return self.address or f"{self.latitude}, {self.longitude}"


class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    image = models.ImageField(upload_to='uploads/restaurant_images/', blank=True, null=True)
    categories = models.ManyToManyField('Category', related_name='restaurants')

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            location = geolocator.geocode(self.address)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
        super(Restaurant, self).save(*args, **kwargs)

    def _str_(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='uploads/menu_images/', blank=True, null=True)

    def _str_(self):
        return self.name


class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="menu_items")
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='uploads/menu_images/', blank=True, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=2)

    def _str_(self):
        return f"{self.name} - {self.restaurant.name}"


class DeliveryPerson(models.Model):
    name = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    current_latitude = models.FloatField(blank=True, null=True)
    current_longitude = models.FloatField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(5)], default=5.0)

    def _str_(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.address and (not self.current_latitude or not self.current_longitude):
            location = geolocator.geocode(self.address)
            if location:
                self.current_latitude = location.latitude
                self.current_longitude = location.longitude
        super(DeliveryPerson, self).save(*args, **kwargs)


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="reviews", blank=True, null=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="reviews", blank=True, null=True)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        if self.menu_item:
            return f"Review by {self.user.username} for {self.menu_item.name}"
        return f"Review by {self.user.username} for {self.restaurant.name}"


class UserDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.address and (not self.latitude or not self.longitude):
            location = geolocator.geocode(self.address)
            if location:
                self.latitude = location.latitude
                self.longitude = location.longitude
        super(UserDetails, self).save(*args, **kwargs)

    def _str_(self):
        return self.name 




class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Correct field
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    order_date = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def _str_(self):
        return f"{self.menu_item.name} - {self.quantity} pcs"