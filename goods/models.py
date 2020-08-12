from django.db import models
from db.base_model import BaseModel
from tinymce.models import HTMLField


# Create your models here.

class GoodsType(BaseModel):
    """商品类型模型类"""
    name = models.CharField('种类名称', max_length=20)
    logo = models.CharField('标识', max_length=20)
    image = models.ImageField('商品类型图片', upload_to='type')

    class Meta:
        db_table = 'df_goods_type'
        verbose_name = '商品种类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '种类名称: %s' % self.name


class GoodsSKU(BaseModel):
    """商品SKU模型类"""
    status_choices = (
        (0, '下线'),
        (1, '上线')
    )
    type = models.ForeignKey('GoodsType', verbose_name='商品种类', on_delete=models.CASCADE)
    goods = models.ForeignKey('Goods', verbose_name='商品SPU', on_delete=models.CASCADE)
    name = models.CharField('商品名称', max_length=20)
    desc = models.CharField('商品简介', max_length=256)
    price = models.DecimalField('商品价格', max_digits=10, decimal_places=2)
    unite = models.CharField('商品单位', max_length=20)
    stock = models.IntegerField('商品库存', default=1)
    sales = models.IntegerField('商品销量', default=0)
    image = models.ImageField('商品图片', upload_to='goods')
    status = models.SmallIntegerField('商品状态', default=1, choices=status_choices)

    class Meta:
        db_table = 'df_goods_sku'
        verbose_name = '商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '商品名称: %s, 商品单位: %s' % (self.name, self.unite)


class Goods(BaseModel):
    """商品SPU模型类"""
    name = models.CharField('商品SPU名称', max_length=20)
    # 富文本类型：带有格式的文本
    detail = HTMLField('商品详情', blank=True)

    class Meta:
        db_table = 'df_goods'
        verbose_name = '商品SPU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '商品SPU名称: %s' % self.name


class GoodsImage(BaseModel):
    """商品图片模型类"""
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)
    image = models.ImageField('图片路径', upload_to='goods')

    class Meta:
        db_table = 'df_goods_image'
        verbose_name = '商品图片'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '商品: %s' % self.sku


class IndexGoodsBanner(BaseModel):
    """首页轮播商品展示模型类"""
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品', on_delete=models.CASCADE)
    image = models.ImageField('商品图片', upload_to='banner')
    index = models.SmallIntegerField('展示顺序', default=0)

    class Meta:
        db_table = 'df_goods_banner'
        verbose_name = '首页轮播商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '商品: %s' % self.sku


class IndexTypeGoodsBanner(BaseModel):
    """首页分类商品展示模型类"""
    DISPLAY_TYPE_CHOICES = (
        (0, '标题'),
        (1, '图片')
    )

    type = models.ForeignKey('GoodsType', verbose_name='商品类型', on_delete=models.CASCADE)
    sku = models.ForeignKey('GoodsSKU', verbose_name='商品SKU', on_delete=models.CASCADE)
    display_type = models.SmallIntegerField('展示类型', choices=DISPLAY_TYPE_CHOICES, default=1)
    index = models.SmallIntegerField('展示顺序', default=0)

    class Meta:
        db_table = 'df_index_type_goods'
        verbose_name = '首页分类展示商品'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s , %s' % (self.type, self.sku)


class IndexPromotionBanner(BaseModel):
    """首页促销活动模型类"""
    name = models.CharField('活动名称', max_length=20)
    url = models.CharField('活动链接', max_length=256)
    image = models.ImageField('活动图片', upload_to='banner')
    index = models.SmallIntegerField('展示顺序', default=0)

    class Meta:
        db_table = 'df_index_promotion'
        verbose_name = '主页促销活动'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '活动名称: %s' % self.name
