from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from .models import Category,MenuItem,CartItem,Cart,OTP,CustomUser
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import login
import random
from twilio.rest import Client
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from django.conf import settings
import razorpay



TWILIO_ACCOUNT_SID = ""

# Your Account SID and Auth Token from Twilio
account_sid = ""
auth_token = ""

# Your Twilio phone number
twilio_number = ""

RAZORPAY_KEY_ID = ""
RAZORPAY_KEY_SECRET = ""

# Create your views here.
def home(request):
    return render(request,'base/home.html')

def send_otp(phone_number,otp):
    # Generate a 6-digit OTP
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        to=phone_number,
        from_=twilio_number,
        body=f"Your OTP is: {otp}"
    )
    print(f"OTP sent to {phone_number}: {otp}")

def phone_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        if phone_number:
            # Generate a random 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            # Create an OTP record
            OTP.objects.create(phone_number=phone_number, otp_code=otp_code)
            # Send the OTP via SMS (here just printing to console)
            send_otp(phone_number, otp_code)
            messages.success(request, 'OTP has been sent to your phone.')
            # Save phone number in session for later verification
            request.session['phone_number'] = phone_number
            return redirect('otp')  # Ensure your URLconf has a name 'otp' for otp_view
        else:
            messages.error(request, 'Please enter a valid phone number.')
    return render(request, 'base/phone.html')


def otp_view(request):
    # Retrieve the phone number from the session
    phone_number = request.session.get('phone_number')
    if not phone_number:
        messages.error(request, 'Phone number not found. Please try again.')
        return redirect('phone')
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        if otp_input:
            # Get the latest unused OTP for this phone number
            try:
                otp_record = OTP.objects.filter(phone_number=phone_number, is_used=False).latest('created_at')
            except OTP.DoesNotExist:
                messages.error(request, 'No OTP request found. Please request again.')
                return redirect('phone')
            # Optionally, check if OTP is expired (e.g., valid for 5 minutes)
            time_diff = timezone.now() - otp_record.created_at
            if time_diff.seconds > 300:
                messages.error(request, 'OTP expired. Please request a new one.')
                return redirect('phone')
            if otp_record.otp_code == otp_input:
                # Mark the OTP as used
                otp_record.is_used = True
                otp_record.save()
                # Log in the user or create a new user if one doesn't exist
                user, created = CustomUser.objects.get_or_create(phone_number=phone_number)
                login(request, user)
                messages.success(request, 'You have been logged in successfully.')
                return redirect('home')  # Replace 'home' with your landing page name
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
    return render(request, 'base/otp.html', {'phone_number': phone_number})


def menu(request):
    categories = Category.objects.all()
    category_filter = request.GET.get('category', 'all')

    # Get menu items with quantity information
    menu_items = MenuItem.objects.all()
    if category_filter != 'all':
        menu_items = menu_items.filter(category__name__iexact=category_filter)

    # Get user's cart
    cart = None
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)

    cart_items_dict = {}
    cart_item_ids = []
    if cart:
        cart_items = cart.items.select_related('menu_item')
        cart_items_dict = {item.menu_item.id: item.quantity for item in cart_items}
        cart_item_ids = list(cart_items_dict.keys())

    context = {
        'categories': categories,
        'menu_items': menu_items,
        'active_category': category_filter,
        'cart_items_dict': cart_items_dict,
        'cart_item_ids': cart_item_ids,
    }
    # Convert menu_items queryset to a list to add quantity attribute
    menu_items = list(menu_items)
    for item in menu_items:
        item.quantity = cart_items_dict.get(item.id, 0)

    return render(request, 'base/menu.html', context)


def cart(request):
    if not request.user.is_authenticated:
        return redirect('home')

    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('menu_item')

    # Calculate total price
    total_price = sum(item.menu_item.price * item.quantity for item in cart_items)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price
    }
    return render(request, 'base/cart.html', context)


@require_POST
@login_required
def update_cart(request):
    # Get current user's cart
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Parse JSON data
    data = json.loads(request.body)
    item_id = data.get('item_id')
    action = data.get('action')

    # Get menu item or return 404
    menu_item = get_object_or_404(MenuItem, id=item_id)

    try:
        cart_item = CartItem.objects.get(cart=cart, menu_item=menu_item)
    except CartItem.DoesNotExist:
        cart_item = None

    # Handle actions
    if action == 'add':
        if not cart_item:
            CartItem.objects.create(cart=cart, menu_item=menu_item, quantity=1)
            return JsonResponse({'status': 'added', 'quantity': 1})
        return JsonResponse({'status': 'exists', 'quantity': cart_item.quantity})

    elif action in ['increment', 'decrement'] and cart_item:
        if action == 'increment':
            cart_item.quantity += 1
        else:
            cart_item.quantity -= 1

        if cart_item.quantity < 1:
            cart_item.delete()
            return JsonResponse({'status': 'removed', 'quantity': 0})

        cart_item.save()
        return JsonResponse({'status': 'updated', 'quantity': cart_item.quantity})

    return JsonResponse({'status': 'error'}, status=400)


@login_required
def create_razorpay_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    total_price = sum(item.menu_item.price * item.quantity for item in cart.items.all())

    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    data = {
        "amount": int(total_price * 100),  # Convert to paise
        "currency": "INR",
        "receipt": f"order_{request.user.id}",
        "notes": {
            "user": request.user.phone_number
        }
    }

    order = client.order.create(data=data)
    return JsonResponse(order)


@login_required
@require_POST
def payment_success(request):
    data = json.loads(request.body)

    # Verify payment signature
    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': data['razorpay_order_id'],
            'razorpay_payment_id': data['razorpay_payment_id'],
            'razorpay_signature': data['razorpay_signature']
        })

        # Create Order
        cart = get_object_or_404(Cart, user=request.user)
        total_price = sum(item.menu_item.price * item.quantity for item in cart.items.all())

        order = Order.objects.create(
            user=request.user,
            total_price=total_price
        )

        # Create Order Items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                menu_item=cart_item.menu_item,
                quantity=cart_item.quantity,
                price=cart_item.menu_item.price
            )

        # Clear Cart
        cart.items.all().delete()

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)