import os
import sys
import json
import socket
import time


PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dev_pids.json")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("提示: 安装 psutil 可获得更好的进程管理体验")
    print("      pip install psutil\n")


def check_port(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        result = s.connect_ex(("127.0.0.1", port))
        return result == 0


def load_pids():
    """从文件加载 PID"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def remove_pid_file():
    """删除 PID 文件"""
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except:
            pass


def kill_process_tree(pid, name=""):
    """终止进程及其所有子进程"""
    if not HAS_PSUTIL:
        return kill_process_fallback(pid, name)
    
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # 先终止子进程
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # 终止父进程
        try:
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
        
        gone, alive = psutil.wait_procs([parent] + children, timeout=3)
        
        # 强制杀死未响应的进程
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
        
        print(f"  ✓ 已停止 {name} (PID: {pid})")
        return True
        
    except psutil.NoSuchProcess:
        print(f"  - {name} (PID: {pid}) 已不存在")
        return True
    except psutil.AccessDenied:
        print(f"  ✗ {name} (PID: {pid}) 权限不足")
        return False
    except Exception as e:
        print(f"  ✗ {name} (PID: {pid}) 停止失败: {e}")
        return False


def kill_process_fallback(pid, name=""):
    """不使用 psutil 的备用方案"""
    import subprocess
    import platform
    
    system = platform.system()
    
    try:
        if system == "Windows":
            # Windows: 使用 taskkill 强制终止进程树
            result = subprocess.run(
                f"taskkill /F /T /PID {pid}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"  ✓ 已停止 {name} (PID: {pid})")
                return True
            elif "not found" in result.stderr.lower() or result.returncode == 128:
                print(f"  - {name} (PID: {pid}) 已不存在")
                return True
            else:
                print(f"  ✗ {name} (PID: {pid}) 停止失败")
                return False
        else:
            # Unix: 使用 kill
            os.kill(pid, 15)  # SIGTERM
            time.sleep(1)
            try:
                os.kill(pid, 0)  # 检查进程是否存在
                os.kill(pid, 9)  # SIGKILL
            except ProcessLookupError:
                pass
            print(f"  ✓ 已停止 {name} (PID: {pid})")
            return True
            
    except ProcessLookupError:
        print(f"  - {name} (PID: {pid}) 已不存在")
        return True
    except PermissionError:
        print(f"  ✗ {name} (PID: {pid}) 权限不足")
        return False
    except Exception as e:
        print(f"  ✗ {name} (PID: {pid}) 停止失败: {e}")
        return False


def find_and_kill_by_pattern(patterns):
    """通过命令行模式查找并终止进程"""
    if not HAS_PSUTIL:
        print("  ⚠ 需要 psutil 来按模式查找进程")
        return
    
    killed = set()
    
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"] or [])
            for name, pattern in patterns.items():
                if pattern in cmdline and proc.pid not in killed:
                    kill_process_tree(proc.pid, name)
                    killed.add(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def stop_services():
    """停止所有服务"""
    print("=" * 50)
    print("停止视频平台开发环境")
    print("=" * 50 + "\n")
    
    # 1. 先尝试通过 PID 文件停止
    pids = load_pids()
    
    if pids:
        print("通过 PID 文件停止服务...\n")
        
        # 按顺序停止：前端 -> Django -> Celery Beat -> Celery Worker（不停止 Redis）
        order = ["frontend", "django", "celery_beat", "celery"]
        
        for service in order:
            if service in pids:
                pid = pids[service]
                if pid is None:
                    print(f"  - {service.capitalize()} 是系统服务，跳过")
                else:
                    kill_process_tree(pid, service.capitalize())
        
        # 检查 Redis 是否是脚本启动的
        if pids.get("redis") is not None:
            kill_process_tree(pids["redis"], "Redis")
        else:
            print("  - Redis 是系统服务，保持运行")
        
        remove_pid_file()
        print()
    
    # 2. 额外检查：通过命令行模式查找残留进程
    if HAS_PSUTIL:
        print("检查残留进程...\n")
        
        patterns = {
            "Celery Beat": "celery -A video beat",
            "Celery Worker": "celery -A video worker",
            "Django": "uvicorn video.asgi",
            "Frontend": "vite",
        }        
        find_and_kill_by_pattern(patterns)
        print()
    
    print("验证端口状态...\n")
    ports = {"Django": 8000, "Frontend": 5173}
    all_clear = True
    
    for name, port in ports.items():
        if check_port(port):
            print(f"  ⚠ 端口 {port} ({name}) 仍被占用")
            all_clear = False
        else:
            print(f"  ✓ 端口 {port} ({name}) 已释放")
    
    if check_port(6379):
        print("  ℹ 端口 6379 (Redis) 仍在运行（系统服务）")
    else:
        print("  ✓ 端口 6379 (Redis) 已停止")
    
    print("\n" + "=" * 50)
    if all_clear:
        print("所有服务已停止！")
    else:
        print("部分服务可能未完全停止，请手动检查")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    try:
        stop_services()
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)