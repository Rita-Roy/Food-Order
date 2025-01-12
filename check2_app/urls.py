from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("restaurants/available/", views.available_restaurants, name="available_restaurants"),
    path("food/<int:pk>", views.food_item, name='food-item'),
    path("category/<int:pk>", views.category_item, name='category-item'),
    path("restaurant/<int:pk>/categories/", views.restaurant_categories, name='restaurant-categories'),
    path("cart/", views.cart_view, name="cart-view"),
    path("cart/add/<int:item_id>/", views.add_to_cart, name="add-to-cart"),
    path("cart/update/<int:item_id>/", views.update_cart, name="update-cart"),
    path("cart/remove/<int:item_id>/", views.remove_from_cart, name="remove-from-cart"),
    path('payment/', views.homepage, name='payment'),
    path('paymenthandler/', views.paymenthandler, name='paymenthandler'),
    path("assign-delivery-agent/", views.assign_delivery_agent, name="assign_delivery_agent"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("signup/", views.signup, name="signup"),
   
    path('food/<int:pk>/', views.food_item, name='food-item'),
    path('user-details/delete/', views.delete_user_details, name='delete_user_details'),
    path('search/', views.search_menu_item, name='search-menu-item'),
    path('menuitem/<int:pk>/', views.food_item, name='food-item'),
path('user-details/', views.user_details, name='user_details'),
    path("order-history/", views.order_history, name="order_history"),

]
