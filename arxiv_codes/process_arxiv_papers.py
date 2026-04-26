#!/usr/bin/env python3
"""
arXiv 论文 NotebookLM 处理脚本（独立 Notebook 版）

特性：
- 每篇论文独立 notebook，避免 infographic 互相覆盖
- 两阶段流水线：先批量提交生成任务，再统一轮询下载
- 通过图片文件存在性判断去重
- 720P JPG 图片压缩
"""

import json
import os
import re
import subprocess
import time
import traceback
import shutil
from datetime import datetime
from urllib.parse import urlparse


OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./arxiv-daily-output")
PAPERS_JSON = os.path.join(OUTPUT_DIR, "papers.json")
PROCESSED_JSON = os.path.join(OUTPUT_DIR, "papers_processed.json")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "arxiv-daily", "images")
NOTEBOOK_PREFIX = "arxiv_daily"

PAPERS_LIMIT = int(os.environ.get("DEBUG_LIMIT", 12))
SOURCE_READY_WAIT = int(os.environ.get("SOURCE_READY_WAIT", 10))
INFOGRAPHIC_READY_WAIT = int(os.environ.get("INFOGRAPHIC_READY_WAIT", 30))
DOWNLOAD_MAX_RETRIES = int(os.environ.get("DOWNLOAD_MAX_RETRIES", 5))
DOWNLOAD_RETRY_INTERVAL = int(os.environ.get("DOWNLOAD_RETRY_INTERVAL", 60))
ARTIFACT_STATUS_POLL_INTERVAL = int(os.environ.get("ARTIFACT_STATUS_POLL_INTERVAL", 30))
ARTIFACT_STATUS_TIMEOUT = int(os.environ.get("ARTIFACT_STATUS_TIMEOUT", 1800))

os.makedirs(IMAGES_DIR, exist_ok=True)


def resolve_nlm_command() -> str:
    """Resolve the nlm executable path across local and CI environments."""
    explicit = os.environ.get("NLM_COMMAND")
    if explicit:
        return explicit

    resolved = shutil.which("nlm")
    if resolved:
        return resolved

    appdata = os.environ.get("APPDATA")
    if appdata:
        candidate = os.path.join(appdata, "uv", "tools", "notebooklm-mcp-cli", "Scripts", "nlm.exe")
        if os.path.exists(candidate):
            return candidate

    home = os.path.expanduser("~")
    candidate = os.path.join(home, ".local", "bin", "nlm")
    if os.path.exists(candidate):
        return candidate

    raise FileNotFoundError(
        "Unable to find the nlm CLI. Set NLM_COMMAND or add nlm to PATH."
    )


NLM_COMMAND = resolve_nlm_command()
NLM_PROFILE = os.environ.get("NLM_PROFILE", "default")


