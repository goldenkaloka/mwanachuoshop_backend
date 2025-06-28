from django.core.mail import send_mail
from django.db.models import Count
from .models import WhatsAppClick, Product
from django.utils import timezone
from datetime import timedelta

def send_whatsapp_click_report():
    # Get clicks from the last 7 days (adjust as needed)
    one_week_ago = timezone.now() - timedelta(days=7)
    click_data = WhatsAppClick.objects.filter(
        clicked_at__gte=one_week_ago
    ).values(
        'product__name'
    ).annotate(
        click_count=Count('id')
    ).order_by('-click_count')

    # Prepare email content
    subject = 'Weekly WhatsApp Click Report'
    message = 'WhatsApp Click Report (Last 7 Days):\n\n'
    for entry in click_data:
        message += f"Product: {entry['product__name']}, Clicks: {entry['click_count']}\n"
    
    # Send email (configure recipient and email settings in Django settings)
    send_mail(
        subject=subject,
        message=message,
        from_email='goldenkaloka@gmail.com',
        recipient_list=['goldenkaloka@gmail.com'],
        fail_silently=False,
    )