from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


from db.base_model import BaseModel


class User(AbstractUser, BaseModel):
    """用户模型类"""
    # active_choices = (
    #     (0, '没有激活'),
    #     (1, '激活'),
    # )
    # staff_choices = (
    #     (0, '没有权限'),
    #     (1, '有权限'),
    # )
    # username = models.CharField('用户名称', max_length=20)
    # password = models.CharField('密码',max_length=20)
    # email = models.EmailField('邮箱', max_length=30)
    # is_active = models.SmallIntegerField('激活标识', default=0, choices=active_choices)
    # is_staff = models.SmallIntegerField('权限', default=0,choices=staff_choices)

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name


class AddressManager(models.Manager):
    """地址模型管理器类"""
    # 1.改变原有查询结果集：all()
    # 2.封装方法：用于操作模型类对应的数据表(增删改查)
    def get_default_address(self, user):
        """获取用户的默认收获地址"""
        # self.model:获取self对象所在的模型类 -- self.model在这里相当于models.Address
        try:
            # self本身就是AddressManager的一个对象，可以直接调用父类models.Manager方法
            address = self.get(user=user, is_default=True)
        except self.model.DoesNotExist:
            # 不存在默认收获地址
            address = None
        return address


class Address(BaseModel):
    """地址模型类"""
    receiver = models.CharField('收件人', max_length=20)
    addr = models.CharField('收件地址', max_length=256)
    # null=True 允许为空
    zip_code = models.CharField('邮编', max_length=6, null=True)
    phone = models.CharField('联系方式', max_length=11)
    is_default = models.BooleanField('是否默认', default=False)
    user = models.ForeignKey('User', verbose_name='所属账户', on_delete=models.CASCADE)

    # 自定义一个模型管理器对象
    objects = AddressManager()

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name
