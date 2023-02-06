from tortoise import fields, Model
import datetime


class ConfigModel(Model):
    class Meta:
        table = "config"

    id = fields.IntField(pk=True)
    key = fields.CharField(max_length=255, description="键")
    value = fields.TextField(description="值")


class UserModel(Model):
    id = fields.IntField(pk=True)
    mobile = fields.CharField(max_length=255, description="手机号码")
    code = fields.IntField(default=0, description="验证码")
    result = fields.CharField(max_length=255, default="wait", description="结果")
    created_at = fields.CharField(max_length=255, description="创建时间",
                                  default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    class Meta:
        table = "user"

    @classmethod
    async def paginate(cls, per_page, page):
        # 获取总的数据量
        query_count = await super().all().count()
        # 判断如果总数量等于 0
        if query_count == 0:
            return []
        # 根据每页的获取数量来获得总页数
        if query_count % per_page == 0:
            pages = query_count // per_page
        else:
            pages = query_count // per_page + 1
        # 如果当前页数大于总页数 返回空列表
        if page > pages:
            return []
        # 返回数据
        offset_num = (page - 1) * per_page
        result = await super().filter() \
            .offset(offset_num) \
            .limit(per_page) \
            .order_by("-id") \
            .values("id", "mobile", "result", "code", "created_at")
        return {"total": query_count, "pages": pages, "page": page, "limit": per_page, "item": result}

    @classmethod
    async def mobile_paginate(cls, per_page, page, mobile):
        # 获取总的数据量
        query_count = await super().filter(mobile__icontains=mobile).count()
        # 判断如果总数量等于 0
        if query_count == 0:
            return []
        # 根据每页的获取数量来获得总页数
        if query_count % per_page == 0:
            pages = query_count // per_page
        else:
            pages = query_count // per_page + 1
        # 如果当前页数大于总页数 返回空列表
        if page > pages:
            return []
        # 返回数据
        offset_num = (page - 1) * per_page
        result = await super().filter(mobile__contains=mobile) \
            .offset(offset_num) \
            .limit(per_page) \
            .order_by("-id") \
            .values("id", "mobile", "result", "code", "created_at")
        return {"total": query_count, "pages": pages, "page": page, "limit": per_page, "item": result}
