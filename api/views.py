"""
cafeMuji - REST API設定
DRF（Django REST Framework）を使用したAPI実装

このファイルは、モバイルアプリや外部システムとの
連携のためのREST APIを提供します。
"""

from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from food.models import FoodOrder
from ice.models import Order as IceOrder
from shavedice.models import ShavedIceOrder


# ==================== シリアライザー ====================

class FoodOrderSerializer(serializers.ModelSerializer):
    """フード注文のシリアライザー"""
    
    class Meta:
        model = FoodOrder
        fields = '__all__'
        read_only_fields = ('id', 'timestamp', 'completed_at')
    
    def validate_quantity(self, value):
        """数量の検証"""
        if value <= 0:
            raise serializers.ValidationError("数量は1以上である必要があります。")
        return value
    
    def validate_clip_number(self, value):
        """クリップ番号の検証"""
        if value < 0 or value > 16:
            raise serializers.ValidationError("クリップ番号は0-16の範囲である必要があります。")
        return value


class IceOrderSerializer(serializers.ModelSerializer):
    """アイスクリーム注文のシリアライザー"""
    
    class Meta:
        model = IceOrder
        fields = '__all__'
        read_only_fields = ('id', 'timestamp', 'completed_at')
    
    def validate(self, data):
        """全体的な検証"""
        if data.get('size') == 'W' and not data.get('flavor2'):
            raise serializers.ValidationError("ダブルサイズの場合は2つ目のフレーバーが必要です。")
        return data


class ShavedIceOrderSerializer(serializers.ModelSerializer):
    """かき氷注文のシリアライザー"""
    
    class Meta:
        model = ShavedIceOrder
        fields = '__all__'
        read_only_fields = ('id', 'timestamp', 'completed_at')


# ==================== ビューセット ====================

class FoodOrderViewSet(viewsets.ModelViewSet):
    """フード注文のAPI ViewSet"""
    
    queryset = FoodOrder.objects.all()
    serializer_class = FoodOrderSerializer
    
    def get_queryset(self):
        """クエリセットのフィルタリング"""
        queryset = FoodOrder.objects.all()
        
        # パラメータによるフィルタリング
        menu = self.request.query_params.get('menu')
        is_completed = self.request.query_params.get('is_completed')
        group_id = self.request.query_params.get('group_id')
        
        if menu:
            queryset = queryset.filter(menu=menu)
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == 'true')
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """注文完了処理"""
        order = self.get_object()
        order.is_completed = True
        order.completed_at = timezone.now()
        order.save()
        
        return Response({
            'message': '注文が完了しました。',
            'order_id': order.id,
            'completed_at': order.completed_at
        })
    
    @action(detail=False, methods=['get'])
    def active_orders(self, request):
        """未完了注文の取得"""
        active_orders = self.get_queryset().filter(is_completed=False)
        serializer = self.get_serializer(active_orders, many=True)
        return Response({
            'count': active_orders.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """注文統計の取得"""
        today = timezone.now().date()
        queryset = self.get_queryset()
        
        stats = {
            'total_orders_today': queryset.filter(timestamp__date=today).count(),
            'completed_orders_today': queryset.filter(
                timestamp__date=today, 
                is_completed=True
            ).count(),
            'pending_orders': queryset.filter(is_completed=False).count(),
            'popular_menu': self._get_popular_menu(queryset.filter(timestamp__date=today))
        }
        
        return Response(stats)
    
    def _get_popular_menu(self, queryset):
        """人気メニューの取得"""
        from django.db.models import Count
        popular = queryset.values('menu').annotate(
            count=Count('menu')
        ).order_by('-count').first()
        
        return popular if popular else {'menu': 'なし', 'count': 0}


class IceOrderViewSet(viewsets.ModelViewSet):
    """アイスクリーム注文のAPI ViewSet"""
    
    queryset = IceOrder.objects.all()
    serializer_class = IceOrderSerializer
    
    def get_queryset(self):
        """クエリセットのフィルタリング"""
        queryset = IceOrder.objects.all()
        
        size = self.request.query_params.get('size')
        status = self.request.query_params.get('status')
        is_completed = self.request.query_params.get('is_completed')
        
        if size:
            queryset = queryset.filter(size=size)
        if status:
            queryset = queryset.filter(status=status)
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == 'true')
        
        return queryset.order_by('-timestamp')
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """注文完了処理"""
        order = self.get_object()
        order.is_completed = True
        order.completed_at = timezone.now()
        order.save()
        
        return Response({
            'message': 'アイス注文が完了しました。',
            'order_id': order.id,
            'completed_at': order.completed_at
        })
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """注文状態の更新"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['ok', 'stop', 'hold']:
            return Response(
                {'error': '無効な状態です。'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        return Response({
            'message': f'状態を{new_status}に変更しました。',
            'order_id': order.id,
            'status': order.status
        })


class ShavedIceOrderViewSet(viewsets.ModelViewSet):
    """かき氷注文のAPI ViewSet"""
    
    queryset = ShavedIceOrder.objects.all()
    serializer_class = ShavedIceOrderSerializer
    
    def get_queryset(self):
        """クエリセットのフィルタリング"""
        queryset = ShavedIceOrder.objects.all()
        
        flavor = self.request.query_params.get('flavor')
        status = self.request.query_params.get('status')
        is_completed = self.request.query_params.get('is_completed')
        
        if flavor:
            queryset = queryset.filter(flavor=flavor)
        if status:
            queryset = queryset.filter(status=status)
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == 'true')
        
        return queryset.order_by('-timestamp')
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """注文完了処理"""
        order = self.get_object()
        order.is_completed = True
        order.completed_at = timezone.now()
        order.save()
        
        return Response({
            'message': 'かき氷注文が完了しました。',
            'order_id': order.id,
            'completed_at': order.completed_at
        })


# ==================== ヘルスチェック ====================

from rest_framework.decorators import api_view
from django.db import connection
from django.http import JsonResponse

@api_view(['GET'])
def health_check(request):
    """システムヘルスチェック"""
    try:
        # データベース接続確認
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # 基本統計の取得
        food_count = FoodOrder.objects.filter(is_completed=False).count()
        ice_count = IceOrder.objects.filter(is_completed=False).count()
        shavedice_count = ShavedIceOrder.objects.filter(is_completed=False).count()
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now(),
            'pending_orders': {
                'food': food_count,
                'ice': ice_count,
                'shavedice': shavedice_count,
                'total': food_count + ice_count + shavedice_count
            },
            'database': 'connected'
        })
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'timestamp': timezone.now(),
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)