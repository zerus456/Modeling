from pathlib import Path
from datetime import timedelta
from environs import Env
import os
from django.contrib import messages

env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-&)0dbnucsu)$f4pgxd0ombb4)b+oj2ci9mi=yno-veu%^doqh!'

DEBUG = True

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1', 'https://*.ngrok-free.app', 'https://fastcart.up.railway.app']
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin-allow-popups'

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',

    'userauths',
    'store',
    'vendor',
    'customer',
    'blog',

    'django_ckeditor_5',
    'anymail',
    # 'captcha',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecom_prj.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'store.context.default',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecom_prj.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env("POSTGRES_DB", default="ecommerce_wb"),
        'USER': env("POSTGRES_USER", default="postgres"),
        'PASSWORD': env("POSTGRES_PASSWORD", default="ducan06112004"),
        'HOST': env("POSTGRES_HOST", default="localhost"),
        'PORT': env("POSTGRES_PORT", default="5432"),
    }
}



AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

AUTH_USER_MODEL = 'userauths.User'

# Stripe (mặc định là rỗng nếu không có)
# Stripe API Keys (Không cần nếu bạn không dùng Stripe)
STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")

# Paypal API Keys
PAYPAL_CLIENT_ID = env("PAYPAL_CLIENT_ID", default="")
PAYPAL_SECRET_ID = env("PAYPAL_SECRET_ID", default="")

# Flutterwave Keys
FLUTTERWAVE_PUBLIC_KEY = env("FLUTTERWAVE_PUBLIC_KEY", default="")
FLUTTERWAVE_PRIVATE_KEY = env("FLUTTERWAVE_PRIVATE_KEY", default="")

# Paystack Keys
PAYSTACK_PUBLIC_KEY = env("PAYSTACK_PUBLIC_KEY", default="")
PAYSTACK_PRIVATE_KEY = env("PAYSTACK_PRIVATE_KEY", default="")

# Razorpay keys
RAZORPAY_KEY_ID = env("RAZORPAY_KEY_ID", default="")
RAZORPAY_KEY_SECRET = env("RAZORPAY_KEY_SECRET", default="")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email cấu hình mặc định
FROM_EMAIL = env("FROM_EMAIL", default="")
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")
SERVER_EMAIL = env("SERVER_EMAIL", default="")

ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.environ.get("MAILGUN_SENDER_DOMAIN"),
}

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

GRAPH_MODELS = {
    'all_applications': True,
    'graph_models': True,
}

LOGIN_URL = "userauths:sign-in"
LOGIN_REDIRECT_URL = ""
LOGOUT_REDIRECT_URL = "userauths:sign-in"



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Tùy chỉnh giao diện admin (Jazzmin) – không cần chỉnh nếu chưa dùng
JAZZMIN_SETTINGS = {
    "site_title": "FastCart Ecommerce",
    "site_header": "FastCart Ecommerce",
    "site_brand": "FastCart Ecommerce ",
    "welcome_sign": "Welcome To Desphixs",
    "copyright": "Desphixs",
    "user_avatar": "images/photos/logo.jpg",
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": [
        "store", "store.product", "store.cartorder", "store.cartorderitem", "store.cart",
        "store.category", "store.brand", "store.productfaq", "store.review", "vendor.Coupon",
        "vendor.DeliveryCouriers", "userauths", "userauths.user", "userauths.profile", "donations",
        "blog", 'newsfeed', "contacts", "addon"
    ],
    "icons": {
        "admin.LogEntry": "fas fa-file",
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "userauths.User": "fas fa-user",
        "userauths.Profile": "fas fa-address-card",
        "donations.Donation": "fas fa-hand-holding-usd",
        "donations.Payment": "fas fa-credit-card",
        "newsfeed.Newsletter": "fas fa-envelope",
        "contacts.Inquiry": "fas fa-phone",
        "addon.BasicAddon": "fas fa-cog",
        "store.Product": "fas fa-th",
        "store.CartOrder": "fas fa-shopping-cart",
        "store.Cart": "fas fa-cart-plus",
        "store.CartOrderItem": "fas fa-shopping-basket",
        "store.Brand": "fas fa-check-circle",
        "store.productfaq": "fas fa-question",
        "store.Review": "fas fa-star fa-beat",
        "store.Category": "fas fa-tag",
        "store.Tag": "fas fa-tag",
        "store.Notification": "fas fa-bell",
        "customer.Address": "fas fa-location-arrow",
        "customer.Wishlist": "fas fa-heart",
        "vendor.DeliveryCouriers": "fas fa-truck",
        "vendor.Coupon": "fas fa-percentage",
        "vendor.Vendor": "fas fa-store",
        "vendor.Notification": "fas fa-bell",
        "vendor.PayoutTracker": "fas fa-wallet",
        "vendor.ChatMessage": "fas fa-envelope",
        "addons.BecomeAVendor": "fas fa-user-plus",
        "addons.AboutUS": "fas fa-users",
        "addons.Company": "fas fa-university",
        "addons.BasicAddon": "fas fa-cog",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-arrow-circle-right",
    "related_modal_active": False,
    "custom_js": None,
    "show_ui_builder": True,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
}

# Cấu hình CKEditor
customColorPalette = [
    {"color": "hsl(4, 90%, 58%)", "label": "Red"},
    {"color": "hsl(340, 82%, 52%)", "label": "Pink"},
    {"color": "hsl(291, 64%, 42%)", "label": "Purple"},
    {"color": "hsl(262, 52%, 47%)", "label": "Deep Purple"},
    {"color": "hsl(231, 48%, 48%)", "label": "Indigo"},
    {"color": "hsl(207, 90%, 54%)", "label": "Blue"},
]

CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|", "bold", "italic", "link", "bulletedList", "numberedList", "blockQuote", "imageUpload"
        ],
    },
    "comment": {
        "language": {"ui": "en", "content": "en"},
        "toolbar": [
            "heading", "|", "bold", "italic", "link", "bulletedList", "numberedList", "blockQuote",
        ],
    },
    "extends": {
        "language": "en",
        "blockToolbar": ["paragraph", "heading1", "heading2", "heading3", "|", "bulletedList", "numberedList", "|", "blockQuote"],
        "toolbar": [
            "bold", "italic", "underline", "|", "link", "strikethrough", "code", "subscript", "superscript",
            "highlight", "|", "bulletedList", "numberedList", "todoList", "|", "blockQuote", "insertImage",
            "|", "fontSize", "fontFamily", "fontColor", "fontBackgroundColor", "mediaEmbed", "removeFormat",
            "insertTable", "sourceEditing",
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative", "|", "imageStyle:alignLeft", "imageStyle:alignRight",
                "imageStyle:alignCenter", "imageStyle:side", "|", "toggleImageCaption", "|"
            ],
            "styles": ["full", "side", "alignLeft", "alignRight", "alignCenter"],
        },
        "table": {
            "contentToolbar": ["tableColumn", "tableRow", "mergeTableCells", "tableProperties", "tableCellProperties"],
            "tableProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
            "tableCellProperties": {
                "borderColors": customColorPalette,
                "backgroundColors": customColorPalette,
            },
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading1", "view": "h1", "title": "Heading 1", "class": "ck-heading_heading1"},
                {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
            ]
        },
        "list": {
            "properties": {
                "styles": True,
                "startIndex": True,
                "reversed": True,
            }
        },
        "htmlSupport": {
            "allow": [
                {"name": "/.*/", "attributes": True, "classes": True, "styles": True}
            ]
        },
    },
}
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_TZ = True