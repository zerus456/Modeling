from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mail
from vendor.models import Notifications
from decimal import Decimal
import requests
import stripe
from plugin.service_fee import calculate_service_fee
import razorpay

from plugin.paginate_queryset import paginate_queryset
from store import models as store_models
from customer import models as customer_models
from vendor import models as vendor_models
from userauths import models as userauths_models
from plugin.tax_calculation import tax_calculation
from plugin.exchange_rate import convert_usd_to_inr, convert_usd_to_kobo, convert_usd_to_ngn, get_usd_to_ngn_rate

from django.shortcuts import render
from django.contrib.auth import get_user_model
User = get_user_model()

def index(request):
    return render(request, "store/index.html")

stripe.api_key = settings.STRIPE_SECRET_KEY
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def clear_cart_items(request):
    try:
        cart_id = request.session['cart_id']
        store_models.Cart.objects.filter(cart_id=cart_id).delete()
    except:
        pass
    return

def index(request):
    products = store_models.Product.objects.filter(status="Published")
    categories = store_models.Category.objects.all()
    
    context = {
        "products": products,
        "categories": categories,
    }
    return render(request, "store/index.html", context)

def shop(request):
    products_list = store_models.Product.objects.filter(status="Published")
    categories = store_models.Category.objects.all()
    colors = store_models.VariantItem.objects.filter(variant__name='Color').values('title', 'content').distinct()
    sizes = store_models.VariantItem.objects.filter(variant__name='Size').values('title', 'content').distinct()
    item_display = [
        {"id": "1", "value": 1},
        {"id": "2", "value": 2},
        {"id": "3", "value": 3},
        {"id": "40", "value": 40},
        {"id": "50", "value": 50},
        {"id": "100", "value": 100},
    ]

    ratings = [
        {"id": "1", "value": "★☆☆☆☆"},
        {"id": "2", "value": "★★☆☆☆"},
        {"id": "3", "value": "★★★☆☆"},
        {"id": "4", "value": "★★★★☆"},
        {"id": "5", "value": "★★★★★"},
    ]

    prices = [
        {"id": "lowest", "value": "Highest to Lowest"},
        {"id": "highest", "value": "Lowest to Highest"},
    ]


    print(sizes)

    products = paginate_queryset(request, products_list, 10)

    context = {
        "products": products,
        "products_list": products_list,
        "categories": categories,
         'colors': colors,
        'sizes': sizes,
        'item_display': item_display,
        'ratings': ratings,
        'prices': prices,
    }
    return render(request, "store/shop.html", context)

def category(request, id):
    category = store_models.Category.objects.get(id=id)
    products_list = store_models.Product.objects.filter(status="Published", category=category)

    query = request.GET.get("q")
    if query:
        products_list = products_list.filter(name__icontains=query)

    products = paginate_queryset(request, products_list, 10)

    context = {
        "products": products,
        "products_list": products_list,
        "category": category,
    }
    return render(request, "store/category.html", context)

def vendors(request):
    vendors = userauths_models.Profile.objects.filter(user_type="Vendor")
    
    context = {
        "vendors": vendors
    }
    return render(request, "store/vendors.html", context)

def product_detail(request, slug):
    product = store_models.Product.objects.get(status="Published", slug=slug)
    product_stock_range = range(1, product.stock + 1)

    # LẤY VARIANTS (Color, Size, …)
    variants = store_models.Variant.objects.filter(product=product).prefetch_related("variantitem_set")

    # PRODUCTS LIÊN QUAN
    related_products = store_models.Product.objects.filter(category=product.category).exclude(id=product.id)

    context = {
        "product": product,
        "product_stock_range": product_stock_range,

        # TRUYỀN VARIANTS XUỐNG TEMPLATE
        "variants": variants,

        "related_products": related_products,
    }
    return render(request, "store/product_detail.html", context)


from decimal import Decimal
from django.http import JsonResponse
from django.contrib import messages
from store import models as store_models

