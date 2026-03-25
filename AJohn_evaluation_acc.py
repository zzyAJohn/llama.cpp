import argparse
import csv
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
import random

import matplotlib.pyplot as plt

# -------------------- 生成测试数据 --------------------
def generate_appointment_certificate(valid: bool) -> str:
    """
    生成一条任命证书文本。
    valid=True 返回符合逻辑的正例，valid=False 返回不合逻辑的反例。
    """
    # 正例模板
    valid_templates = [
        "经公司董事会研究决定，任命张三为技术部经理，自2025年1月1日起生效。",
        "兹任命李四担任销售总监，全面负责销售团队管理工作。",
        "根据公司发展需要，聘任王五为财务总监，任期三年。",
        "任命赵六为项目负责人，负责新产品研发项目。",
        "经考核合格，决定聘用周七为市场部副经理。",
        "兹聘任吴八为首席架构师，主管技术架构设计。",
        "任命郑九为人力资源总监，自即日起执行。",
        "经总经理办公会决议，任命孙十为运营总监。",
        "聘任钱十一为总工程师，负责技术管理工作。",
        "根据工作需要，任命陈十二为华东区域经理。",
    ]
    # 反例：添加逻辑错误或表达问题
    invalid_templates = [
        "经公司董事会研究决定，任命张三为技术部经理，自2025年1月1日起生效，但张三昨天已离职。",
        "兹任命李四担任销售总监，同时解除其销售总监职务。",
        "聘任王五为财务总监，任期三年，但财务总监岗位已撤销。",
        "任命赵六为项目负责人，负责新产品研发项目，但赵六没有相关经验。",
        "经考核合格，决定聘用周七为市场部副经理，然而周七从未从事过市场工作。",
        "兹聘任吴八为首席架构师，但公司没有架构师岗位。",
        "任命郑九为人力资源总监，自即日起执行，但郑九尚未入职。",
        "经总经理办公会决议，任命孙十为运营总监，而运营部已解散。",
        "聘任钱十一为总工程师，但钱十一学历造假。",
        "任命陈十二为华东区域经理，但华东区域经理职位已由他人担任。",
    ]

    # 随机选择一个模板，可添加更多变体
    if valid:
        text = random.choice(valid_templates)
        # 可添加日期、部门等细节增加多样性
        if random.random() > 0.5:
            text = text.replace("技术部经理", "技术研发部经理")
        return text
    else:
        text = random.choice(invalid_templates)
        # 增加随机错误
        if random.random() > 0.7:
            text += "（注：此任命与公司规定冲突）"
        return text

def build_test_cases(num_positive=100, num_negative=100):
    """构造测试用例列表，每个元素为 (prompt_text, label)"""
    test_cases = []
    # 正例
    for _ in range(num_positive):
        cert = generate_appointment_certificate(valid=True)
        prompt = f"请判断以下任命证书文本是否符合中文表达逻辑，只回答'合理'或'不合理'，不要有其他内容。\n证书文本：{cert}"
        test_cases.append((prompt, True))
    # 反例
    for _ in range(num_negative):
        cert = generate_appointment_certificate(valid=False)
        prompt = f"请判断以下任命证书文本是否符合中文表达逻辑，只回答'合理'或'不合理'，不要有其他内容。\n证书文本：{cert}"
        test_cases.append((prompt, False))
    # 打乱顺序
    random.shuffle(test_cases)
    return test_cases

# -------------------- 原有函数（略作调整） --------------------
def parse_args():
    parser = argparse.ArgumentParser(description="Judge appointment certificate logic")
    parser.add_argument(
        "--exe",
        default=r".\build\bin\Release\local_llm.exe",
        help="local_llm.exe path",
    )
    parser.add_argument(
        "--model",
        default=r".\models\Qwen3.5-0.8B.Q4_K_M.gguf",
        help="model gguf path",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=64,          # 判断任务只需简短回答，降低 token 数
        help="maximum generated tokens for each sample",
    )
    parser.add_argument(
        "--outdir",
        default="runs",
        help="output directory for logs, csv, and plots",
    )
    # 移除 --prompt-file 参数，因为现在由程序内部生成
    return parser.parse_args()

def make_run_dir(base_dir: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(base_dir) / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "samples").mkdir(exist_ok=True)
    return run_dir

def rough_token_count(text: str) -> int:
    if not text.strip():
        return 0
    pattern = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+|[^\w\s]", re.UNICODE)
    return len(pattern.findall(text))

