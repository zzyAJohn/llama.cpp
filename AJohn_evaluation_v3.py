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

import matplotlib.pyplot as plt


DEFAULT_PROMPTS = [
    "你好",
    "请简单介绍一下人工智能",
    "请写一段关于机器学习的介绍，200字左右",
    "请详细解释深度学习的原理，并举例说明其应用场景",
    "写一篇关于未来科技发展的短文，500字",
    "解释Transformer模型的结构和原理",
    "介绍操作系统的基本组成",
    "解释什么是数据库事务以及ACID特性",
    "讲解C++中的智能指针",
    "分析一下计算机网络中的TCP协议",
]


def parse_args():
    parser = argparse.ArgumentParser(description="llama.cpp performance evaluation")
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
        default=256,
        help="maximum generated tokens for each sample",
    )
    parser.add_argument(
        "--outdir",
        default="runs",
        help="output directory for logs, csv, and plots",
    )
    parser.add_argument(
        "--prompt-file",
        default="",
        help="optional prompt txt file, one prompt per line",
    )
    return parser.parse_args()


def make_run_dir(base_dir: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(base_dir) / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "samples").mkdir(exist_ok=True)
    return run_dir


def load_prompts(prompt_file: str):
    if not prompt_file:
        return DEFAULT_PROMPTS

    path = Path(prompt_file)
    if not path.exists():
        raise FileNotFoundError(f"prompt file not found: {prompt_file}")

    prompts = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s:
                prompts.append(s)

    if not prompts:
        raise ValueError("prompt file is empty")
    return prompts


def rough_token_count(text: str) -> int:
    """
    Approximate token count for mixed Chinese/English text.
    This is not model-true token IDs, but it is stable and good enough
    for comparative evaluation across prompts.
    """
    if not text.strip():
        return 0

    # Chinese chars, latin words/numbers, or punctuation/symbol blocks
    pattern = re.compile(
        r"[\u4e00-\u9fff]|[A-Za-z0-9_]+|[^\w\s]",
        re.UNICODE,
    )
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
    # 将 prompt 写入临时文件
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
            prompt_file,            # 使用文件代替 -p
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
        answer = clean_output(raw_output)
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
        # 清理临时文件
        os.unlink(prompt_file)

