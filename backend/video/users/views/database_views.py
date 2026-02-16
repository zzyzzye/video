from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import connection
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
import os
import subprocess
import json

from core.permissions import IsSuperAdmin


class DatabaseManagementViewSet(viewsets.ViewSet):
    """数据库管理视图集"""
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def info(self, request):
        """获取数据库信息"""
        db_config = settings.DATABASES['default']
        
        with connection.cursor() as cursor:
            # 获取数据库版本
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            
            # 获取数据库大小
            db_name = db_config['NAME']
            cursor.execute(f"""
                SELECT 
                    table_schema AS 'database',
                    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'size_mb'
                FROM information_schema.tables 
                WHERE table_schema = '{db_name}'
                GROUP BY table_schema
            """)
            size_result = cursor.fetchone()
            db_size = size_result[1] if size_result else 0
            
            # 获取表信息
            cursor.execute(f"""
                SELECT 
                    table_name,
                    table_rows,
                    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                    ROUND(data_length / 1024 / 1024, 2) AS data_mb,
                    ROUND(index_length / 1024 / 1024, 2) AS index_mb,
                    engine,
                    table_collation,
                    avg_row_length,
                    auto_increment,
                    create_time,
                    update_time,
                    table_comment
                FROM information_schema.tables
                WHERE table_schema = '{db_name}'
                ORDER BY (data_length + index_length) DESC
            """)
            
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    'name': row[0],
                    'rows': row[1] or 0,
                    'size_mb': float(row[2]) if row[2] else 0,
                    'data_mb': float(row[3]) if row[3] else 0,
                    'index_mb': float(row[4]) if row[4] else 0,
                    'engine': row[5],
                    'collation': row[6],
                    'avg_row_length': row[7] or 0,
                    'auto_increment': row[8],
                    'create_time': row[9].isoformat() if row[9] else None,
                    'update_time': row[10].isoformat() if row[10] else None,
                    'comment': row[11] or ''
                })
        
        return Response({
            'engine': db_config['ENGINE'].split('.')[-1],
            'name': db_name,
            'host': db_config['HOST'],
            'port': db_config['PORT'],
            'version': version,
            'size_mb': float(db_size),
            'table_count': len(tables),
            'tables': tables
        })
    
    @action(detail=False, methods=['post'])
    def backup(self, request):
        """备份数据库"""
        db_config = settings.DATABASES['default']
        
        # 创建备份目录
        backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.sql')
        
        try:
            # 使用 mysqldump 备份
            cmd = [
                'mysqldump',
                '-h', db_config['HOST'],
                '-P', str(db_config['PORT']),
                '-u', db_config['USER'],
                f'-p{db_config["PASSWORD"]}',
                db_config['NAME'],
                '--result-file', backup_file
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # 获取文件大小
            file_size = os.path.getsize(backup_file) / (1024 * 1024)  # MB
            
            return Response({
                'message': '数据库备份成功',
                'file': backup_file,
                'size_mb': round(file_size, 2),
                'created_at': timezone.now().isoformat()
            })
        except subprocess.CalledProcessError as e:
            return Response({
                'error': '备份失败',
                'detail': e.stderr
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'error': '备份失败',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def backups(self, request):
        """获取备份列表"""
        backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
        
        if not os.path.exists(backup_dir):
            return Response({'backups': []})
        
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.sql'):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_at': timezone.datetime.fromtimestamp(stat.st_ctime).isoformat()
                })
        
        # 按创建时间倒序排序
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return Response({'backups': backups})
    
    @action(detail=False, methods=['post'])
    def restore(self, request):
        """恢复数据库"""
        filename = request.data.get('filename')
        if not filename:
            return Response({
                'error': '请指定备份文件'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        backup_dir = os.path.join(settings.BASE_DIR, 'backups', 'database')
        backup_file = os.path.join(backup_dir, filename)
        
        if not os.path.exists(backup_file):
            return Response({
                'error': '备份文件不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        db_config = settings.DATABASES['default']
        
        try:
            # 使用 mysql 命令恢复
            cmd = [
                'mysql',
                '-h', db_config['HOST'],
                '-P', str(db_config['PORT']),
                '-u', db_config['USER'],
                f'-p{db_config["PASSWORD"]}',
                db_config['NAME']
            ]
            
            with open(backup_file, 'r', encoding='utf-8') as f:
                subprocess.run(cmd, stdin=f, check=True, capture_output=True, text=True)
            
            return Response({
                'message': '数据库恢复成功',
                'file': filename
            })
        except subprocess.CalledProcessError as e:
            return Response({
                'error': '恢复失败',
                'detail': e.stderr
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'error': '恢复失败',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def optimize(self, request):
        """优化数据库"""
        table_name = request.data.get('table')
        
        with connection.cursor() as cursor:
            if table_name:
                # 优化指定表
                cursor.execute(f"OPTIMIZE TABLE {table_name}")
                result = cursor.fetchall()
                return Response({
                    'message': f'表 {table_name} 优化完成',
                    'result': result
                })
            else:
                # 优化所有表
                db_name = settings.DATABASES['default']['NAME']
                cursor.execute(f"""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = '{db_name}'
                """)
                
                tables = [row[0] for row in cursor.fetchall()]
                results = {}
                
                for table in tables:
                    try:
                        cursor.execute(f"OPTIMIZE TABLE {table}")
                        results[table] = 'success'
                    except Exception as e:
                        results[table] = str(e)
                
                return Response({
                    'message': '数据库优化完成',
                    'results': results
                })
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """分析表"""
        table_name = request.data.get('table')
        
        if not table_name:
            return Response({
                'error': '请指定表名'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute(f"ANALYZE TABLE {table_name}")
            result = cursor.fetchall()
            
            return Response({
                'message': f'表 {table_name} 分析完成',
                'result': result
            })
    
    @action(detail=False, methods=['post'])
    def repair(self, request):
        """修复表"""
        table_name = request.data.get('table')
        
        if not table_name:
            return Response({
                'error': '请指定表名'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute(f"REPAIR TABLE {table_name}")
            result = cursor.fetchall()
            
            return Response({
                'message': f'表 {table_name} 修复完成',
                'result': result
            })
    
    @action(detail=False, methods=['get'])
    def connections(self, request):
        """获取数据库连接信息"""
        with connection.cursor() as cursor:
            cursor.execute("SHOW PROCESSLIST")
            columns = [col[0] for col in cursor.description]
            connections = []
            
            for row in cursor.fetchall():
                conn = dict(zip(columns, row))
                connections.append(conn)
        
        return Response({
            'connections': connections,
            'count': len(connections)
        })
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """获取数据库状态"""
        with connection.cursor() as cursor:
            cursor.execute("SHOW STATUS")
            status_dict = {}
            
            for row in cursor.fetchall():
                status_dict[row[0]] = row[1]
        
        # 提取关键指标
        key_metrics = {
            'uptime': status_dict.get('Uptime', 0),
            'threads_connected': status_dict.get('Threads_connected', 0),
            'threads_running': status_dict.get('Threads_running', 0),
            'queries': status_dict.get('Queries', 0),
            'slow_queries': status_dict.get('Slow_queries', 0),
            'connections': status_dict.get('Connections', 0),
            'aborted_connects': status_dict.get('Aborted_connects', 0),
            'bytes_received': status_dict.get('Bytes_received', 0),
            'bytes_sent': status_dict.get('Bytes_sent', 0),
        }
        
        return Response({
            'status': key_metrics,
            'full_status': status_dict
        })
    
    @action(detail=False, methods=['get'], url_path='table-structure')
    def table_structure(self, request):
        """获取表结构"""
        table_name = request.query_params.get('table')
        
        if not table_name:
            return Response({
                'error': '请指定表名'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [col[0] for col in cursor.description]
            structure = []
            
            for row in cursor.fetchall():
                field_info = dict(zip(columns, row))
                structure.append(field_info)
        
        return Response({
            'structure': structure
        })
    
    @action(detail=False, methods=['get'], url_path='table-indexes')
    def table_indexes(self, request):
        """获取表索引"""
        table_name = request.query_params.get('table')
        
        if not table_name:
            return Response({
                'error': '请指定表名'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW INDEX FROM {table_name}")
            columns = [col[0] for col in cursor.description]
            indexes = []
            
            for row in cursor.fetchall():
                index_info = dict(zip(columns, row))
                indexes.append(index_info)
        
        return Response({
            'indexes': indexes
        })
    
    @action(detail=False, methods=['get'], url_path='table-data')
    def table_data(self, request):
        """获取表数据预览"""
        table_name = request.query_params.get('table')
        limit = int(request.query_params.get('limit', 100))
        
        if not table_name:
            return Response({
                'error': '请指定表名'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            # 获取列名
            cursor.execute(f"DESCRIBE {table_name}")
            columns = [row[0] for row in cursor.fetchall()]
            
            # 获取数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
            data = []
            
            for row in cursor.fetchall():
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # 处理特殊类型
                    if isinstance(value, (bytes, bytearray)):
                        row_dict[col] = '[BINARY]'
                    elif value is None:
                        row_dict[col] = None
                    else:
                        row_dict[col] = str(value)
                data.append(row_dict)
        
        return Response({
            'columns': columns,
            'data': data,
            'count': len(data)
        })
