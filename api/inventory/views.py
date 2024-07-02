from django.db.models import F, Value, Sum
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .exception import BusinessException
from .models import Product, Purchase, Sales
from .serializers import InventorySerializer, ProductSerializer, PurchaseSerializer, SalesSerializer

class ProductView(APIView):
    # 共通利用する商品取得関数
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            raise NotFound

    def get(self, request, id=None, format=None):
        # 商品の一覧もしくは一意の商品を取得する
        if id is None:
            queryset = Product.objects.all()
            serializer = ProductSerializer(queryset, many=True)
        else:
            product = self.get_object(id)
            serializer = ProductSerializer(product)
        return Response(serializer.data, status.HTTP_200_OK)

    def post(self, request, format=None):
        """
        商品を登録する
        """
        serializer = ProductSerializer(data=request.data)
        # validationを通らなかった場合、例外を投げる
        serializer.is_valid(raise_exception=True)
        # 検証したデータを永続化する
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)

    def put(self, request, id, format=None):
        product = self.get_object(id)
        serializer = ProductSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_200_OK)

    def delete(self, request, id, format=None):
        product = self.get_object(id)
        product.delete()
        return Response(status = status.HTTP_200_OK)


class PurchaseView(APIView):
    def post(self, request, format=None):
        """
        仕入情報を登録する
        """
        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)


class SalesView(APIView):
    def post(self, request, format=None):
        """
        売上情報を登録する
        """
        serializer = SalesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 数量チェック
        # 登録済の仕入数の合計
        purchase = Purchase.objects.filter(product_id=request.data['product']).aggregate(quantity_sum=Coalesce(Sum('quantity'), 0))
        # 登録済の売上数の合計
        sales = Sales.objects.filter(product_id=request.data['product']).aggregate(quantity_sum=Coalesce(Sum('quantity'), 0))
        # 在庫の合計を超えていないかチェック
        if purchase['quantity_sum'] < (sales['quantity_sam'] + int(request.data['quantity'])):
            raise BusinessException('在庫数量を超過することはできません')

        serializer.save()
        return Response(serializer.data, status.HTTP_201_CREATED)


# ModelViewSetでの実装
class ProductModelViewSet(ModelViewSet):
    """
    商品操作に関する関数（ModelViewSet）
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class InventoryView(APIView):
    # 仕入・売上情報を取得する
    def get(self, request, id=None, format=None):
        if id is None:
            # 件数が多くなるため商品IDは必ず指定する
            return Response(serializer.data, status.HTTP_400_BAD_REQUEST)
        else:
            # UNIONするために、それぞれフィールド名を再定義している
            purchase = Purchase.objects.filter(product_id=id).prefetch_related('product').values("id", "quantity", type=Value('1'), data=F('purchase_date'), unit=F('product__price'))

            sales = Sales.objects.filter(product_id=id).prefetch_related('product').values("id", "quantity", type=Value('2'), date=F('sales_date'), unit=F('product__price'))

            queryset = purchase.union(sales).order_by(F("date"))
            serializer = InventorySerializer(queryset, many=True)

        return Response(serializer.data, status.HTTP_200_OK)