def add_to_cart(request):
    id = request.GET.get("id")
    qty = request.GET.get("qty")
    color = request.GET.get("color")
    size = request.GET.get("size")
    cart_id = request.GET.get("cart_id")

    request.session['cart_id'] = cart_id

    # Check required fields
    if not id or not qty or not cart_id:
        return JsonResponse({"error": "Invalid parameters provided"}, status=400)

    # Get product
    try:
        product = store_models.Product.objects.get(status="Published", id=id)
    except store_models.Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    # Convert qty
    qty = int(qty)

    #  If stock is zero → do not allow adding to cart
    if product.stock <= 0:
        return JsonResponse({"error": "This product is out of stock!"}, status=400)

    # Look for existing item in cart
    existing_cart_item = store_models.Cart.objects.filter(cart_id=cart_id, product=product).first()

    # If item does not exist in cart → validate qty
    if not existing_cart_item:
        if qty > product.stock:
            return JsonResponse({"error": "Requested quantity exceeds available stock"}, status=400)

        cart = store_models.Cart()
        cart.product = product
        cart.qty = qty
        cart.price = product.price
        cart.color = color
        cart.size = size
        cart.sub_total = Decimal(product.price) * qty
        cart.shipping = Decimal(product.shipping) * qty
        cart.total = cart.sub_total + cart.shipping
        cart.user = request.user if request.user.is_authenticated else None
        cart.cart_id = cart_id
        cart.save()

        message = "Item added to cart"
    
    else:
        # If already in cart → update quantity
        new_qty = qty

        # ❌ Prevent exceeding stock
        if new_qty > product.stock:
            return JsonResponse({"error": "Cannot update cart. Quantity exceeds available stock"}, status=400)

        existing_cart_item.qty = new_qty
        existing_cart_item.color = color
        existing_cart_item.size = size
        existing_cart_item.price = product.price
        existing_cart_item.sub_total = Decimal(product.price) * new_qty
        existing_cart_item.shipping = Decimal(product.shipping) * new_qty
        existing_cart_item.total = existing_cart_item.sub_total + existing_cart_item.shipping
        existing_cart_item.save()

        message = "Cart updated"

    # Cart stats
    total_cart_items = store_models.Cart.objects.filter(cart_id=cart_id).count()
    cart_sub_total = store_models.Cart.objects.filter(cart_id=cart_id).aggregate(
        sub_total=models.Sum("sub_total")
    )['sub_total']

    # Return JSON
    return JsonResponse({
        "message": message,
        "total_cart_items": total_cart_items,
        "cart_sub_total": "{:,.2f}".format(cart_sub_total),
        "item_sub_total": "{:,.2f}".format(
            existing_cart_item.sub_total if existing_cart_item else cart.sub_total
        )
    })


def delete_cart_item(request):
    id = request.GET.get("id")
    item_id = request.GET.get("item_id")
    cart_id = request.GET.get("cart_id")
    
    # Validate required fields
    if not id and not item_id and not cart_id:
        return JsonResponse({"error": "Item or Product id not found"}, status=400)

    try:
        product = store_models.Product.objects.get(status="Published", id=id)
    except store_models.Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    # Check if the item is already in the cart
    item = store_models.Cart.objects.get(product=product, id=item_id)
    item.delete()

    # Count the total number of items in the cart
    total_cart_items = store_models.Cart.objects.filter(cart_id=cart_id)
    cart_sub_total = store_models.Cart.objects.filter(cart_id=cart_id).aggregate(sub_total = models.Sum("sub_total"))['sub_total']

    return JsonResponse({
        "message": "Item deleted",
        "total_cart_items": total_cart_items.count(),
        "cart_sub_total": "{:,.2f}".format(cart_sub_total) if cart_sub_total else 0.00
    })

from decimal import Decimal
from django.db import transaction

# … các import khác giữ nguyên …

@transaction.atomic
def create_order(request):
    if request.method != "POST":
        return redirect("store:cart")

    # 1️⃣  Get selected address
    address_id = request.POST.get("address")
    if not address_id:
        messages.warning(request, "Please select an address to continue.")
        return redirect("store:cart")

    address = customer_models.Address.objects.filter(user=request.user, id=address_id).first()
    if not address:
        messages.error(request, "Address not found.")
        return redirect("store:cart")

    # 2️⃣  Get cart items
    cart_id = request.session.get("cart_id")
    items = store_models.Cart.objects.filter(cart_id=cart_id)

    if not items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("store:cart")

    cart_sub_total = items.aggregate(sub_total=models.Sum("sub_total"))["sub_total"] or Decimal("0")
    cart_shipping_total = items.aggregate(shipping=models.Sum("shipping"))["shipping"] or Decimal("0")

    # 3️⃣  Create the Order
    order = store_models.Order.objects.create(
        customer=request.user,
        address=address,
        sub_total=cart_sub_total,
        shipping=cart_shipping_total,
        tax=tax_calculation(address.country, cart_sub_total),
    )

    order.service_fee = calculate_service_fee(order.sub_total + order.shipping + Decimal(order.tax))
    order.total = order.sub_total + order.shipping + Decimal(order.tax) + order.service_fee
    order.save(update_fields=["service_fee", "total"])

    # 4️⃣  Create OrderItems + Assign Vendor + Reduce Stock
    for cart_item in items:
        product = cart_item.product

        # Vendor check
        try:
            vendor_user = product.vendor.user
        except vendor_models.Vendor.DoesNotExist:
            messages.error(
                request,
                f"Product '{product.name}' has no assigned vendor. Contact the administrator."
            )
            order.delete()  # Cancel incomplete order
            return redirect("store:cart")

        # Create Order Item
        store_models.OrderItem.objects.create(
            order=order,
            product=product,
            qty=cart_item.qty,
            color=cart_item.color,
            size=cart_item.size,
            price=cart_item.price,
            sub_total=cart_item.sub_total,
            shipping=cart_item.shipping,
            tax=tax_calculation(address.country, cart_item.sub_total),
            total=cart_item.total,
            initial_total=cart_item.total,
            vendor=vendor_user,
        )

        # Add vendor to order
        order.vendors.add(vendor_user)

        # 📉 Reduce product stock
        product.stock -= cart_item.qty
        if product.stock < 0:
            product.stock = 0
        product.save(update_fields=["stock"])

    # 5️⃣  Clear cart
    items.delete()
    request.session.pop("cart_id", None)

    # 6️⃣  Set payment method
    order.payment_method = "Manual"
    order.payment_status = "Processing"
    order.save(update_fields=["payment_method", "payment_status"])

    # 7️⃣  Redirect to checkout page
    return redirect("store:checkout", order.order_id)