def run_nlm(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the nlm CLI with captured output."""
    return subprocess.run(
        [NLM_COMMAND, *args],
        capture_output=True,
        text=True,
    )


def run_nlm_json(*args: str):
    """Run nlm and parse JSON output when possible."""
    result = run_nlm(*args)
    if result.returncode != 0:
        return None, result

    try:
        return json.loads(result.stdout), result
    except json.JSONDecodeError:
        return None, result


def extract_arxiv_id(abs_url):
    """从 arXiv URL 中提取论文 ID。"""
    match = re.search(r"/abs/(\d+\.\d+)", abs_url)
    if match:
        return match.group(1)

    parsed = urlparse(abs_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 2 and path_parts[0] == "abs":
        return path_parts[1]
    return None


def find_existing_notebook(notebook_name):
    """查找是否已存在同名 notebook。"""
    result = run_nlm("notebook", "list")
    if result.returncode == 0:
        try:
            notebooks = json.loads(result.stdout)
            for notebook in notebooks:
                if notebook.get("title") == notebook_name:
                    return notebook.get("id")
        except json.JSONDecodeError:
            pass
    return None


def create_notebook(notebook_name):
    """创建 notebook，如果已存在则复用。"""
    existing_id = find_existing_notebook(notebook_name)
    if existing_id:
        print(f"    复用已有 notebook: {notebook_name}")
        return existing_id

    result = run_nlm("notebook", "create", notebook_name)
    if result.returncode != 0:
        return None

    for line in result.stdout.strip().splitlines():
        if "ID:" in line:
            return line.split("ID:")[-1].strip()
    return None


def add_url_to_notebook(notebook_id, pdf_url):
    """向 notebook 添加论文 PDF URL。"""
    result = run_nlm("add", "url", notebook_id, pdf_url)
    return result.returncode == 0, result.stdout, result.stderr


def get_all_sources(notebook_id):
    """获取 notebook 下所有 sources。"""
    result = run_nlm("source", "list", notebook_id, "--json")
    if result.returncode != 0:
        return []

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return []


def find_source_id(sources, target_url):
    """根据 URL 查找 source ID。"""
    for source in sources:
        source_url = source.get("url", "")
        if source_url and (target_url in source_url or source_url in target_url):
            return source.get("id")
    return None


def is_transient_nlm_error(stderr_text: str) -> bool:
    """Return True for retryable network or backend errors."""
    text = (stderr_text or "").lower()
    retry_markers = [
        "ssl: unexpected_eof_while_reading",
        "connecterror",
        "connectionreseterror",
        "timed out",
        "timeout",
        "temporarily unavailable",
        "503",
        "bad gateway",
        "gateway timeout",
    ]
    return any(marker in text for marker in retry_markers)


def parse_artifact_id(stdout: str) -> str | None:
    """Extract an artifact id from nlm stdout."""
    match = re.search(r"Artifact ID:\s*([0-9a-fA-F-]+)", stdout or "")
    if match:
        return match.group(1)
    return None


def create_infographic(notebook_id, source_id):
    """发起 infographic 生成请求。"""
    for attempt in range(3):
        result = run_nlm(
            "infographic",
            "create",
            notebook_id,
            "--source-ids",
            source_id,
            "--orientation",
            "landscape",
            "--detail",
            "concise",
            "--language",
            "zh-CN",
            "-y",
        )
        if result.returncode == 0:
            return True, parse_artifact_id(result.stdout), None

        if attempt < 2 and is_transient_nlm_error(result.stderr):
            time.sleep(10 * (attempt + 1))
            continue

        return False, None, result.stderr

    return False, None, "infographic creation failed after retries"


def get_artifact_status(notebook_id, artifact_id):
    """Fetch the current artifact status from NotebookLM."""
    data, result = run_nlm_json("status", "artifacts", notebook_id, "--json", "-p", NLM_PROFILE)
    if result.returncode != 0:
        return None, result.stderr

    if not isinstance(data, list):
        return None, "Unexpected artifact status payload"

    for artifact in data:
        if artifact.get("id") == artifact_id:
            return artifact, None

    return None, "Artifact not found"


def wait_for_artifact_ready(notebook_id, artifact_id, timeout_seconds=None):
    """Wait until an infographic artifact reaches completed status."""
    timeout_seconds = timeout_seconds or ARTIFACT_STATUS_TIMEOUT
    deadline = time.time() + timeout_seconds
    last_error = None

    while time.time() < deadline:
        artifact, error = get_artifact_status(notebook_id, artifact_id)
        if artifact:
            status = (artifact.get("status") or "").lower()
            if status == "completed":
                return True, artifact, None
            if status in {"failed", "canceled", "cancelled"}:
                return False, artifact, f"Artifact ended with status: {status}"
            last_error = status or "unknown"
        else:
            last_error = error

        time.sleep(ARTIFACT_STATUS_POLL_INTERVAL)

    return False, None, f"Timed out waiting for infographic readiness: {last_error}"


def download_infographic_with_retry(notebook_id, output_path, max_retries=10, retry_interval=60):
    """
    下载 infographic，支持重试。
    每隔 retry_interval 秒尝试一次，最多重试 max_retries 次。
    """
    for attempt in range(max_retries):
        result = run_nlm("download", "infographic", notebook_id, "--output", output_path)
        if result.returncode == 0:
            return True, result.stdout, None

        stderr = result.stderr or ""
        lowered = stderr.lower()
        if "not ready" in lowered or "does not exist" in lowered or is_transient_nlm_error(stderr):
            if attempt < max_retries - 1:
                print(
                    f"    图片未就绪，等待 {retry_interval} 秒后重试..."
                    f" ({attempt + 1}/{max_retries})"
                )
                time.sleep(retry_interval)
                continue

        return False, result.stdout, result.stderr

    return False, "", f"超过最大重试次数({max_retries})"


def download_infographic_by_id(notebook_id, artifact_id, output_path):
    """Download an infographic artifact explicitly by ID."""
    for attempt in range(3):
        result = run_nlm(
            "download",
            "infographic",
            notebook_id,
            "--id",
            artifact_id,
            "--no-progress",
            "--output",
            output_path,
        )
        if result.returncode == 0:
            return True, result.stdout, None

        if attempt < 2 and is_transient_nlm_error(result.stderr):
            time.sleep(5 * (attempt + 1))
            continue

        return False, result.stdout, result.stderr

    return False, "", "download infographic failed after retries"


def delete_notebook(notebook_id):
    """删除 notebook。"""
    for attempt in range(3):
        result = run_nlm("notebook", "delete", notebook_id, "-y")
        if result.returncode == 0:
            return True, result.stdout, None

        if attempt < 2 and is_transient_nlm_error(result.stderr):
            time.sleep(5 * (attempt + 1))
            continue

        return False, result.stdout, result.stderr

    return False, "", "delete notebook failed after retries"


def compress_image_to_720p(input_path, output_path):
    """将图片压缩为 720P JPG 格式。"""
    try:
        from PIL import Image

        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            width, height = img.size
            if width > 1280:
                ratio = 1280 / width
                img = img.resize((1280, int(height * ratio)), Image.LANCZOS)

            img.save(output_path, "JPEG", quality=85, optimize=True)

        return True, None, None
    except Exception as exc:
        return False, None, str(exc)


def check_login():
    """检查 NotebookLM CLI 登录状态。"""
    result = run_nlm("login", "--check", "-p", NLM_PROFILE)
    if result.returncode == 0:
        return True

    login_result = run_nlm("login", "-p", NLM_PROFILE)
    return login_result.returncode == 0


def delete_all_arxiv_notebooks():
    """删除所有以 arxiv_daily 开头的 notebook。"""
    print("\n" + "-" * 60)
    print("清理旧的 arXiv notebook...")

    result = run_nlm("notebook", "list", "--json")
    if result.returncode != 0:
        print(f"  获取 notebook 列表失败: {result.stderr}")
        return

    try:
        notebooks = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"  解析 notebook 列表失败: {exc}")
        print(f"  输出片段: {result.stdout[:200]}")
        return

    arxiv_notebooks = [
        notebook
        for notebook in notebooks
        if notebook.get("title", "").startswith(NOTEBOOK_PREFIX)
    ]
    if not arxiv_notebooks:
        print(f"  没有找到旧的 {NOTEBOOK_PREFIX}_* notebook")
        print("-" * 60)
        return

    print(f"  发现 {len(arxiv_notebooks)} 个旧 notebook 需要删除")
    deleted_count = 0
    failed_count = 0

    for notebook in arxiv_notebooks:
        notebook_id = notebook.get("id")
        notebook_title = notebook.get("title", "N/A")
        if not notebook_id:
            print(f"  跳过: {notebook_title}（缺少 ID）")
            continue

        print(f"  删除: {notebook_title} ({notebook_id[:20]}...)")
        del_result = run_nlm("notebook", "delete", notebook_id, "-y")
        if del_result.returncode == 0:
            print("    已删除")
            deleted_count += 1
        else:
            print(f"    删除失败: {del_result.stderr}")
            failed_count += 1

    print(f"  清理完成: 成功 {deleted_count} 个，失败 {failed_count} 个")
    print("-" * 60)


def build_output_paths(arxiv_id, today):
    """构造图片输出路径。"""
    png_filename = f"paper_{arxiv_id}_{today}.png"
    jpg_filename = f"paper_{arxiv_id}_{today}.jpg"
    return {
        "png_filename": png_filename,
        "png_path": os.path.join(IMAGES_DIR, png_filename),
        "jpg_filename": jpg_filename,
        "jpg_path": os.path.join(IMAGES_DIR, jpg_filename),
    }


def load_existing_results():
    """加载既有处理结果。"""
    if not os.path.exists(PROCESSED_JSON):
        return []

    with open(PROCESSED_JSON, "r", encoding="utf-8") as file:
        return json.load(file)


def save_results(results):
    """保存处理结果。"""
    with open(PROCESSED_JSON, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)


def prepare_papers():
    """加载并补齐论文元数据。"""
    with open(PAPERS_JSON, "r", encoding="utf-8") as file:
        papers = json.load(file)

    print(f"\n从 RSS 加载了 {len(papers)} 篇论文")

    if len(papers) > PAPERS_LIMIT:
        mode = "DEBUG 模式" if os.environ.get("DEBUG_LIMIT") else "限制模式"
        print(f"[{mode}] 限制只处理前 {PAPERS_LIMIT} 篇论文")
        papers = papers[:PAPERS_LIMIT]

    for paper in papers:
        paper["arxiv_id"] = extract_arxiv_id(paper["abs_url"])
        paper["pdf_url"] = paper["abs_url"].replace("/abs/", "/pdf/") + ".pdf"

    return papers


def filter_pending_papers(papers, today):
    """筛选尚未生成图片的论文。"""
    papers_to_process = []
    skipped_completed = 0

    for paper in papers:
        arxiv_id = paper.get("arxiv_id")
        if not arxiv_id:
            continue

        output_paths = build_output_paths(arxiv_id, today)
        if os.path.exists(output_paths["jpg_path"]) or os.path.exists(output_paths["png_path"]):
            skipped_completed += 1
            continue

        papers_to_process.append(paper)

    if skipped_completed > 0:
        print(f"\n跳过 {skipped_completed} 篇已有图片的论文")

    return papers_to_process


def submit_paper_task(paper, today):
    """
    提交论文处理任务，只做生成前准备，不等待下载完成。
    返回任务元数据供回收阶段使用。
    """
    arxiv_id = paper.get("arxiv_id", "unknown")
    notebook_id = None
    source_id = None

    print(f"\n{'=' * 60}")
    print(f"提交任务: {arxiv_id}")
    print(f"标题: {paper.get('title', 'N/A')[:60]}...")

    try:
        notebook_name = f"{NOTEBOOK_PREFIX}_{arxiv_id}"
        print(f"  步骤1: 创建 notebook '{notebook_name}'...")
        notebook_id = create_notebook(notebook_name)
        if not notebook_id:
            print("  创建 notebook 失败: 返回值为空")
            return None
        print(f"  Notebook ID: {notebook_id[:20]}...")

        pdf_url = paper.get("pdf_url", "")
        if not pdf_url:
            print("  论文 PDF URL 为空")
            cleanup_task_notebook({"notebook_id": notebook_id})
            return None

        print("  步骤2: 提交论文 URL...")
        success, stdout, stderr = add_url_to_notebook(notebook_id, pdf_url)
        if not success:
            print("  提交失败")
            print(f"    stdout: {stdout}")
            print(f"    stderr: {stderr}")
            cleanup_task_notebook({"notebook_id": notebook_id})
            return None
        print("  已提交")

        print(f"  等待 {SOURCE_READY_WAIT} 秒让 source 完成处理...")
        time.sleep(SOURCE_READY_WAIT)

        print("  步骤3: 获取 source ID...")
        sources = get_all_sources(notebook_id)
        source_id = find_source_id(sources, pdf_url)
        if not source_id:
            print("  未找到 source ID")
            print(f"    source 数量: {len(sources)}")
            cleanup_task_notebook({"notebook_id": notebook_id})
            return None
        print(f"  Source ID: {source_id[:20]}...")

        print("  步骤4: 发起 infographic 生成...")
        success, artifact_id, error = create_infographic(notebook_id, source_id)
        if not success:
            print(f"  infographic 请求失败: {error}")
            cleanup_task_notebook({"notebook_id": notebook_id})
            return None
        print("  infographic 请求已提交")

        output_paths = build_output_paths(arxiv_id, today)
        return {
            "arxiv_id": arxiv_id,
            "paper": paper,
            "notebook_id": notebook_id,
            "source_id": source_id,
            "artifact_id": artifact_id,
            "pdf_url": pdf_url,
            "today": today,
            **output_paths,
        }
    except Exception as exc:
        print(f"  提交阶段异常: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        cleanup_task_notebook({"notebook_id": notebook_id})
        return None


def cleanup_task_notebook(task):
    """清理任务对应的 notebook。"""
    notebook_id = task.get("notebook_id")
    if not notebook_id:
        return

    try:
        del_success, _, del_error = delete_notebook(notebook_id)
        if del_success:
            print("  已删除 notebook")
        else:
            print(f"  删除 notebook 失败: {del_error}")
    except Exception as exc:
        print(f"  删除 notebook 异常: {type(exc).__name__}: {exc}")
        traceback.print_exc()


def collect_paper_task(task):
    """
    回收论文任务，负责下载、压缩、生成结果并清理 notebook。
    """
    paper = task["paper"]
    arxiv_id = task["arxiv_id"]
    png_path = task["png_path"]
    jpg_path = task["jpg_path"]
    png_filename = task["png_filename"]
    jpg_filename = task["jpg_filename"]
    artifact_id = task.get("artifact_id")

    print(f"\n{'=' * 60}")
    print(f"回收任务: {arxiv_id}")
    print(f"标题: {paper.get('title', 'N/A')[:60]}...")

    try:
        if artifact_id:
            print(f"  步骤5: 轮询等待 infographic 完成 ({artifact_id[:8]}...) ...")
            ready, artifact, wait_error = wait_for_artifact_ready(
                task["notebook_id"],
                artifact_id,
            )
            if not ready:
                print("  infographic 仍未完成")
                print(f"    错误: {wait_error}")
                cleanup_task_notebook(task)
                return None
            print(f"  infographic 状态: {artifact.get('status')}")
        else:
            print(f"  步骤5: 等待 {INFOGRAPHIC_READY_WAIT} 秒让生成开始...")
            time.sleep(INFOGRAPHIC_READY_WAIT)

        print("  步骤6: 下载图片...")
        if artifact_id:
            dl_success, stdout, dl_error = download_infographic_by_id(
                task["notebook_id"],
                artifact_id,
                png_path,
            )
        else:
            dl_success, stdout, dl_error = download_infographic_with_retry(
                task["notebook_id"],
                png_path,
                max_retries=DOWNLOAD_MAX_RETRIES,
                retry_interval=DOWNLOAD_RETRY_INTERVAL,
            )
        if not dl_success:
            print("  下载失败")
            print(f"    错误: {dl_error}")
            print(f"    stdout: {stdout}")
            cleanup_task_notebook(task)
            return None
        print(f"  已下载: {png_filename}")

        print("  步骤7: 压缩为 720P JPG...")
        rel_path = f"images/{jpg_filename}"
        compress_success, _, compress_error = compress_image_to_720p(png_path, jpg_path)
        if compress_success:
            os.remove(png_path)
            print(f"  已压缩: {jpg_filename}")
        else:
            print(f"  压缩失败，保留 PNG: {compress_error}")
            rel_path = f"images/{png_filename}"

        print("  步骤8: 删除 notebook...")
        cleanup_task_notebook(task)

        processed_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"  回收完成: {arxiv_id}")
        return {
            "arxiv_id": arxiv_id,
            "title": paper.get("title", ""),
            "authors": paper.get("authors", []),
            "abstract": paper.get("abstract", ""),
            "abs_url": paper.get("abs_url", ""),
            "pdf_url": task["pdf_url"],
            "published": paper.get("published", ""),
            "source_id": task["source_id"],
            "image": rel_path,
            "processed_date": processed_date,
        }
    except Exception as exc:
        print(f"  回收阶段异常: {type(exc).__name__}: {exc}")
        traceback.print_exc()
        cleanup_task_notebook(task)
        return None


def process_papers():
    """主处理函数。"""
    print(f"[{datetime.now()}] 开始处理 arXiv 论文")
    print("=" * 60)
    print("配置: 两阶段流水线，先批量提交，再统一轮询下载")
    print(
        f"参数: source等待 {SOURCE_READY_WAIT}s, "
        f"生成启动等待 {INFOGRAPHIC_READY_WAIT}s, "
        f"下载最多重试 {DOWNLOAD_MAX_RETRIES} 次, "
        f"artifact轮询 {ARTIFACT_STATUS_POLL_INTERVAL}s / 超时 {ARTIFACT_STATUS_TIMEOUT}s"
    )
    print("=" * 60)

    if not check_login():
        print("登录失败")
        return

    delete_all_arxiv_notebooks()

    if not os.path.exists(PAPERS_JSON):
        print(f"错误: 找不到 {PAPERS_JSON}")
        return

    papers = prepare_papers()
    today = datetime.now().strftime("%Y%m%d")
    papers_to_process = filter_pending_papers(papers, today)

    if not papers_to_process:
        print("\n所有论文已处理完成，无需新任务")
        return

    print(f"\n需要处理 {len(papers_to_process)} 篇新论文")
    print(
        "预计串行等待已拆分：提交阶段不中断，下载等待只出现在统一回收阶段"
    )

    results = load_existing_results()
    pending_tasks = []

    print(f"\n{'#' * 60}")
    print("# 阶段一：批量提交 infographic 生成任务")
    print(f"{'#' * 60}")
    submitted_count = 0

    for index, paper in enumerate(papers_to_process, 1):
        print(f"\n[{index}/{len(papers_to_process)}] 提交论文任务")
        task = submit_paper_task(paper, today)
        if task:
            pending_tasks.append(task)
            submitted_count += 1
            print(f"  提交成功，累计已提交 {submitted_count}/{len(papers_to_process)}")
        else:
            print(f"  提交失败: {paper.get('arxiv_id', 'N/A')}")

    if not pending_tasks:
        print("\n没有成功提交的任务，结束")
        return

    print(f"\n提交阶段完成，共成功提交 {len(pending_tasks)} 篇")

    print(f"\n{'#' * 60}")
    print("# 阶段二：统一回收图片、压缩并清理 notebook")
    print(f"{'#' * 60}")
    collected_count = 0

    for index, task in enumerate(pending_tasks, 1):
        print(f"\n[{index}/{len(pending_tasks)}] 回收论文任务")
        result = collect_paper_task(task)
        if result:
            results.append(result)
            collected_count += 1
            print(f"  回收成功，累计已完成 {collected_count}/{len(pending_tasks)}")
        else:
            print(f"  回收失败: {task.get('arxiv_id', 'N/A')}")

    save_results(results)

    print("\n" + "=" * 60)
    print("处理完成")
    print(f"  本次提交成功: {len(pending_tasks)} 篇")
    print(f"  本次回收成功: {collected_count} 篇")
    print(f"  累计结果数: {len(results)} 篇")
    print("=" * 60)


if __name__ == "__main__":
    process_papers()
