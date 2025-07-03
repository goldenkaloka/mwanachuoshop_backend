# shops/tasks.py
from django.db import transaction
from django.utils import timezone
from .models import Subscription, Shop
from marketplace.models import Product
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# (No background task needed for subscription expiry. Use on-demand checks in views/models.)