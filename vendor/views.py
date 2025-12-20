# vendor/views.py
from django.http import JsonResponse, Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.db.models.functions import TruncMonth
from django.db.models import Count, Q
import json

from plugin.paginate_queryset import paginate_queryset
from store import models as store_models
from vendor import models as vendor_models
from django.contrib.auth import get_user_model
from functools import wraps
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
import json

User = get_user_model()
def vendor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            _ = request.user.vendor
        except vendor_models.Vendor.DoesNotExist:
            messages.error(request, "You do not have permission to access this page.")
            return redirect("store:index")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# --------------------------------------------------
#  Helpers
# --------------------------------------------------
def get_monthly_sales():
    return (
        store_models.OrderItem.objects
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(order_count=Count("id"))
        .order_by("month")
    )

# --------------------------------------------------
#  DashBoard
# --------------------------------------------------
# vendor/views.py
@login_required
@vendor_required
def dashboard(request):
    try:
        vendor = request.user.vendor
    except vendor_models.Vendor.DoesNotExist:
        messages.error(request, "Bạn chưa có tài khoản Vendor!")
        return redirect("store:index")

    products = store_models.Product.objects.filter(vendor=vendor)

    low_stock_products = products.filter(stock__gt=0, stock__lte=5)
    out_of_stock_products = products.filter(stock=0)

    order_items = (
        store_models.OrderItem.objects
        .select_related("order__customer", "product")
        .filter(
            vendor=request.user,
            order__payment_status__in=["Paid", "Processing"],
        )
        .order_by("-date")
    )

    # ORDER STATUS
    orders_pending = order_items.filter(order_status="Pending").count()
    orders_processing = order_items.filter(order_status="Processing").count()
    orders_shipped = order_items.filter(order_status="Shipped").count()
    orders_cancelled = order_items.filter(order_status="Cancelled").count()

    # ================= ANALYTICS =================
    monthly_orders = (
        order_items
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )

    labels = [m["month"].strftime("%b %Y") for m in monthly_orders if m["month"]]
    data = [m["total"] for m in monthly_orders]

    total_orders = order_items.count()
    total_items_sold = order_items.aggregate(total=Sum("qty"))["total"] or 0

    top_products = (
        order_items
        .values("product__name")
        .annotate(total=Sum("qty"))
        .order_by("-total")[:5]
    )

    return render(
        request,
        "vendor/dashboard.html",
        {
            "products": products,
            "order_items": order_items,

            "low_stock_products": low_stock_products,
            "out_of_stock_products": out_of_stock_products,

            "orders_pending": orders_pending,
            "orders_processing": orders_processing,
            "orders_shipped": orders_shipped,
            "orders_cancelled": orders_cancelled,

            # ANALYTICS
            "labels": json.dumps(labels),
            "data": json.dumps(data),
            "total_orders": total_orders,
            "total_items_sold": total_items_sold,
            "top_products": top_products,
        }
    )


# --------------------------------------------------
#  Product list
# --------------------------------------------------
@login_required
@vendor_required
def products(request):
    try:
        vendor = request.user.vendor
    except vendor_models.Vendor.DoesNotExist:
        messages.error(request, "Bạn chưa có tài khoản Vendor!")
        return redirect("vendor:dashboard")

    products_qs = store_models.Product.objects.filter(vendor=vendor)
    products = paginate_queryset(request, products_qs, 10)

    return render(
        request,
        "vendor/products.html",
        {"products": products, "products_list": products_qs},
    )

# --------------------------------------------------
#  Orders
# --------------------------------------------------
# =========================
# VENDOR ORDERS (FIXED)
# =========================

@login_required
@vendor_required
def orders(request):
    """
    Vendor chỉ xem OrderItem của chính mình
    """
    order_items_qs = (
        store_models.OrderItem.objects
        .select_related("order", "product", "product__vendor")
        .filter(
            vendor=request.user,
            order__payment_status__in=["Paid", "Processing"]
        )
        .exclude(order_status="Cancelled") 
        .order_by("-date")
    )

    order_items = paginate_queryset(request, order_items_qs, 10)

    return render(
        request,
        "vendor/orders.html",
        {
            "order_items": order_items,
            "order_items_list": order_items_qs,
        }
    )


@login_required
@vendor_required
def order_detail(request, order_id):
    """
    Vendor xem chi tiết 1 đơn (chỉ item của mình)
    """
    order_items = (
        store_models.OrderItem.objects
        .select_related("order", "product", "product__vendor")
        .filter(
            vendor=request.user,
            order__order_id=order_id,
            order__payment_status__in=["Paid", "Processing"]
        )
    )

    if not order_items.exists():
        raise Http404("Order not found")

    order = order_items.first().order

    return render(
        request,
        "vendor/order_detail.html",
        {
            "order": order,
            "order_items": order_items,
        }
    )


