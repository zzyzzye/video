from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs
import logging

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user(token_key):
    """
    从 JWT token 获取用户
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        # 验证 token
        access_token = AccessToken(token_key)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        return user
    except (InvalidToken, TokenError) as e:
        logger.warning(f"JWT Token 无效: {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        logger.warning(f"用户不存在: user_id={access_token.get('user_id')}")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"获取用户失败: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """
    WebSocket JWT 认证中间件
    从 query string 中获取 token 进行认证
    
    连接示例: ws://localhost:8000/ws/notifications/?token=xxx
    """
    
    async def __call__(self, scope, receive, send):
        # 从 query string 获取 token
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token_list = query_params.get('token', [])
        
        if token_list:
            token = token_list[0]
            scope['user'] = await get_user(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
