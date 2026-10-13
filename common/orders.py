"""Shared queries for the live order boards."""
from datetime import timedelta
from django.db.models import Q


def visible_orders(model, now):
    visible_groups = model.objects.filter(
        Q(is_completed=False) | Q(completed_at__gte=now - timedelta(seconds=30))
    ).order_by().values('group_id')
    return model.objects.filter(group_id__in=visible_groups).order_by('timestamp', 'id')


def migrate_legacy_cart(session):
    """Preserve shaved-ice items from the formerly shared cart."""
    old_cart = session.get('temp_ice', [])
    shaved = [item for item in old_cart if 'flavor' in item]
    if shaved:
        session['temp_shavedice'] = session.get('temp_shavedice', []) + shaved
        session['temp_ice'] = [item for item in old_cart if 'flavor' not in item]
