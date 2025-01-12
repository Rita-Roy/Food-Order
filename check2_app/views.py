from django.shortcuts import render, redirect,get_object_or_404
from django.http import HttpResponse
from geopy.distance import geodesic

from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt



from django.contrib import messages
from .models import UserDetails
from .forms import UserDetailsForm
  # Import the OTP generation function






from .models import Restaurant, Location, MenuItem,Category,DeliveryPerson,Review,OrderItem,Order
from django.contrib.auth.decorators import login_required
from geopy.geocoders import Nominatim

import razorpay
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse

from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User




from django.shortcuts import render, redirect
from django.http import HttpResponse
from geopy.distance import geodesic
from .models import Restaurant, Location, MenuItem,Category
from django.contrib.auth.decorators import login_required
from geopy.geocoders import Nominatim
from django.shortcuts import render, get_object_or_404






geolocator = Nominatim(user_agent="geo_food_app", timeout=100)




def home(request):
    restaurants = Restaurant.objects.all()
    categorys = Category.objects.all()  # Correcting the typo "categorys" -> "categories" might be better if intentional.

    if request.method == "POST":
        # Handle user location input
        address = request.POST.get("address")
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")

        if address:
            # Geocode the address to get latitude and longitude
            location = geolocator.geocode(address)
            if location:
                latitude, longitude = location.latitude, location.longitude
            else:
                return HttpResponse("Invalid address. Please try again.", status=400)
                if latitude and longitude:
            # Update or create the user's location
                    user_location, created = Location.objects.update_or_create(
                    user=request.user,
                defaults={
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                    "address": address if address else None,
                },
            )
            return redirect("available_restaurants")
        else:
            return HttpResponse("Invalid input. Please provide either a valid address or latitude and longitude.", status=400)

    # Combine restaurants and categorys into a single context dictionary
    context = {
        "restaurants": restaurants,
        "categorys": categorys,  # Consider renaming this to "categories" for clarity
    }
    return render(request, "home.html", context)







def food_item(request,pk):
    menuitem=MenuItem.objects.get(id=pk)
    return render(request, 'food.html',{"menuitem":menuitem})


def category_item(request,pk):
    categorys=Category.objects.get(id=pk)
    return render(request, 'category.html',{"categorys":categorys})






def restaurant_categories(request, pk):
   
    restaurant = get_object_or_404(Restaurant, id=pk)
    categories = restaurant.categories.all()

    categories_with_menu_items = []
    for category in categories:
        menu_items = category.menuitem_set.filter(restaurant=restaurant)
        categories_with_menu_items.append({
            'category': category,
            'menu_items': menu_items,
        })
    
    
    context = {
        'restaurant': restaurant,
        'categories_with_menu_items': categories_with_menu_items,
    }
    
    return render(request, 'restaurant_categories.html', context)



def search_menu_item(request):
    query = request.GET.get('q')  # 
    if query:
        try:
            menu_item = MenuItem.objects.get(name__icontains=query)  
            return redirect('food-item', pk=menu_item.id)  
        except MenuItem.DoesNotExist:
            
            return render(request, 'search_results.html', {"message": "No menu item found."})
    return render(request, 'search_results.html') 






def available_restaurants(request):
    user_location = Location.objects.filter(user=request.user).first()

    if not user_location:
        return redirect("home")

    user_coords = (user_location.latitude, user_location.longitude)
    nearby_restaurants = []

    for restaurant in Restaurant.objects.all():
        if restaurant.latitude and restaurant.longitude:
            restaurant_coords = (restaurant.latitude, restaurant.longitude)
            distance = geodesic(user_coords, restaurant_coords).km
            if distance <= 10:  # Filter restaurants within 10 km radius
                nearby_restaurants.append((restaurant, distance))

    context = {"restaurants": nearby_restaurants}
    return render(request, "available_restaurants.html",context)






