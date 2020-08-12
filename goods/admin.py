from django.contrib import admin
from django.core.cache import cache

from . import models
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """新增或更新表中的数据时调用"""
        super().save_model(request, obj, form, change)

        # 发出任务，让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页的缓存存储
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除表中的数据时调用"""
        super().delete_model(request, obj)
        # 发出任务，让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页的缓存存储
        cache.delete('index_page_data')


# 编写模型管理器类
class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class GoodsSKUAdmin(BaseModelAdmin):
    pass


class GoodsImageAdmin(BaseModelAdmin):
    pass


class GoodsAdmin(BaseModelAdmin):
    pass


admin.site.register(models.GoodsType, GoodsTypeAdmin)
admin.site.register(models.IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(models.IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(models.IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(models.GoodsSKU, GoodsSKUAdmin)
admin.site.register(models.GoodsImage, GoodsImageAdmin)
admin.site.register(models.Goods, GoodsAdmin)