@login_required
@vendor_required
def order_item_detail(request, order_id, item_id):
    """
    Vendor xem chi tiết 1 item
    """
    item = get_object_or_404(
        store_models.OrderItem,
        item_id=item_id,
        vendor=request.user,
        order__order_id=order_id,
        order__payment_status__in=["Paid", "Processing"],
    )

    return render(
        request,
        "vendor/order_item_detail.html",
        {
            "item": item,
            "order": item.order,
        }
    )


@login_required
@vendor_required
def update_order_item_status(request, order_id, item_id):
    item = get_object_or_404(
        store_models.OrderItem,
        item_id=item_id,
        vendor=request.user,
        order__order_id=order_id,
    )

    if request.method == "POST":
        item.order_status     = request.POST.get("order_status")
        item.shipping_service = request.POST.get("shipping_service")
        item.tracking_id      = request.POST.get("tracking_id")
        item.save()

        messages.success(request, "Item status updated successfully")

    return redirect("vendor:orders")

from django.urls import reverse

@login_required
@vendor_required
def cancel_order_item(request, order_id, item_id):
    item = get_object_or_404(
        store_models.OrderItem,
        item_id=item_id,
        vendor=request.user,
        order__order_id=order_id,
    )

    if request.method == "POST":
        item.order_status = "Cancelled"
        item.save()
        messages.success(request, "Order item cancelled successfully")

    return redirect("vendor:orders")




# --------------------------------------------------
#  Coupons
# --------------------------------------------------
@login_required
@vendor_required
def coupons(request):
    vendor = request.user.vendor
    coupons_qs = store_models.Coupon.objects.filter(vendor=vendor)
    coupons = paginate_queryset(request, coupons_qs, 10)
    return render(
        request,
        "vendor/coupons.html",
        {"coupons": coupons, "coupons_list": coupons_qs},
    )

@login_required
@vendor_required
def update_coupon(request, id):
    coupon = get_object_or_404(store_models.Coupon, vendor=request.user.vendor, id=id)
    if request.method == "POST":
        coupon.code = request.POST.get("coupon_code")
        coupon.save()
        messages.success(request, "Coupon updated")
    return redirect("vendor:coupons")

@login_required
@vendor_required
def delete_coupon(request, id):
    coupon = get_object_or_404(store_models.Coupon, vendor=request.user.vendor, id=id)
    coupon.delete()
    messages.success(request, "Coupon deleted")
    return redirect("vendor:coupons")

@login_required
@vendor_required
def create_coupon(request):
    if request.method == "POST":
        store_models.Coupon.objects.create(
            vendor   = request.user.vendor,
            code     = request.POST.get("coupon_code"),
            discount = request.POST.get("coupon_discount"),
        )
        messages.success(request, "Coupon created")
    return redirect("vendor:coupons")

# --------------------------------------------------
#  Reviews
# --------------------------------------------------
@login_required
@vendor_required
def reviews(request):
    reviews_qs = store_models.Review.objects.filter(product__vendor=request.user.vendor)

    rating = request.GET.get("rating")
    order  = request.GET.get("date")

    if rating:
        reviews_qs = reviews_qs.filter(rating=rating)
    if order:
        reviews_qs = reviews_qs.order_by(order)

    reviews = paginate_queryset(request, reviews_qs, 10)
    return render(
        request,
        "vendor/reviews.html",
        {"reviews": reviews, "reviews_list": reviews_qs},
    )

@login_required
@vendor_required
def update_reply(request, id):
    review = get_object_or_404(store_models.Review, id=id)
    if request.method == "POST":
        review.reply = request.POST.get("reply")
        review.save()
        messages.success(request, "Reply added")
    return redirect("vendor:reviews")

# --------------------------------------------------
#  Notifications
# --------------------------------------------------
@login_required
@vendor_required
def notis(request):
    notis_qs = vendor_models.Notifications.objects.filter(user=request.user, seen=False)
    notis = paginate_queryset(request, notis_qs, 10)
    return render(request, "vendor/notis.html", {"notis": notis, "notis_list": notis_qs})

@login_required
@vendor_required
def mark_noti_seen(request, id):
    noti = get_object_or_404(vendor_models.Notifications, user=request.user, id=id)
    noti.seen = True
    noti.save()
    messages.success(request, "Notification marked as seen")
    return redirect("vendor:notis")

# --------------------------------------------------
#  Profile & Password
# --------------------------------------------------
@login_required
@vendor_required
def profile(request):
    profile = request.user.profile
    if request.method == "POST":
        if (image := request.FILES.get("image")):
            profile.image = image
        profile.full_name = request.POST.get("full_name")
        profile.mobile    = request.POST.get("mobile")
        profile.save()
        messages.success(request, "Profile Updated Successfully")
        return redirect("vendor:profile")
    return render(request, "vendor/profile.html", {"profile": profile})

