from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone

from common.orders import visible_orders
from food.models import FoodOrder
from food.views import _get_food_order_context
from ice.models import Order
from ice.views import _update_hold_status, complete_group
from shavedice.models import ShavedIceOrder


class OrderRegressionTests(TestCase):
    def setUp(self):
        self.food = FoodOrder.objects.create(menu='からあげ', clip_color='yellow', clip_number=1, group_id='food')
        self.ice = Order.objects.create(size='S', container='cup', flavor1='jersey', clip_color='yellow', clip_number=1, group_id='ice')
        self.shaved = ShavedIceOrder.objects.create(flavor='🍧抹茶🍧', group_id='shaved')
        session = self.client.session
        session['logged_in'] = True
        session.save()

    def test_all_screens_render(self):
        paths = ['/', '/login/', '/register/', '/ice/', '/deshap/',
                 '/ice/register/', '/ice/ice/', '/ice/deshap/',
                 '/food/register/', '/food/kitchen/', '/food/deshap/', '/food/waittime/',
                 '/shavedice/register/', '/shavedice/kitchen/', '/shavedice/ice/',
                 '/shavedice/deshap/', '/shavedice/waittime/', '/mobile/', '/mobile/complete/',
                 f'/detail/{self.ice.pk}/', f'/shavedice/detail/{self.shaved.pk}/']
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_polling_endpoints(self):
        for path in ['/food/kitchen/', '/food/deshap/', '/ice/', '/deshap/', '/shavedice/kitchen/', '/shavedice/deshap/']:
            with self.subTest(path=path):
                response = self.client.get(path, {'format': 'json'})
                self.assertEqual(response.status_code, 200)
                self.assertIn('value', response.json())

    def test_ice_reverse_names_do_not_target_shaved_ice(self):
        for name, args in [('add_temp_ice', []), ('submit_order_group', []), ('complete_group', ['ice']), ('order_detail', [1]), ('delete_group', ['ice']), ('delete_temp_ice', [0]), ('ice', [])]:
            with self.subTest(name=name):
                self.assertFalse(reverse(name, args=args).startswith('/shavedice/'))

    def test_carts_and_submission_are_independent(self):
        self.client.post('/add_temp_ice/', {'size': 'S', 'container': 'cup', 'flavor1': 'jersey'})
        self.client.post('/shavedice/add_temp_ice/', {'flavor': '🍧抹茶🍧'})
        self.assertEqual(len(self.client.session['temp_ice']), 1)
        self.assertEqual(len(self.client.session['temp_shavedice']), 1)
        self.client.post('/shavedice/submit_order_group/', {'clip_color': 'white', 'clip_number': '2'})
        self.assertEqual(len(self.client.session['temp_ice']), 1)
        self.assertEqual(self.client.session['temp_shavedice'], [])
        self.client.post('/submit_order_group/', {'clip_color': 'yellow', 'clip_number': '3'})
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(ShavedIceOrder.objects.count(), 2)
        self.assertLessEqual(len(Order.objects.get(clip_number=3).group_id), 20)

    def test_legacy_mixed_cart_is_preserved(self):
        session = self.client.session
        session['temp_ice'] = [{'flavor': '🍧抹茶🍧'}, {'is_pudding': True}]
        session.save()
        self.client.get('/register/')
        self.assertEqual(self.client.session['temp_ice'], [{'is_pudding': True}])
        self.assertEqual(self.client.session['temp_shavedice'], [{'flavor': '🍧抹茶🍧'}])
        self.client.get('/shavedice/register/')
        self.assertEqual(len(self.client.session['temp_shavedice']), 1)

    def test_food_groups_are_unique_even_at_same_time(self):
        with patch('time.time', return_value=1800000000):
            for _ in range(2):
                self.client.post('/food/add_temp_food/', {'menu': 'からあげ', 'quantity': '2', 'eat_in': '1'})
                self.client.post(reverse('submit_temp_food_orders'), {'clip_color': 'yellow', 'clip_number': '2'})
        self.assertEqual(FoodOrder.objects.filter(clip_number=2).values('group_id').distinct().count(), 2)

    def test_history_query_preserves_partial_groups_but_excludes_old_groups(self):
        now = timezone.now()
        old = now - timedelta(days=1)
        completed = FoodOrder.objects.create(menu='ルーロー飯', clip_color='yellow', clip_number=1, group_id='food', is_completed=True, completed_at=old)
        hidden = FoodOrder.objects.create(menu='からあげ', clip_color='white', clip_number=2, group_id='old', is_completed=True, completed_at=old)
        with self.assertNumQueries(1):
            ids = {o.pk for o in visible_orders(FoodOrder, now)}
        self.assertIn(completed.pk, ids)
        self.assertIn(self.food.pk, ids)
        self.assertNotIn(hidden.pk, ids)
        html = self.client.get('/food/kitchen/').content.decode()
        self.assertIn('✅ 完了済み', html)
        self.assertNotIn(f'action="/food/complete_order/{completed.pk}/"', html)

    def test_countdown_uses_last_completion_not_last_created_item(self):
        now = timezone.now()
        FoodOrder.objects.filter(pk=self.food.pk).update(is_completed=True, completed_at=now)
        FoodOrder.objects.create(menu='ルーロー飯', clip_color='yellow', clip_number=1, group_id='food', is_completed=True, completed_at=now-timedelta(seconds=20))
        orders = _get_food_order_context()['completed_orders']['food']
        self.assertEqual(orders[-1].group_completed_at, now)
        self.assertContains(self.client.get('/food/kitchen/'), timezone.localtime(now).isoformat(), html=False)

    def test_hold_threshold_counts_groups_not_items(self):
        Order.objects.filter(pk=self.ice.pk).update(status='hold')
        for _ in range(4):
            Order.objects.create(size='S', container='cup', flavor1='jersey', clip_color='yellow', clip_number=1, group_id='ice', status='hold')
        _update_hold_status()
        self.assertFalse(Order.objects.filter(status='stop').exists())

    def test_group_completion_is_one_write_and_idempotent(self):
        request = RequestFactory().post('/')
        with self.assertNumQueries(1):
            complete_group(request, 'ice')
        self.ice.refresh_from_db()
        completed_at = self.ice.completed_at
        complete_group(request, 'ice')
        self.ice.refresh_from_db()
        self.assertEqual(self.ice.completed_at, completed_at)

    def test_invalid_status_does_not_corrupt_orders(self):
        for path, order in [('/update_status/ice/bogus/', self.ice), ('/shavedice/update_status/shaved/bogus/', self.shaved)]:
            self.client.post(path)
            order.refresh_from_db()
            self.assertEqual(order.status, 'ok')

    def test_production_static_files_are_served(self):
        from tempfile import TemporaryDirectory
        from django.core.management import call_command
        from django.test import Client, override_settings
        with TemporaryDirectory() as static_root:
            with override_settings(DEBUG=False, STATIC_ROOT=static_root):
                call_command('collectstatic', interactive=False, verbosity=0)
                client = Client()
                for asset in ['js/auto-refresh.js', 'food/base_cafe.css', 'sounds/notify.mp3']:
                    with self.subTest(asset=asset):
                        response = client.get('/static/' + asset)
                        self.assertEqual(response.status_code, 200)
                        response.close()
