from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from rest_framework import status
from rest_framework.viewsets import ModelViewSet

class ProductView(APIView):
    """
    商品操作に関する関数
    """
    def get(self, request, format=None):
        """
        商品一覧の取得
        """
        queryset = Product.objects.all()
        serializer = ProductSerializer(queryset, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

class ProductModelViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