@login_required
def cart_view(request):
    cart = request.session.get('cart', {})
    items = []
    total = 0

    for item_id, details in cart.items():
        menu_item = get_object_or_404(MenuItem, id=item_id)
        quantity = details['quantity']
        total += menu_item.price * quantity
        items.append({
            'menu_item': menu_item,
            'quantity': quantity,
            'subtotal': menu_item.price * quantity,
        })

    return render(request, 'cart.html', {'items': items, 'total': total})


@login_required
def add_to_cart(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    cart = request.session.get('cart', {})

    if str(item_id) in cart:
        cart[str(item_id)]['quantity'] += 1
    else:
        cart[str(item_id)] = {'quantity': 1}

    request.session['cart'] = cart
    return redirect('cart-view')


@login_required
def update_cart(request, item_id):
    cart = request.session.get('cart', {})
    if str(item_id) in cart:
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart[str(item_id)]['quantity'] = quantity
        else:
            del cart[str(item_id)]

    request.session['cart'] = cart
    return redirect('cart-view')


@login_required
def remove_from_cart(request, item_id):
    cart = request.session.get('cart', {})
    if str(item_id) in cart:
        del cart[str(item_id)]

    request.session['cart'] = cart
    return redirect('cart-view')


# authorize razorpay client with API Keys.
razorpay_client = razorpay.Client(
    auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))


@login_required
def homepage(request):
    # Redirect to fill user details
    cart = request.session.get('cart', {})
    total = 0

    # Calculate total amount from cart
    for item_id, details in cart.items():
        menu_item = get_object_or_404(MenuItem, id=item_id)
        total += menu_item.price * details['quantity']

    if total == 0:
        return HttpResponse("Your cart is empty!", status=400)

    amount_in_paise = int(total * 100)  # Convert to paise
    currency = "INR"

    # Create Razorpay order
    try:
        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": currency,
            "payment_capture": "1",
        })
    except Exception as e:
        return HttpResponse(f"Error creating payment: {e}", status=500)

    # Context for payment page
    context = {
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_merchant_key": settings.RAZOR_KEY_ID,
        "razorpay_amount": amount_in_paise,
        "currency": currency,
        "callback_url": "/paymenthandler/",
        "cart_total": total,
    }

    return render(request, "payment_page.html", context)




@csrf_exempt
def paymenthandler(request):
    if request.method == "POST":
        print(request.user)
        # order = Order.objects.create(
        #         user=request.user,
        #         total_price=total,
        #         # delivery_address=request.session.get('user_details', {}).get('address', 'No Address'),
        #         )
        # order.save()  # Save the order explicitly
        
        
        try:
            payment_id = request.POST.get('razorpay_payment_id', '')
            razorpay_order_id = request.POST.get('razorpay_order_id', '')
            signature = request.POST.get('razorpay_signature', '')

            params_dict = {
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": payment_id,
                "razorpay_signature": signature,
            }

            # Verify the payment signature
            result = razorpay_client.utility.verify_payment_signature(params_dict)
            if result is None:
                return HttpResponseBadRequest("Signature verification failed.")

            # Calculate the total price and fetch items from the cart
            cart = request.session.get('cart', {})
            total = 0
            order_items = []

            for item_id, details in cart.items():
                menu_item = get_object_or_404(MenuItem, id=item_id)
                subtotal = menu_item.price * details['quantity']
                total += subtotal
                order_items.append({
                    'menu_item': menu_item,
                    'quantity': details['quantity'],
                    'price': menu_item.price,
                    'subtotal': subtotal,
                })
                
                
                # Create the order
            
            # Create order items
          

            # Clear the cart
            del request.session['cart']

            # Redirect to order history
            return redirect('order-history')



        except Exception as e:
            print(f"Payment handler error: {e}")
            return HttpResponseBadRequest("Payment failed. Please try again.")
    else:
        return HttpResponseBadRequest("Invalid request method.")