def coupon_apply(request, order_id):
    print("Order Id ========", order_id)
    
    try:
        order = store_models.Order.objects.get(order_id=order_id)
        order_items = store_models.OrderItem.objects.filter(order=order)
    except store_models.Order.DoesNotExist:
        messages.error(request, "Order not found")
        return redirect("store:cart")

    if request.method == 'POST':
        coupon_code = request.POST.get("coupon_code")
        
        if not coupon_code:
            messages.error(request, "No coupon entered")
            return redirect("store:checkout", order.order_id)
            
        try:
            coupon = store_models.Coupon.objects.get(code=coupon_code)
        except store_models.Coupon.DoesNotExist:
            messages.error(request, "Coupon does not exist")
            return redirect("store:checkout", order.order_id)
        
        if coupon in order.coupons.all():
            messages.warning(request, "Coupon already activated")
            return redirect("store:checkout", order.order_id)
        else:
            # Assuming coupon applies to specific vendor items, not globally
            total_discount = 0
            for item in order_items:
                if coupon.vendor == item.product.vendor and coupon not in item.coupon.all():
                    item_discount = item.total * coupon.discount / 100  # Discount for this item
                    total_discount += item_discount

                    item.coupon.add(coupon) 
                    item.total -= item_discount
                    item.saved += item_discount
                    item.save()

            # Apply total discount to the order after processing all items
            if total_discount > 0:
                order.coupons.add(coupon)
                order.total -= total_discount
                order.sub_total -= total_discount
                order.saved += total_discount
                order.save()
        
        messages.success(request, "Coupon Activated")
        return redirect("store:checkout", order.order_id)

def checkout(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)

    # Người dùng bấm nút “Xác nhận đơn hàng (COD)”
    if request.method == "POST":
        clear_cart_items(request)            # dọn giỏ hàng
        order.payment_method = "Manual"
        order.payment_status = "Processing"
        order.save(update_fields=["payment_method", "payment_status"])
        return redirect(
            f"/payment_status/{order.order_id}/?payment_status=processing"
        )

    # GET: chỉ cần trả order cho template, không cần khóa API thanh toán
    return render(request, "store/checkout.html", {"order": order})

@csrf_exempt
def stripe_payment(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    stripe.api_key = settings.STRIPE_SECRET_KEY

    checkout_session = stripe.checkout.Session.create(
        customer_email = order.address.email,
        payment_method_types=['card'],
        line_items = [
            {
                'price_data': {
                    'currency': 'USD',
                    'product_data': {
                        'name': order.address.full_name
                    },
                    'unit_amount': int(order.total * 100)
                },
                'quantity': 1
            }
        ],
        mode = 'payment',
        success_url = request.build_absolute_uri(reverse("store:stripe_payment_verify", args=[order.order_id])) + "?session_id={CHECKOUT_SESSION_ID}" + "&payment_method=Stripe",
        cancel_url = request.build_absolute_uri(reverse("store:stripe_payment_verify", args=[order.order_id]))
    )

    print("checkkout session", checkout_session)
    return JsonResponse({"sessionId": checkout_session.id})

def stripe_payment_verify(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)

    session_id = request.GET.get("session_id")
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == "paid":
        if order.payment_status == "Processing":
            order.payment_status = "Paid"
            order.save()
            clear_cart_items(request)
            customer_models.Notifications.objects.create(type="New Order", user=request.user)
            customer_merge_data = {
                'order': order,
                'order_items': order.order_items(),
            }
            subject = f"New Order!"
            text_body = render_to_string("email/order/customer/customer_new_order.txt", customer_merge_data)
            html_body = render_to_string("email/order/customer/customer_new_order.html", customer_merge_data)

            msg = EmailMultiAlternatives(
                subject=subject, from_email=settings.FROM_EMAIL,
                to=[order.address.email], body=text_body
            )
            msg.attach_alternative(html_body, "text/html")
            msg.send()

            # Send Order Emails to Vendors
            for item in order.order_items():
                
                vendor_merge_data = {
                    'item': item,
                }
                subject = f"New Order!"
                text_body = render_to_string("email/order/vendor/vendor_new_order.txt", vendor_merge_data)
                html_body = render_to_string("email/order/vendor/vendor_new_order.html", vendor_merge_data)

                msg = EmailMultiAlternatives(
                    subject=subject, from_email=settings.FROM_EMAIL,
                    to=[item.vendor.email], body=text_body
                )
                msg.attach_alternative(html_body, "text/html")
                msg.send()

            return redirect(f"/payment_status/{order.order_id}/?payment_status=paid")
    
    return redirect(f"/payment_status/{order.order_id}/?payment_status=failed")
    
def get_paypal_access_token():
    token_url = 'https://api.sandbox.paypal.com/v1/oauth2/token'
    data = {'grant_type': 'client_credentials'}
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET_ID)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f'Failed to get access token from PayPal. Status code: {response.status_code}') 