def save_csv(path: Path, rows: list[dict]):
    fieldnames = [
        "sample_id",
        "timestamp",
        "prompt",
        "prompt_chars",
        "prompt_token_est",
        "model_path",
        "exe_path",
        "max_new_tokens",
        "status",
        "ttft",
        "tpot",
        "e2e",
        "output_chars",
        "output_token_est",
        "return_code",
        "cmd_str",
        "answer",
        "error",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def clean_output(text: str) -> str:
    lines = text.splitlines()
    clean_lines = []

    for line in lines:
        if any(keyword in line for keyword in [
            "Loading model",
            "available commands",
            "llama_memory",
            "[Start thinking]",
            "[End thinking]",
            "build      :",
            "modalities :",
            "Prompt:",
            "Generation:",
            "Exiting..."
        ]):
            continue

        # 过滤 ASCII banner
        if set(line.strip()) <= set("▄█▀ "):
            continue

        clean_lines.append(line)

    return "\n".join(clean_lines).strip()

def save_run_config(path: Path, config: dict):
    with path.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def plot_metrics(run_dir: Path, rows: list[dict]):
    x = [r["prompt_chars"] for r in rows]
    ttft = [r["ttft"] for r in rows]
    tpot = [r["tpot"] for r in rows]
    e2e = [r["e2e"] for r in rows]
    out_tokens = [r["output_token_est"] for r in rows]

    # TTFT plot
    plt.figure()
    plt.plot(x, ttft, marker="o")
    plt.xlabel("Prompt length (chars)")
    plt.ylabel("TTFT (s)")
    plt.title("Prompt Length vs TTFT")
    plt.tight_layout()
    plt.savefig(run_dir / "ttft.png", dpi=200)
    plt.close()

    # TPOT plot
    plt.figure()
    plt.plot(x, tpot, marker="o")
    plt.xlabel("Prompt length (chars)")
    plt.ylabel("TPOT (s/token, estimated)")
    plt.title("Prompt Length vs TPOT")
    plt.tight_layout()
    plt.savefig(run_dir / "tpot.png", dpi=200)
    plt.close()

    # E2E plot
    plt.figure()
    plt.plot(x, e2e, marker="o")
    plt.xlabel("Prompt length (chars)")
    plt.ylabel("E2E (s)")
    plt.title("Prompt Length vs E2E")
    plt.tight_layout()
    plt.savefig(run_dir / "e2e.png", dpi=200)
    plt.close()

    # Output tokens plot
    plt.figure()
    plt.plot(x, out_tokens, marker="o")
    plt.xlabel("Prompt length (chars)")
    plt.ylabel("Output tokens (estimated)")
    plt.title("Prompt Length vs Output Length")
    plt.tight_layout()
    plt.savefig(run_dir / "output_tokens.png", dpi=200)
    plt.close()


def save_summary_md(path: Path, rows: list[dict], config: dict):
    def avg(vals):
        return sum(vals) / len(vals) if vals else 0.0

    ttft_avg = avg([r["ttft"] for r in rows])
    tpot_avg = avg([r["tpot"] for r in rows])
    e2e_avg = avg([r["e2e"] for r in rows])

    with path.open("w", encoding="utf-8") as f:
        f.write("# Performance Summary\n\n")
        f.write("## Run Config\n\n")
        for k, v in config.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n## Averages\n\n")
        f.write(f"- **Average TTFT**: {ttft_avg:.6f}s\n")
        f.write(f"- **Average TPOT**: {tpot_avg:.6f}s/token\n")
        f.write(f"- **Average E2E**: {e2e_avg:.6f}s\n\n")
        f.write("## Samples\n\n")
        f.write("| ID | Prompt chars | Output tokens(est.) | TTFT(s) | TPOT(s/token) | E2E(s) |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")
        for r in rows:
            f.write(
                f"| {r['sample_id']} | {r['prompt_chars']} | {r['output_token_est']} | "
                f"{r['ttft']:.6f} | {r['tpot']:.6f} | {r['e2e']:.6f} |\n"
            )


def main():
    args = parse_args()
    exe_path = str(Path(args.exe))
    model_path = str(Path(args.model))
    prompts = load_prompts(args.prompt_file)

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
        "prompt_count": len(prompts),
        "output_dir": str(run_dir),
    }
    save_run_config(config_path, run_config)

    rows = []

    for idx, prompt in enumerate(prompts, start=1):
        sample_id = f"{idx:02d}"
        timestamp = datetime.now().isoformat(timespec="seconds")
        prompt_chars = len(prompt)
        prompt_token_est = rough_token_count(prompt)

        print(f"\n=== 测试 prompt {sample_id}: {prompt[:24]} ===", flush=True)

        try:
            result = run_one_sample(exe_path, model_path, prompt, args.max_new_tokens)
            status = "ok"
            error = ""
        except Exception as e:
            status = "error"
            error = str(e)
            result = {
                "cmd_str": "",
                "answer": "",
                "ttft": 0.0,
                "e2e": 0.0,
                "output_token_est": 0,
                "tpot": 0.0,
                "return_code": -1,
            }

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
            "output_chars": len(result["answer"]),
            "output_token_est": result["output_token_est"],
            "return_code": result["return_code"],
            "cmd_str": result["cmd_str"],
            "answer": result["answer"],
            "error": error,
        }

        rows.append(row)

        write_jsonl(jsonl_path, row)
        write_sample_txt(run_dir / "samples" / f"sample_{sample_id}.txt", row)

        print(
            f"TTFT: {row['ttft']:.3f}s, "
            f"TPOT: {row['tpot']:.3f}s/token, "
            f"E2E: {row['e2e']:.3f}s, "
            f"OutputTokens(est): {row['output_token_est']}",
            flush=True,
        )

    save_csv(csv_path, rows)
    plot_metrics(run_dir, rows)
    save_summary_md(summary_path, rows, run_config)

    print("\nDone.")
    print(f"Logs: {run_dir}")
    print(f"- JSONL: {jsonl_path}")
    print(f"- CSV  : {csv_path}")
    print(f"- MD   : {summary_path}")
    print(f"- Plots: ttft.png / tpot.png / e2e.png / output_tokens.png")


if __name__ == "__main__":
    main()