import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# --- 配置区 ---
# 定义所有需要处理的目录对（源目录，输出目录）
DIRECTORIES = [
    ("./assets/raw_models/asia", "./assets/compressed/asia"),
    ("./assets/raw_models/africa", "./assets/compressed/africa"),
    ("./assets/raw_models/europe", "./assets/compressed/europe"),
    ("./assets/raw_models/north_america", "./assets/compressed/north_america"),
    ("./assets/raw_models/south_america", "./assets/compressed/south_america"),
    ("./assets/raw_models/australia", "./assets/compressed/australia"),
]

MAX_WORKERS = 4  # 最大并发线程数，可根据机器性能调整


def ultra_compress_model(input_path, output_path, verbose=True):
    """
    压缩单个模型文件

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        verbose: 是否打印详细信息

    Returns:
        tuple: (success, input_size_mb, output_size_mb, compression_ratio)
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 核心指令对应关系：
    # --simplify 0.7  => 保留 30% 的面数（减掉 70%）
    # --texture-compress webp => 将贴图转为 WebP 格式
    # --texture-size 1024 => 强制贴图最大分辨率为 1024px
    # --compress draco => 几何坐标压缩
    cmd = [
        "gltf-transform", "optimize",
        input_path,
        output_path,
        "--simplify", "0.7",
        "--texture-compress", "webp",
        "--texture-size", "1024",
        "--compress", "draco"
    ]

    if verbose:
        cmd.append("--verbose")

    # 关键：通过环境变量给 Node.js 注入 4GB 内存限制，防止大文件崩溃
    env = os.environ.copy()
    env["NODE_OPTIONS"] = "--max-old-space-size=4096"

    try:
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            old_size = os.path.getsize(input_path) / (1024 * 1024)
            new_size = os.path.getsize(output_path) / (1024 * 1024)
            compression_ratio = (1 - new_size / old_size) * 100 if old_size > 0 else 0

            return True, old_size, new_size, compression_ratio
        else:
            if verbose:
                print(f"❌ 压缩失败: {os.path.basename(input_path)}")
                print(f"错误日志:\n{result.stderr}")
            return False, 0, 0, 0

    except Exception as e:
        if verbose:
            print(f"🚨 系统调用错误: {str(e)}")
        return False, 0, 0, 0


def process_directory(input_dir, output_dir, verbose=True):
    """
    处理单个目录下的所有模型

    Args:
        input_dir: 源目录路径
        output_dir: 输出目录路径
        verbose: 是否打印详细信息

    Returns:
        dict: 处理结果统计
    """
    # 获取目录下所有 glb 文件
    input_path = Path(input_dir)
    if not input_path.exists():
        if verbose:
            print(f"⚠️  目录不存在，跳过: {input_dir}")
        return {"total": 0, "success": 0, "failed": 0, "files": []}

    files = list(input_path.glob("*.glb"))

    if not files:
        if verbose:
            print(f"⚠️  未在 {input_dir} 找到模型文件，跳过。")
        return {"total": 0, "success": 0, "failed": 0, "files": []}

    if verbose:
        print(f"\n📁 开始处理目录: {input_dir}")
        print(f"   找到 {len(files)} 个模型文件")

    results = []
    success_count = 0

    for glb_file in files:
        # 生成输出路径
        output_path = Path(output_dir) / f"{glb_file.stem}_ultra{glb_file.suffix}"

        if verbose:
            print(f"\n📦 正在进行深度压缩: {glb_file.name}...")

        success, old_size, new_size, ratio = ultra_compress_model(
            str(glb_file), str(output_path), verbose
        )

        if success:
            success_count += 1
            if verbose:
                print(f"✅ 压缩成功!")
                print(f"📊 体积变化: {old_size:.2f}MB -> {new_size:.2f}MB")
                print(f"📉 压缩率: {ratio:.1f}%")
            results.append({
                "file": glb_file.name,
                "success": True,
                "old_size": old_size,
                "new_size": new_size,
                "ratio": ratio
            })
        else:
            results.append({
                "file": glb_file.name,
                "success": False,
                "old_size": 0,
                "new_size": 0,
                "ratio": 0
            })

    return {
        "total": len(files),
        "success": success_count,
        "failed": len(files) - success_count,
        "files": results
    }


def process_all_files_parallel(max_workers=MAX_WORKERS):
    """
    直接针对所有文件进行扁平化并发处理，不分目录级别
    """
    all_tasks = []

    # 1. 收集所有待处理的文件任务
    for input_dir, output_dir in DIRECTORIES:
        input_path = Path(input_dir)
        if not input_path.exists(): continue

        for glb_file in input_path.glob("*.glb"):
            output_path = Path(output_dir) / f"{glb_file.name}"  # 保持原名或加前缀
            all_tasks.append((glb_file, output_path))

    print(f"🚀 准备并发处理 {len(all_tasks)} 个文件，最大并发数: {max_workers}")

    # 2. 使用 ProcessPoolExecutor (进程池) 替代线程池
    # 对于 CPU 密集型工具，ProcessPool 在多核 Mac 上通常更稳定
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 将单个文件的压缩函数提交到进程池
        future_to_file = {
            executor.submit(ultra_compress_model, str(task[0]), str(task[1]), False): task[0].name
            for task in all_tasks
        }

        for future in as_completed(future_to_file):
            filename = future_to_file[future]
            success, _, _, _ = future.result()
            print(f"{'✅' if success else '❌'} {filename} 处理完毕")


if __name__ == "__main__":
    # 可以选择使用并行或串行模式
    # process_all_directories(parallel=False)  # 串行处理目录
    process_all_files_parallel(max_workers=8)  # 并行处理目录