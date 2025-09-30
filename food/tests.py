from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import FoodOrder
import json


class FoodOrderModelTest(TestCase):
    """FoodOrderモデルのテスト"""
    
    def setUp(self):
        """テスト用データの準備"""
        self.food_order = FoodOrder.objects.create(
            menu='からあげ丼',
            quantity=2,
            eat_in=True,
            clip_color='yellow',
            clip_number=1,
            group_id='test_group_001',
            status='ok',
            note='テスト注文'
        )
    
    def test_food_order_creation(self):
        """注文作成のテスト"""
        self.assertEqual(self.food_order.menu, 'からあげ丼')
        self.assertEqual(self.food_order.quantity, 2)
        self.assertTrue(self.food_order.eat_in)
        self.assertEqual(self.food_order.status, 'ok')
        self.assertFalse(self.food_order.is_completed)
        self.assertEqual(self.food_order.clip_color, 'yellow')
        self.assertEqual(self.food_order.clip_number, 1)
        self.assertEqual(self.food_order.group_id, 'test_group_001')
    
    def test_food_order_str_method(self):
        """文字列表現のテスト"""
        expected = "からあげ丼 ×2 [test_group_001]"
        self.assertEqual(str(self.food_order), expected)
    
    def test_food_order_completion(self):
        """注文完了機能のテスト"""
        self.assertIsNone(self.food_order.completed_at)
        self.food_order.is_completed = True
        self.food_order.completed_at = timezone.now()
        self.food_order.save()
        self.assertTrue(self.food_order.is_completed)
        self.assertIsNotNone(self.food_order.completed_at)
    
    def test_food_order_defaults(self):
        """デフォルト値のテスト"""
        order = FoodOrder.objects.create(
            menu='ルーロー飯',
            clip_color='white',
            clip_number=2,
            group_id='test_002'
        )
        self.assertEqual(order.quantity, 1)  # デフォルト値
        self.assertTrue(order.eat_in)  # デフォルト値
        self.assertEqual(order.status, 'ok')  # デフォルト値
        self.assertFalse(order.is_completed)  # デフォルト値


class FoodOrderViewTest(TestCase):
    """FoodOrderビューのテスト"""
    
    def setUp(self):
        """テスト用クライアントとデータの準備"""
        self.client = Client()
        self.test_order = FoodOrder.objects.create(
            menu='からあげ丼',
            quantity=1,
            clip_color='yellow',
            clip_number=1,
            group_id='test_view_001'
        )
    
    def test_food_register_view(self):
        """注文登録画面のテスト"""
        response = self.client.get(reverse('food_register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'からあげ丼')
        self.assertContains(response, 'ルーロー飯')
    
    def test_add_temp_food_valid_data(self):
        """仮注文追加（有効データ）のテスト"""
        response = self.client.post(reverse('add_temp_food'), {
            'menu': 'からあげ丼',
            'eat_in': '1'
        })
        self.assertEqual(response.status_code, 302)  # リダイレクト
    
    def test_add_temp_food_invalid_data(self):
        """仮注文追加（無効データ）のテスト"""
        response = self.client.post(reverse('add_temp_food'), {
            'menu': '',  # 空のメニュー
            'eat_in': '1'
        })
        self.assertEqual(response.status_code, 302)  # エラー時のリダイレクト
    
    def test_food_kitchen_view(self):
        """キッチン画面のテスト"""
        response = self.client.get(reverse('food_kitchen'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_order.menu)
    
    def test_complete_food_order(self):
        """注文完了処理のテスト"""
        response = self.client.post(reverse('complete_food_order', args=[self.test_order.id]))
        self.assertEqual(response.status_code, 302)
        
        # 注文が完了しているかチェック
        updated_order = FoodOrder.objects.get(id=self.test_order.id)
        self.assertTrue(updated_order.is_completed)
        self.assertIsNotNone(updated_order.completed_at)


class FoodOrderSessionTest(TestCase):
    """セッション関連のテスト"""
    
    def setUp(self):
        self.client = Client()
    
    def test_temp_food_session_storage(self):
        """仮注文のセッション保存テスト"""
        # 仮注文を追加
        self.client.post(reverse('add_temp_food'), {
            'menu': 'からあげ丼',
            'eat_in': '1'
        })
        
        # セッションに保存されているかチェック
        session = self.client.session
        self.assertIn('temp_food', session)
        self.assertEqual(len(session['temp_food']), 1)
        self.assertEqual(session['temp_food'][0]['menu'], 'からあげ丼')
    
    def test_submit_temp_food_orders(self):
        """仮注文の本注文化テスト"""
        # 仮注文をセッションに追加
        session = self.client.session
        session['temp_food'] = [{
            'menu': 'からあげ丼',
            'eat_in': True
        }]
        session.save()
        
        # 本注文として送信
        response = self.client.post(reverse('submit_temp_food_orders'), {
            'clip_color': 'yellow',
            'clip_number': '1'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # データベースに保存されているかチェック
        orders = FoodOrder.objects.all()
        self.assertEqual(orders.count(), 1)
        self.assertEqual(orders.first().menu, 'からあげ丼')
