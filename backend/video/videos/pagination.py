"""
自定义分页类
"""
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    """
    标准分页类 - 适用于小数据量
    支持页码分页，用户可以跳转到任意页
    """
    page_size = 20  # 每页20条
    page_size_query_param = 'page_size'  # 允许客户端自定义每页数量
    max_page_size = 100  # 最大每页100条
    
    def get_paginated_response(self, data):
        """自定义分页响应格式"""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),  # 总数
            ('next', self.get_next_link()),  # 下一页链接
            ('previous', self.get_previous_link()),  # 上一页链接
            ('total_pages', self.page.paginator.num_pages),  # 总页数
            ('current_page', self.page.number),  # 当前页码
            ('results', data)  # 数据
        ]))


class LargeResultsSetPagination(CursorPagination):
    """
    游标分页类 - 适用于大数据量
    性能更好，但不支持跳页
    适用场景：
    - 观看历史（按时间倒序）
    - 评论列表（按时间倒序）
    - 视频流（无限滚动）
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'  # 默认按创建时间倒序
    cursor_query_param = 'cursor'
    
    def get_paginated_response(self, data):
        """自定义分页响应格式"""
        return Response(OrderedDict([
            ('next', self.get_next_link()),  # 下一页游标
            ('previous', self.get_previous_link()),  # 上一页游标
            ('results', data)  # 数据
        ]))


class VideoListPagination(StandardResultsSetPagination):
    """视频列表分页 - 使用标准分页"""
    page_size = 24  # 视频列表每页24个（4x6网格）


class CommentListPagination(LargeResultsSetPagination):
    """评论列表分页 - 使用游标分页"""
    page_size = 30  # 评论每页30条
    ordering = '-created_at'


class HistoryListPagination(LargeResultsSetPagination):
    """观看历史分页 - 使用游标分页"""
    page_size = 20
    ordering = '-view_date'  # 按观看时间倒序


class CollectionListPagination(StandardResultsSetPagination):
    """收藏列表分页 - 使用标准分页"""
    page_size = 20