def assign_delivery_agent(request):
    user_location = Location.objects.filter(user=request.user).first()

    if not user_location:
        return HttpResponse("User location not found. Please set your location.", status=400)

    user_coords = (user_location.latitude, user_location.longitude)
    available_agents = DeliveryPerson.objects.filter(is_available=True)

    if not available_agents.exists():
        return HttpResponse("No available delivery agents. Please try again later.", status=400)

    # Find the closest delivery agent
    closest_agent = None
    shortest_distance = float('inf')

    for agent in available_agents:
        if agent.current_latitude and agent.current_longitude:
            agent_coords = (agent.current_latitude, agent.current_longitude)
            distance = geodesic(user_coords, agent_coords).km
            if distance < shortest_distance:
                shortest_distance = distance
                closest_agent = agent

    if closest_agent:
        # Mark the agent as unavailable for the delivery
        closest_agent.is_available = False
        closest_agent.save()

        # Render a page with the agent's details
        context = {
            "agent_name": closest_agent.name,
            "agent_rating": closest_agent.rating,
            "agent_distance": round(shortest_distance, 2),
        }
        return render(request, "agent_assigned.html", context)
    else:
        return HttpResponse("No suitable delivery agent found.",status=400)
    
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.core.mail import send_mail
from django.conf import settings

def signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            email = form.cleaned_data.get('email')

            # Authenticate and log in the user
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                login(request, user)
                # Send email to the user
                send_mail(
                    subject="Welcome to Our Platform",
                    message=f"Hi {username},\n\nThank you for signing up!\n\nBest regards,\nYour Team",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, "Registration successful. Check your email for a welcome message.")
                return redirect('home')  # Redirect to the desired page after login
            else:
                messages.error(request, "Authentication failed. Please try logging in.")
        else:
            messages.error(request, "Invalid details. Please try again.")
    else:
        form = CustomUserCreationForm()
    return render(request, "sign_up.html", {"form": form})




def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirect to the home page
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to the home page after logout


def food_item(request, pk):
    # Use pk to get the menu item
    menu_item = get_object_or_404(MenuItem, pk=pk)

    # Handle the review submission
    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        
        if rating and comment:
            # Create and save the review
            Review.objects.create(
                user=request.user,
                menu_item=menu_item,
                rating=rating,
                comment=comment
            )
            # Reload the page to show the newly added review
            return redirect('food-item', pk=menu_item.pk)
    
    return render(request, 'food.html', {'menuitem': menu_item})





@login_required
def user_details(request):
    

    user_details = UserDetails.objects.filter(user=request.user).first()

    if request.method == 'POST':
        if user_details:
            # If user details already exist, update them
            form = UserDetailsForm(request.POST, instance=user_details)
             # Calculate the total price and fetch items from the cart
            cart = request.session.get('cart', {})
            total = 0
            order_items = []

            for item_id, details in cart.items():
                menu_item = get_object_or_404(MenuItem, id=item_id)
                subtotal = menu_item.price * details['quantity']
                total += subtotal
                order_items.append({
                    'menu_item': menu_item,
                    'quantity': details['quantity'],
                    'price': menu_item.price,
                    'subtotal': subtotal,
                })
            order = Order.objects.create(
                
                user=request.user,
                total_price=total,
                status='Completed',
                order_date='3-01-2025'
                # delivery_address=request.session.get('user_details', {}).get('address', 'No Address'),
                )
            for item in order_items:
                OrderItem.objects.create(
                order=order,
                menu_item=item['menu_item'],
                quantity=item['quantity'],
                price=item['price'],
            subtotal=item['subtotal']
        )

            order.save()
           
            

             # Save the order explicitly
        else:
            # If user details don't exist, create new ones
            form = UserDetailsForm(request.POST)
            form.instance.user = request.user

        if form.is_valid():
            form.save()
            return redirect('user_details')
    else:
        if user_details:
            form = UserDetailsForm(instance=user_details)
        else:
            form = UserDetailsForm()

    return render(request, 'user_details.html', {'form': form, 'user_details': user_details})

@login_required
def delete_user_details(request):
    user_details = get_object_or_404(UserDetails, user=request.user)
    user_details.delete()
    return redirect('user_details')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order

@login_required
def order_history(request):
    # Fetch all completed orders for the logged-in user
    orders = Order.objects.filter(user=request.user).order_by('-order_date')  # Adjust field name if needed

    return render(request, 'order_history.html', {'orders': orders})