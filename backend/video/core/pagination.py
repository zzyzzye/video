from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页，每页10条"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(PageNumberPagination):
    """大分页，每页50条"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200 