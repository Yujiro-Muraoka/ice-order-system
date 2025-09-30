from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import ShavedIceOrder


class ShavedIceOrderModelTest(TestCase):
    """かき氷注文モデルのテスト"""
    
    def setUp(self):
        """テスト用データの準備"""
        self.shavedice_order = ShavedIceOrder.objects.create(
            flavor='matcha',
            clip_color='yellow',
            clip_number=1,
            group_id='shavedice_test_001',
            status='ok'
        )
    
    def test_shavedice_order_creation(self):
        """かき氷注文作成のテスト"""
        self.assertEqual(self.shavedice_order.flavor, 'matcha')
        self.assertEqual(self.shavedice_order.clip_color, 'yellow')
        self.assertEqual(self.shavedice_order.clip_number, 1)
        self.assertEqual(self.shavedice_order.group_id, 'shavedice_test_001')
        self.assertEqual(self.shavedice_order.status, 'ok')
        self.assertFalse(self.shavedice_order.is_completed)
    
    def test_shavedice_order_completion(self):
        """かき氷注文完了のテスト"""
        self.assertIsNone(self.shavedice_order.completed_at)
        self.shavedice_order.is_completed = True
        self.shavedice_order.completed_at = timezone.now()
        self.shavedice_order.save()
        self.assertTrue(self.shavedice_order.is_completed)
        self.assertIsNotNone(self.shavedice_order.completed_at)
    
    def test_shavedice_flavors(self):
        """各フレーバーの注文テスト"""
        flavors = ['matcha', 'ichigo', 'yuzu']
        for flavor in flavors:
            order = ShavedIceOrder.objects.create(
                flavor=flavor,
                clip_color='white',
                clip_number=2,
                group_id=f'test_{flavor}_001'
            )
            self.assertEqual(order.flavor, flavor)


class ShavedIceOrderViewTest(TestCase):
    """かき氷注文ビューのテスト"""
    
    def setUp(self):
        """テスト用クライアントとデータの準備"""
        self.client = Client()
        self.test_order = ShavedIceOrder.objects.create(
            flavor='matcha',
            clip_color='yellow',
            clip_number=1,
            group_id='view_test_001'
        )
    
    def test_shavedice_register_view(self):
        """かき氷注文登録画面のテスト"""
        response = self.client.get(reverse('shavedice_register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '抹茶')
        self.assertContains(response, 'いちご')
        self.assertContains(response, 'ゆず')
    
    def test_shavedice_kitchen_view(self):
        """かき氷キッチン画面のテスト"""
        response = self.client.get(reverse('shavedice_kitchen'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_order.group_id)
    
    def test_complete_shavedice_order(self):
        """かき氷注文完了処理のテスト"""
        response = self.client.post(reverse('complete_shavedice_order', args=[self.test_order.id]))
        self.assertEqual(response.status_code, 302)
        
        updated_order = ShavedIceOrder.objects.get(id=self.test_order.id)
        self.assertTrue(updated_order.is_completed)
        self.assertIsNotNone(updated_order.completed_at)
