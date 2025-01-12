from django.contrib import admin
from .models import Location, Restaurant, MenuItem,Category, DeliveryPerson, Order, OrderItem, Review

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'latitude', 'longitude')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'address', 'latitude', 'longitude')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price', 'image_display')
    search_fields = ('name', 'restaurant__name')

    def image_display(self, obj):
        # If an image is available, display it as a thumbnail, otherwise show a placeholder
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover;" />'
        else:
            return 'No image'
    image_display.allow_tags = True  # Allow HTML to be rendered for the image tag
    image_display.short_description = 'Image Preview'
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name','image')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'menu_item', 'rating', 'created_at')
    list_filter = ('restaurant', 'menu_item', 'rating', 'created_at')
    search_fields = ('user__username', 'comment')
    readonly_fields = ('created_at',)
    
    # Optional: you can set the ordering
    ordering = ('-created_at',)

# Register the Review model with the customized admin interface
admin.site.register(Review, ReviewAdmin)

admin.site.register(Order)
admin.site.register(OrderItem)

@admin.register(DeliveryPerson)
class DeliveryPersontAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_available', 'current_latitude', 'current_longitude')  # Correct field names
    list_editable = ('is_available',)  # Allows inline editing of availability
    list_filter = ('is_available',)  # Add a filter for availability
    search_fields = ('name',)  # Allow searching by name
