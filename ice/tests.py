from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Order
import json


class IceOrderModelTest(TestCase):
    """アイスクリーム注文モデルのテスト"""
    
    def setUp(self):
        """テスト用データの準備"""
        self.ice_order = Order.objects.create(
            group_id='ice_test_001',
            size='S',
            container='cup',
            flavor1='jersey',
            clip_color='yellow',
            clip_number=1,
            status='ok'
        )
    
    def test_ice_order_creation(self):
        """注文作成のテスト"""
        self.assertEqual(self.ice_order.group_id, 'ice_test_001')
        self.assertEqual(self.ice_order.size, 'S')
        self.assertEqual(self.ice_order.container, 'cup')
        self.assertEqual(self.ice_order.flavor1, 'jersey')
        self.assertFalse(self.ice_order.is_completed)
        self.assertEqual(self.ice_order.status, 'ok')
    
    def test_double_ice_order(self):
        """ダブルアイス注文のテスト"""
        double_order = Order.objects.create(
            group_id='ice_test_002',
            size='W',
            container='cone',
            flavor1='jersey',
            flavor2='chocolate',
            clip_color='white',
            clip_number=2
        )
        self.assertEqual(double_order.size, 'W')
        self.assertEqual(double_order.flavor2, 'chocolate')
    
    def test_ice_order_completion(self):
        """注文完了のテスト"""
        self.assertIsNone(self.ice_order.completed_at)
        self.ice_order.is_completed = True
        self.ice_order.completed_at = timezone.now()
        self.ice_order.save()
        self.assertTrue(self.ice_order.is_completed)
        self.assertIsNotNone(self.ice_order.completed_at)
    
    def test_pudding_order(self):
        """アフォガードプリン注文のテスト"""
        pudding_order = Order.objects.create(
            group_id='pudding_test_001',
            size='S',
            container='cup',
            flavor1='jersey',
            clip_color='yellow',
            clip_number=3,
            is_pudding=True
        )
        self.assertTrue(pudding_order.is_pudding)


class IceOrderViewTest(TestCase):
    """アイスクリーム注文ビューのテスト"""
    
    def setUp(self):
        """テスト用クライアントとデータの準備"""
        self.client = Client()
        self.test_order = Order.objects.create(
            group_id='view_test_001',
            size='S',
            container='cup',
            flavor1='jersey',
            clip_color='yellow',
            clip_number=1
        )
    
    def test_ice_register_view(self):
        """アイス注文登録画面のテスト"""
        response = self.client.get(reverse('register_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'シングル')
        self.assertContains(response, 'ダブル')
    
    def test_ice_view(self):
        """アイス作成画面のテスト"""
        response = self.client.get(reverse('ice_view'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_order.group_id)
    
    def test_add_temp_ice_valid(self):
        """仮アイス注文追加（有効データ）のテスト"""
        response = self.client.post(reverse('add_temp_ice'), {
            'size': 'S',
            'container': 'cup',
            'flavor1': 'jersey'
        })
        self.assertEqual(response.status_code, 302)
    
    def test_complete_ice_order(self):
        """アイス注文完了処理のテスト"""
        response = self.client.post(reverse('complete_order', args=[self.test_order.id]))
        self.assertEqual(response.status_code, 302)
        
        updated_order = Order.objects.get(id=self.test_order.id)
        self.assertTrue(updated_order.is_completed)
        self.assertIsNotNone(updated_order.completed_at)


class IceOrderStatusTest(TestCase):
    """アイス注文状態管理のテスト"""
    
    def setUp(self):
        self.client = Client()
        self.test_order = Order.objects.create(
            group_id='status_test_001',
            size='S',
            container='cup',
            flavor1='jersey',
            clip_color='yellow',
            clip_number=1,
            status='ok'
        )
    
    def test_update_status_to_stop(self):
        """状態をSTOPに変更するテスト"""
        response = self.client.post(reverse('update_status', args=[self.test_order.group_id, 'stop']))
        self.assertEqual(response.status_code, 302)
        
        updated_order = Order.objects.get(id=self.test_order.id)
        self.assertEqual(updated_order.status, 'stop')
    
    def test_update_status_to_hold(self):
        """状態を保留に変更するテスト"""
        response = self.client.post(reverse('update_status', args=[self.test_order.group_id, 'hold']))
        self.assertEqual(response.status_code, 302)
        
        updated_order = Order.objects.get(id=self.test_order.id)
        self.assertEqual(updated_order.status, 'hold')