def payment_status(request, order_id):
    order = store_models.Order.objects.get(order_id=order_id)
    payment_status = request.GET.get("payment_status")

    context = {
        "order": order,
        "payment_status": payment_status
    }
    return render(request, "store/payment_status.html", context)

def filter_products(request):
    products = store_models.Product.objects.all()

    # Get filters from the AJAX request
    categories = request.GET.getlist('categories[]')
    rating = request.GET.getlist('rating[]')
    sizes = request.GET.getlist('sizes[]')
    colors = request.GET.getlist('colors[]')
    price_order = request.GET.get('prices')
    search_filter = request.GET.get('searchFilter')
    display = request.GET.get('display')

    print("categories =======", categories)
    print("rating =======", rating)
    print("sizes =======", sizes)
    print("colors =======", colors)
    print("price_order =======", price_order)
    print("search_filter =======", search_filter)
    print("display =======", display)

   
    # Apply category filtering
    if categories:
        products = products.filter(category__id__in=categories)

    # Apply rating filtering
    if rating:
        products = products.filter(reviews__rating__in=rating).distinct()

    

    # Apply size filtering
    if sizes:
        products = products.filter(variant__variant_items__content__in=sizes).distinct()

    # Apply color filtering
    if colors:
        products = products.filter(variant__variant_items__content__in=colors).distinct()

    # Apply price ordering
    if price_order == 'lowest':
        products = products.order_by('-price')
    elif price_order == 'highest':
        products = products.order_by('price')

    # Apply search filter
    if search_filter:
        products = products.filter(name__icontains=search_filter)

    if display:
        products = products.filter()[:int(display)]


    # Render the filtered products as HTML using render_to_string
    html = render_to_string('partials/_store.html', {'products': products})

    return JsonResponse({'html': html, 'product_count': products.count()})

def order_tracker_page(request):
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        return redirect("store:order_tracker_detail", item_id)
    
    return render(request, "store/order_tracker_page.html")

def order_tracker_detail(request, item_id):
    try:
        item = store_models.OrderItem.objects.filter(models.Q(item_id=item_id) | models.Q(tracking_id=item_id)).first()
    except:
        item = None
        messages.error(request, "Order not found!")
        return redirect("store:order_tracker_page")
    
    context = {
        "item": item,
    }
    return render(request, "store/order_tracker.html", context)

def about(request):
    return render(request, "pages/about.html")

def contact(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        userauths_models.ContactMessage.objects.create(
            full_name=full_name,
            email=email,
            subject=subject,
            message=message,
        )
        messages.success(request, "Message sent successfully")
        return redirect("store:contact")
    return render(request, "pages/contact.html")

def faqs(request):
    return render(request, "pages/faqs.html")

def privacy_policy(request):
    return render(request, "pages/privacy_policy.html")

def terms_conditions(request):
    return render(request, "pages/terms_conditions.html")


def cart(request):
    cart_id = request.session.get("cart_id")

    if not cart_id:
        messages.warning(request, "Your cart is empty.")
        return redirect("store:index")

    items = store_models.Cart.objects.filter(cart_id=cart_id)
    cart_sub_total = items.aggregate(sub_total=models.Sum("sub_total"))['sub_total']

    try:
        addresses = customer_models.Address.objects.filter(user=request.user)
    except:
        addresses = None

    if not items.exists():
        messages.warning(request, "No items in cart")
        return redirect("store:index")

    context = {
        "items": items,
        "cart_sub_total": cart_sub_total,
        "addresses": addresses,
    }

    return render(request, "store/cart.html", context)
