import subprocess
import time

exe_path = r".\build\bin\Release\local_llm.exe"
model_path = r".\models\Qwen3.5-0.8B.Q4_K_M.gguf"

prompts = [
    "你好",
    "请简单介绍一下人工智能",
    "请写一段关于机器学习的介绍，200字左右",
    "请详细解释深度学习的原理，并举例说明其应用场景",
    "写一篇关于未来科技发展的短文，500字",
    "解释Transformer模型的结构和原理",
    "介绍操作系统的基本组成",
    "解释什么是数据库事务以及ACID特性",
    "讲解C++中的智能指针",
    "分析一下计算机网络中的TCP协议"
]

results = []

for prompt in prompts:
    print(f"\n=== 测试 prompt: {prompt[:20]} ===")
    start_time = time.time()

    process = subprocess.Popen(
        [
            exe_path,
            "--simple-io",
            "-st",
            "--no-warmup",
            "-n", "64",
            "-m", model_path,
            "-p", prompt,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    first_token_time = None
    output = []

    while True:
        ch = process.stdout.read(1)
        if ch == "" and process.poll() is not None:
            break
        if ch:
            if first_token_time is None:
                first_token_time = time.time()
            output.append(ch)

    end_time = time.time()
    text = "".join(output)

    token_count = len(text.split())
    ttft = first_token_time - start_time if first_token_time else 0
    e2e = end_time - start_time
    tpot = (e2e - ttft) / token_count if token_count > 0 else 0

    results.append((prompt, ttft, tpot, e2e, token_count))
    print(f"TTFT: {ttft:.3f}s, TPOT: {tpot:.3f}s, E2E: {e2e:.3f}s")

with open("performance.txt", "w", encoding="utf-8") as f:
    for r in results:
        f.write(str(r) + "\n")