def write_jsonl(path: Path, record: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def write_sample_txt(path: Path, record: dict):
    with path.open("w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"Sample ID   : {record['sample_id']}\n")
        f.write(f"Timestamp   : {record['timestamp']}\n")
        f.write(f"Model       : {record['model_path']}\n")
        f.write(f"Executable  : {record['exe_path']}\n")
        f.write(f"Prompt chars: {record['prompt_chars']}\n")
        f.write(f"Prompt est. : {record['prompt_token_est']}\n")
        f.write(f"Max new tok : {record['max_new_tokens']}\n")
        f.write(f"Status      : {record['status']}\n")
        f.write(f"TTFT        : {record['ttft']:.6f}s\n")
        f.write(f"TPOT        : {record['tpot']:.6f}s\n")
        f.write(f"E2E         : {record['e2e']:.6f}s\n")
        f.write(f"Output chars: {record['output_chars']}\n")
        f.write(f"Output est. : {record['output_token_est']}\n")
        f.write("\nPROMPT\n")
        f.write("-" * 80 + "\n")
        f.write(record["prompt"] + "\n")
        f.write("\nANSWER\n")
        f.write("-" * 80 + "\n")
        f.write(record["answer"] + "\n")
        f.write("\nCMD\n")
        f.write("-" * 80 + "\n")
        f.write(record["cmd_str"] + "\n")
        if record.get("error"):
            f.write("\nERROR\n")
            f.write("-" * 80 + "\n")
            f.write(record["error"] + "\n")
        f.write("=" * 80 + "\n")

import tempfile
import os

def run_one_sample(exe_path: str, model_path: str, prompt: str, max_new_tokens: int):
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        cmd = [
            exe_path,
            "--simple-io",
            "-st",
            "--no-warmup",
            "-n",
            str(max_new_tokens),
            "-m",
            model_path,
            "-f",
            prompt_file,
        ]
        cmd_str = subprocess.list2cmdline(cmd)
        start_time = time.time()

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        first_token_time = None
        out_chunks = []
        while True:
            ch = process.stdout.read(1)
            if ch == "" and process.poll() is not None:
                break
            if ch:
                if first_token_time is None:
                    first_token_time = time.time()
                out_chunks.append(ch)

        end_time = time.time()
        raw_output = "".join(out_chunks)
        answer = clean_output(raw_output)   # 去除系统信息
        return_code = process.returncode

        ttft = (first_token_time - start_time) if first_token_time else 0.0
        e2e = end_time - start_time
        output_token_est = rough_token_count(answer)
        tpot = ((e2e - ttft) / output_token_est) if output_token_est > 0 else 0.0

        return {
            "cmd_str": cmd_str,
            "answer": answer,
            "ttft": ttft,
            "e2e": e2e,
            "output_token_est": output_token_est,
            "tpot": tpot,
            "return_code": return_code,
        }
    finally:
        os.unlink(prompt_file)

def clean_output(text: str) -> str:
    """去除系统信息，只保留模型输出"""
    lines = text.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith("> "):
            start_idx = i + 1
            break
    if start_idx is None:
        filtered = []
        for line in lines:
            if any(k in line for k in ["Loading model", "available commands", "llama_memory", "build      :", "modalities :", "Exiting..."]):
                continue
            if set(line.strip()) <= set("▄█▀ "):
                continue
            filtered.append(line)
        return "\n".join(filtered).strip()
    result_lines = []
    for line in lines[start_idx:]:
        if any(k in line for k in ["Exiting...", "Loading model", "available commands"]):
            continue
        result_lines.append(line)
    return "\n".join(result_lines).strip()

def save_csv(path: Path, rows: list[dict]):
    fieldnames = [
        "sample_id", "timestamp", "prompt", "prompt_chars", "prompt_token_est",
        "model_path", "exe_path", "max_new_tokens", "status", "ttft", "tpot",
        "e2e", "output_chars", "output_token_est", "return_code", "cmd_str",
        "answer", "error", "true_label", "pred_label"
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def save_run_config(path: Path, config: dict):
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def plot_metrics(run_dir: Path, rows: list[dict]):
    # 此函数可保留，但数据可能不适用；简单注释掉或留空
    pass

def parse_model_answer(answer: str) -> bool:
    """从模型回答中提取合理/不合理判断"""
    answer = answer.strip().lower()
    # 优先匹配明确的关键词
    if "合理" in answer and "不合理" not in answer:
        return True
    if "不合理" in answer:
        return False
    # 次优匹配英文
    if "reasonable" in answer or "correct" in answer:
        return True
    if "unreasonable" in answer or "incorrect" in answer:
        return False
    # 默认当作不合理（保守）
    return False

def save_summary_md(path: Path, rows: list[dict], config: dict, metrics: dict):
    with path.open("w", encoding="utf-8") as f:
        f.write("# 任命证书逻辑判断评测报告\n\n")
        f.write("## 运行配置\n\n")
        for k, v in config.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n## 评测指标\n\n")
        f.write(f"- **准确率 (Accuracy)**: {metrics['accuracy']:.4f}\n")
        f.write(f"- **精确率 (Precision)**: {metrics['precision']:.4f}\n")
        f.write(f"- **召回率 (Recall)**: {metrics['recall']:.4f}\n")
        f.write(f"- **F1 分数 (F1 Score)**: {metrics['f1']:.4f}\n")
        f.write("\n## 混淆矩阵\n\n")
        f.write("|               | 预测合理 | 预测不合理 |\n")
        f.write("|---------------|----------|------------|\n")
        f.write(f"| 实际合理     | {metrics['tp']:>6} | {metrics['fn']:>10} |\n")
        f.write(f"| 实际不合理   | {metrics['fp']:>6} | {metrics['tn']:>10} |\n")

def main():
    args = parse_args()
    exe_path = str(Path(args.exe))
    model_path = str(Path(args.model))

    # 生成测试用例
    print("生成测试用例...")
    test_cases = build_test_cases(num_positive=100, num_negative=100)
    print(f"共生成 {len(test_cases)} 条测试用例 (正例100, 反例100)")

    if not Path(exe_path).exists():
        raise FileNotFoundError(f"exe not found: {exe_path}")
    if not Path(model_path).exists():
        raise FileNotFoundError(f"model not found: {model_path}")

    run_dir = make_run_dir(args.outdir)
    jsonl_path = run_dir / "results.jsonl"
    csv_path = run_dir / "results.csv"
    summary_path = run_dir / "summary.md"
    config_path = run_dir / "run_config.json"

    run_config = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "python": sys.version.replace("\n", " "),
        "exe_path": exe_path,
        "model_path": model_path,
        "max_new_tokens": args.max_new_tokens,
        "num_positive": 100,
        "num_negative": 100,
        "output_dir": str(run_dir),
    }
    save_run_config(config_path, run_config)

    rows = []
    tp = fp = tn = fn = 0

    for idx, (prompt, true_label) in enumerate(test_cases, start=1):
        sample_id = f"{idx:04d}"
        timestamp = datetime.now().isoformat(timespec="seconds")
        prompt_chars = len(prompt)
        prompt_token_est = rough_token_count(prompt)

        print(f"\n=== 测试 #{sample_id} ===", flush=True)

        try:
            result = run_one_sample(exe_path, model_path, prompt, args.max_new_tokens)
            status = "ok"
            error = ""
            answer = result["answer"]
            pred_label = parse_model_answer(answer)
        except Exception as e:
            status = "error"
            error = str(e)
            result = {
                "cmd_str": "",
                "answer": "",
                "ttft": 0.0, "e2e": 0.0,
                "output_token_est": 0, "tpot": 0.0,
                "return_code": -1,
            }
            pred_label = False   # 出错时默认不合理
            answer = ""

        # 更新混淆矩阵
        if true_label and pred_label:
            tp += 1
        elif true_label and not pred_label:
            fn += 1
        elif not true_label and pred_label:
            fp += 1
        else:
            tn += 1

        row = {
            "sample_id": sample_id,
            "timestamp": timestamp,
            "prompt": prompt,
            "prompt_chars": prompt_chars,
            "prompt_token_est": prompt_token_est,
            "model_path": model_path,
            "exe_path": exe_path,
            "max_new_tokens": args.max_new_tokens,
            "status": status,
            "ttft": result["ttft"],
            "tpot": result["tpot"],
            "e2e": result["e2e"],
            "output_chars": len(answer),
            "output_token_est": result["output_token_est"],
            "return_code": result["return_code"],
            "cmd_str": result["cmd_str"],
            "answer": answer,
            "error": error,
            "true_label": true_label,
            "pred_label": pred_label,
        }
        rows.append(row)

        write_jsonl(jsonl_path, row)
        write_sample_txt(run_dir / "samples" / f"sample_{sample_id}.txt", row)

        print(f"真实: {'合理' if true_label else '不合理'}, 预测: {'合理' if pred_label else '不合理'}, TTFT: {row['ttft']:.3f}s", flush=True)

    # 计算指标
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    metrics = {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

    save_csv(csv_path, rows)
    plot_metrics(run_dir, rows)   # 可保留，但实际不使用
    save_summary_md(summary_path, rows, run_config, metrics)

    print("\nDone.")
    print(f"Logs: {run_dir}")
    print(f"- JSONL: {jsonl_path}")
    print(f"- CSV  : {csv_path}")
    print(f"- MD   : {summary_path}")
    print("\n评测指标:")
    print(f"准确率: {accuracy:.4f}")
    print(f"精确率: {precision:.4f}")
    print(f"召回率: {recall:.4f}")
    print(f"F1分数: {f1:.4f}")

if __name__ == "__main__":
    main()