@login_required

def change_password(request):
    if request.method == "POST":
        old = request.POST.get("old_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_new_password")

        if new != confirm:
            messages.error(request, "Confirm Password and New Password do not match")
        elif check_password(old, request.user.password):
            request.user.set_password(new)
            request.user.save()
            messages.success(request, "Password Changed Successfully")
        else:
            messages.error(request, "Old password is incorrect")
        return redirect("vendor:change_password")

    return render(request, "vendor/change_password.html")

# --------------------------------------------------
#  Product CRUD
# --------------------------------------------------
@login_required
@vendor_required
def create_product(request):
    categories = store_models.Category.objects.all()

    if request.method == "POST":
        vendor = request.user.vendor
        store_models.Product.objects.create(
            vendor        = vendor,
            image         = request.FILES.get("image"),
            name          = request.POST.get("name"),
            category_id   = request.POST.get("category_id"),
            description   = request.POST.get("description"),
            price         = request.POST.get("price"),
            regular_price = request.POST.get("regular_price"),
            shipping      = request.POST.get("shipping"),
            stock         = request.POST.get("stock"),
        )
        messages.success(request, "Product created successfully")
        return redirect("vendor:products")

    return render(request, "vendor/create_product.html", {"categories": categories})

@login_required
@vendor_required
def update_product(request, id):
    product = get_object_or_404(
        store_models.Product, id=id, vendor=request.user.vendor
    )
    categories = store_models.Category.objects.all()

    if request.method == "POST":
        product.name          = request.POST.get("name")
        product.category_id   = request.POST.get("category_id")
        product.description   = request.POST.get("description")
        product.price         = request.POST.get("price")
        product.regular_price = request.POST.get("regular_price")
        product.shipping      = request.POST.get("shipping")
        product.stock         = request.POST.get("stock")
        if (image := request.FILES.get("image")):
            product.image = image
        product.save()

        # --------------- Variants ---------------
        variant_ids    = request.POST.getlist("variant_id[]")
        variant_titles = request.POST.getlist("variant_title[]")

        for i, title in enumerate(variant_titles):
            vid = variant_ids[i]
            variant = (
                store_models.Variant.objects.filter(id=vid).first()
                if vid else
                store_models.Variant.objects.create(product=product, name=title)
            )
            variant.name = title
            variant.save()

            item_ids   = request.POST.getlist(f"item_id_{i}[]")
            item_titles= request.POST.getlist(f"item_title_{i}[]")
            item_descs = request.POST.getlist(f"item_description_{i}[]")

            for j, it_title in enumerate(item_titles):
                iid = item_ids[j]
                item = (
                    store_models.VariantItem.objects.filter(id=iid).first()
                    if iid else
                    store_models.VariantItem.objects.create(variant=variant)
                )
                item.title   = it_title
                item.content = item_descs[j]
                item.save()

        # --------------- Gallery images ---------------
        for key, f in request.FILES.items():
            if key.startswith("image_"):
                store_models.Gallery.objects.create(product=product, image=f)

        messages.success(request, "Product updated")
        return redirect("vendor:update_product", product.id)

    return render(
        request,
        "vendor/update_product.html",
        {
            "product": product,
            "categories": categories,
            "variants": store_models.Variant.objects.filter(product=product),
            "gallery_images": store_models.Gallery.objects.filter(product=product),
        },
    )

# --------------- Ajax helpers ---------------
@login_required
@vendor_required
def delete_variants(request, product_id, variant_id):
    variant = get_object_or_404(
        store_models.Variant,
        id=variant_id,
        product_id=product_id,
        product__vendor=request.user.vendor,
    )
    variant.delete()
    return JsonResponse({"message": "Variants deleted"})

@login_required
@vendor_required
def delete_variants_items(request, variant_id, item_id):
    item = get_object_or_404(
        store_models.VariantItem,
        id=item_id,
        variant_id=variant_id,
        variant__product__vendor=request.user.vendor,
    )
    item.delete()
    return JsonResponse({"message": "Variant Item deleted"})

@login_required
@vendor_required
def delete_product_image(request, product_id, image_id):
    image = get_object_or_404(
        store_models.Gallery,
        id=image_id,
        product_id=product_id,
        product__vendor=request.user.vendor,
    )
    image.delete()
    return JsonResponse({"message": "Product Image deleted"})

@login_required
@vendor_required
def delete_product(request, product_id):
    product = get_object_or_404(
        store_models.Product, id=product_id, vendor=request.user.vendor
    )
    product.delete()
    messages.success(request, "Product deleted")
    return redirect("vendor:products")
