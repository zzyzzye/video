import os
import sys
import time
import socket
import subprocess
import platform
import shutil
import json


PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dev_pids.json")


def check_dependency(name, command):
    """检查依赖是否已安装"""
    if shutil.which(command):
        return True
    print(f"✗ 未找到 {name}，请先安装 {command}")
    return False


def check_port(port, host="127.0.0.1"):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        result = s.connect_ex((host, port))
        return result == 0  # True = 被占用


def wait_for_port(port, timeout=30, check_interval=0.5):
    """等待端口可用（服务启动成功）"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_port(port, "127.0.0.1") or check_port(port, "0.0.0.0"):
            return True
        time.sleep(check_interval)
    return False


def print_header(text):
    print("\n" + "=" * 50)
    print(text)
    print("=" * 50 + "\n")


def save_pids(pids):
    """保存 PID 到文件"""
    with open(PID_FILE, "w", encoding="utf-8") as f:
        json.dump(pids, f, indent=2)


def start_process(name, command, cwd=None, shell=True, log_file=None):
    """启动进程并返回 PID"""
    system = platform.system()
    
    # 如果指定了日志文件，输出到文件；否则输出到 DEVNULL
    if log_file:
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file)
        stdout_handle = open(log_path, "w", encoding="utf-8")
        stderr_handle = subprocess.STDOUT
    else:
        stdout_handle = subprocess.DEVNULL
        stderr_handle = subprocess.DEVNULL
    
    # 设置启动参数
    kwargs = {
        "shell": shell,
        "cwd": cwd,
        "stdout": stdout_handle,
        "stderr": stderr_handle,
    }
    
    # Windows 特殊处理：创建新进程组，避免信号传递
    if system == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    
    try:
        proc = subprocess.Popen(command, **kwargs)
        print(f"  ✓ {name} 已启动 (PID: {proc.pid})")
        if log_file:
            print(f"    日志: {log_file}")
        return proc.pid
    except Exception as e:
        print(f"  ✗ {name} 启动失败: {e}")
        return None


def main():
    print_header("启动视频平台开发环境")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend", "video")
    frontend_dir = os.path.join(root_dir, "frontend", "video-ui")
    
    system = platform.system()
    print(f"操作系统: {system}")
    print(f"Python: {sys.version.split()[0]}\n")
    
    # 检查依赖
    print("检查依赖...")
    deps_ok = True
    deps_ok &= check_dependency("Redis", "redis-server")
    deps_ok &= check_dependency("Node.js", "npm")
    deps_ok &= check_dependency("Python", "python")
    
    if not deps_ok:
        print("\n请先安装缺失的依赖！")
        sys.exit(1)
    print("✓ 所有依赖已就绪\n")
    
    print("检查端口...")
    ports_to_check = {"Django": 8000, "Frontend": 5173, "Flower": 5555}
    port_conflict = False
    
    if check_port(6379):
        print("  ✓ 端口 6379 (Redis) 已在运行")
    else:
        print("  - 端口 6379 (Redis) 未运行，稍后启动")
    
    for name, port in ports_to_check.items():
        if check_port(port):
            print(f"  ✗ 端口 {port} ({name}) 已被占用")
            port_conflict = True
        else:
            print(f"  ✓ 端口 {port} ({name}) 可用")
    
    if port_conflict:
        print("\n请先释放被占用的端口，或运行 python stop_dev.py")
        sys.exit(1)
    print()
    
    pids = {}
    
    print("[1/4] 检查 Redis...")
    if check_port(6379):
        print("  ✓ Redis 已在运行（系统服务）")
        pids["redis"] = None  
    else:
        print("  Redis 未运行，尝试启动...")
        pid = start_process("Redis", "redis-server")
        if pid:
            pids["redis"] = pid
            time.sleep(1)
            if not check_port(6379):
                print("  ⚠ Redis 可能未正常启动，请检查")
    
    # 获取虚拟环境 Python 路径
    venv_python = os.path.join(root_dir, "backend", "venv", "Scripts", "python.exe")
    venv_celery = os.path.join(root_dir, "backend", "venv", "Scripts", "celery.exe")
    
    if not os.path.exists(venv_python):
        print(f"✗ 未找到虚拟环境 Python: {venv_python}")
        sys.exit(1)

    # 2. 启动 Celery Worker
    print("\n[2/5] 启动 Celery Worker...")
    # Windows 使用 solo 池，Linux/Mac 使用 prefork 池
    if system == "Windows":
        celery_cmd = f"{venv_celery} -A video worker -l info --pool=solo"
    else:
        celery_cmd = (
            f"{venv_celery} -A video worker -l info "
            "--pool=prefork "
            "--concurrency=2 "
            "--max-tasks-per-child=10 "
            "--max-memory-per-child=500000"
        )
    pid = start_process("Celery Worker", celery_cmd, cwd=backend_dir)
    if pid:
        pids["celery"] = pid
        print("  等待 Celery 启动...")
        time.sleep(3)
        # 检查进程是否还在运行
        try:
            if system == "Windows":
                result = subprocess.run(
                    f"tasklist /FI \"PID eq {pid}\" /NH",
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='gbk',  # Windows 使用 GBK 编码
                    errors='ignore'
                )
                if result.stdout and str(pid) not in result.stdout:
                    print(f"  ✗ Celery Worker 进程已退出")
                    pids["celery"] = None
                else:
                    print("  ✓ Celery Worker 运行正常")
            else:
                os.kill(pid, 0)  # 检查进程是否存在
                print("  ✓ Celery Worker 运行正常")
        except (subprocess.SubprocessError, OSError):
            print(f"  ✗ Celery Worker 进程已退出")
            pids["celery"] = None
    else:
        print("  ✗ Celery Worker 启动失败")
    
    # 3. 启动 Celery Beat（定时任务调度器）
    print("\n[3/6] 启动 Celery Beat...")
    beat_cmd = f"{venv_celery} -A video beat -l info"
    pid = start_process("Celery Beat", beat_cmd, cwd=backend_dir)
    if pid:
        pids["celery_beat"] = pid
        print("  等待 Celery Beat 启动...")
        time.sleep(2)
        # 检查进程是否还在运行
        try:
            if system == "Windows":
                result = subprocess.run(
                    f"tasklist /FI \"PID eq {pid}\" /NH",
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='gbk',
                    errors='ignore'
                )
                if result.stdout and str(pid) not in result.stdout:
                    print(f"  ✗ Celery Beat 进程已退出")
                    pids["celery_beat"] = None
                else:
                    print("  ✓ Celery Beat 运行正常")
            else:
                os.kill(pid, 0)
                print("  ✓ Celery Beat 运行正常")
        except (subprocess.SubprocessError, OSError):
            print(f"  ✗ Celery Beat 进程已退出")
            pids["celery_beat"] = None
    else:
        print("  ✗ Celery Beat 启动失败")
    
    # 4. 启动 Flower (Celery 监控)
    print("\n[4/6] 启动 Flower (Celery 监控)...")
    flower_cmd = f"{venv_celery} -A video flower --port=5555 --address=127.0.0.1"
    pid = start_process("Flower", flower_cmd, cwd=backend_dir)
    if pid:
        pids["flower"] = pid
        print("  等待 Flower 启动...")
        if wait_for_port(5555, timeout=10):
            print("  ✓ Flower 已就绪")
        else:
            print("  ⚠ Flower 启动超时")
    
    # 5. 启动 Django (Uvicorn)
    print("\n[5/6] 启动 Django (Uvicorn)...")
    django_cmd = f"{venv_python} -m uvicorn video.asgi:application --host 127.0.0.1 --port 8000 --ws websockets"
    pid = start_process("Django", django_cmd, cwd=backend_dir)
    if pid:
        pids["django"] = pid
        print("  等待 Django 启动...")
        if wait_for_port(8000, timeout=15):
            print("  ✓ Django 已就绪")
        else:
            print("  ⚠ Django 启动超时")
    
    # 6. 启动前端
    print("\n[6/6] 启动前端 (Vite)...")
    frontend_cmd = "npm run dev"
    pid = start_process("Frontend", frontend_cmd, cwd=frontend_dir)
    if pid:
        pids["frontend"] = pid
        time.sleep(2)  # 等待窗口出现
        print("  ✓ 前端已启动，浏览器将自动打开")
    
    save_pids(pids)
    
    print_header("所有服务已启动！")
    print("后端地址: http://localhost:8000")
    print("前端地址: http://localhost:5173")
    print("Flower 监控: http://localhost:5555")
    print(f"\nPID 已保存到: {PID_FILE}")
    print("停止服务: python stop_dev.py\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断，退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)