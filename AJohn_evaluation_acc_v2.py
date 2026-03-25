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

# -------------------- 固定测试数据（100正例 + 100反例）--------------------
# -------------------- 固定测试数据（100正例 + 100反例）--------------------
VALID_CERTIFICATES = [
    "经董事会批准，任命王一为首席战略官，负责公司战略规划。",
    "兹聘任李二为创新研究院院长，统筹前沿技术研究。",
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
    "经公司董事会审议，任命刘十三为研发中心总经理，全面负责研发工作。",
    "兹聘任林十四为法务部总监，自2025年3月1日起生效。",
    "任命黄十五为西南大区经理，负责区域市场开拓。",
    "经公开竞聘，聘用何十六为品牌部经理，任期两年。",
    "兹任命宋十七为首席安全官，主管公司信息安全。",
    "聘任罗十八为财务副总监，协助财务总监工作。",
    "任命梁十九为华北区域经理，自即日起执行。",
    "经研究决定，聘任邓二十为审计部经理。",
    "兹任命钟二十一为采购部副经理，负责供应商管理。",
    "聘任魏二十二为首席数据官，负责数据治理。",
    "经总裁办公会决议，任命冯二十三为海外事业部总经理。",
    "兹聘任褚二十四为首席运营官，负责日常运营工作。",
    "任命卫二十五为华中区域总经理，自2025年4月1日起生效。",
    "经绩效考评，晋升沈二十六为高级技术专家。",
    "兹聘任韩二十七为首席市场官，制定市场战略。",
    "任命杨二十八为产品总监，统筹产品规划。",
    "经董事会提名，聘任朱二十九为公司副总裁。",
    "兹任命秦三十为华东大区销售总监。",
    "聘任尤三十一为研发部副经理，任期一年。",
    "任命许三十二为客服中心经理，负责客户服务。",
    "经民主评议，任命何三十三为工会主席。",
    "兹聘任吕三十四为首席财务官，全面负责财务工作。",
    "任命施三十五为华南区域经理，自即日起生效。",
    "经公司战略委员会决定，聘任张三十六为创新业务部负责人。",
    "兹任命孔三十七为质量总监，主管质量体系。",
    "聘任曹三十八为生产厂长，负责生产调度。",
    "任命严三十九为供应链总监，优化供应链流程。",
    "经竞聘考核，聘用华四十为培训部经理。",
    "兹聘任金四十一为首席技术官，主导技术研发。",
    "任命魏四十二为西北区域经理，自2025年5月1日生效。",
    "经公司决定，聘任陶四十三为董事会秘书。",
    "兹任命姜四十四为行政总监，负责后勤保障。",
    "聘任戚四十五为信息化部经理，推进数字化转型。",
    "任命谢四十六为首席合规官，监督合规运营。",
    "经总经理提名，聘任邹四十七为副总经理。",
    "兹任命喻四十八为东北区域总经理。",
    "聘任柏四十九为战略发展部总监，任期三年。",
    "任命水五十为品牌传播总监，负责品牌推广。",
    "经董事会表决，聘任窦五十一为公司秘书。",
    "兹任命章五十二为法务副总监，协助法务工作。",
    "聘任云五十三为首席信息官，管理信息系统。",
    "任命苏五十四为人力资源副经理，负责招聘培训。",
    "经薪酬委员会决定，聘任潘五十五为薪酬福利经理。",
    "兹任命葛五十六为审计副总监。",
    "聘任奚五十七为投资总监，负责投资业务。",
    "任命范五十八为公共关系经理，维护政府关系。",
    "经安全委员会决议，聘任彭五十九为安全总监。",
    "兹任命郎六十为质量副经理。",
    "聘任鲁六十一为生产副厂长，协助生产管理。",
    "任命韦六十二为供应链副总监。",
    "经财务部推荐，聘任马六十三为财务分析经理。",
    "兹任命苗六十四为市场调研经理。",
    "聘任花六十五为产品运营总监。",
    "任命袁六十六为商务拓展经理。",
    "经技术委员会决议，聘任柳六十七为研发架构师。",
    "兹任命鲍六十八为测试部经理。",
    "聘任史六十九为运维总监，保障系统稳定。",
    "任命唐七十为前端开发经理。",
    "经项目部提名，聘任费七十一为项目经理。",
    "兹任命廉七十二为后端开发经理。",
    "聘任岑七十三为数据科学家。",
    "任命雷七十四为算法工程师经理。",
    "经人力部决议，聘任倪七十五为员工关系经理。",
    "兹任命汤七十六为薪酬专员主管。",
    "聘任殷七十七为绩效管理经理。",
    "任命罗七十八为招聘经理。",
    "经培训部推荐，聘任毕七十九为培训讲师主管。",
    "兹任命郝八十为行政主管。",
    "聘任邬八十一为后勤主管。",
    "任命安八十二为车队队长。",
    "经办公室决定，聘任常八十三为前台主管。",
    "兹任命乐八十四为档案室主任。",
    "聘任于八十五为保密办主任。",
    "任命傅八十六为法务专员主管。",
    "经风控部推荐，聘任成八十七为风控经理。",
    "兹任命游八十八为内控经理。",
    "聘任易八十九为合规专员主管。",
    "任命荀九十为知识产权经理。",
    "经技术转移中心决议，聘任贾九十一为技术转移经理。",
    "兹任命江九十二为标准化工程师主管。",
    "聘任童九十三为计量主管。",
    "任命饶九十四为实验室主任。",
    "经质量部推荐，聘任单九十五为质量体系主管。",
    "兹任命顾九十六为检验室主任。",
    "聘任欧九十七为售后经理。",
    "任命梁九十八为客服主管。",
    "经客户部决议，聘任谢九十九为客户总监。",
    "兹任命魏一百为业务拓展总监。",
]

INVALID_CERTIFICATES = [
    "任命张一为首席战略官，但公司无战略规划需求。",
    "兹聘任刘二为创新研究院院长，然而创新研究院已被撤销。",
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
    "经董事会决定，任命刘十三为研发中心总经理，同时撤销研发中心。",
    "兹聘任林十四为法务部总监，自2025年3月1日起生效，但林十四已被刑事拘留。",
    "任命黄十五为西南大区经理，负责区域市场开拓，然而黄十五从未去过西南。",
    "经公开竞聘，聘用何十六为品牌部经理，但品牌部已并入市场部。",
    "兹任命宋十七为首席安全官，但公司不设此职位。",
    "聘任罗十八为财务副总监，但财务副总监已由他人担任。",
    "任命梁十九为华北区域经理，自即日起执行，但梁十九尚未毕业。",
    "经研究决定，聘任邓二十为审计部经理，然而审计部经理职位已空缺两年。",
    "兹任命钟二十一为采购部副经理，同时任命其兼任采购部经理。",
    "聘任魏二十二为首席数据官，但公司没有数据部门。",
    "经总裁办公会决议，任命冯二十三为海外事业部总经理，然而海外事业部已裁撤。",
    "兹聘任褚二十四为首席运营官，但褚二十四已被解聘。",
    "任命卫二十五为华中区域总经理，自2025年4月1日起生效，但卫二十五仍在服刑。",
    "经绩效考评，晋升沈二十六为高级技术专家，但沈二十六的绩效不合格。",
    "兹聘任韩二十七为首席市场官，但韩二十七违反竞业协议。",
    "任命杨二十八为产品总监，同时撤销产品部。",
    "经董事会提名，聘任朱二十九为公司副总裁，但朱二十九年龄超限。",
    "兹任命秦三十为华东大区销售总监，但华东大区业务已关闭。",
    "聘任尤三十一为研发部副经理，任期一年，但研发部已解散。",
    "任命许三十二为客服中心经理，但客服中心外包。",
    "经民主评议，任命何三十三为工会主席，但何三十三不是工会会员。",
    "兹聘任吕三十四为首席财务官，但吕三十四有财务造假记录。",
    "任命施三十五为华南区域经理，自即日起生效，但华南区域经理已由他人担任。",
    "经公司战略委员会决定，聘任张三十六为创新业务部负责人，但创新业务部尚未成立。",
    "兹任命孔三十七为质量总监，但质量总监职位已被撤销。",
    "聘任曹三十八为生产厂长，但工厂已停工。",
    "任命严三十九为供应链总监，但供应链已外包。",
    "经竞聘考核，聘用华四十为培训部经理，但培训部已撤销。",
    "兹聘任金四十一为首席技术官，但金四十一无技术背景。",
    "任命魏四十二为西北区域经理，自2025年5月1日生效，但魏四十二已离职。",
    "经公司决定，聘任陶四十三为董事会秘书，但陶四十三没有董秘资格。",
    "兹任命姜四十四为行政总监，同时降级为行政助理。",
    "聘任戚四十五为信息化部经理，但信息化部已关闭。",
    "任命谢四十六为首席合规官，但谢四十六有违规记录。",
    "经总经理提名，聘任邹四十七为副总经理，但邹四十七已被免职。",
    "兹任命喻四十八为东北区域总经理，但东北区域已合并至华北。",
    "聘任柏四十九为战略发展部总监，任期三年，但战略发展部已撤销。",
    "任命水五十为品牌传播总监，但品牌传播职能已外包。",
    "经董事会表决，聘任窦五十一为公司秘书，但窦五十一不识字。",
    "兹任命章五十二为法务副总监，但法务部只有一个人。",
    "聘任云五十三为首席信息官，但公司无信息系统。",
    "任命苏五十四为人力资源副经理，但人力资源部经理已由他人担任。",
    "经薪酬委员会决定，聘任潘五十五为薪酬福利经理，但薪酬委员会已解散。",
    "兹任命葛五十六为审计副总监，但审计部已被撤销。",
    "聘任奚五十七为投资总监，但公司无投资业务。",
    "任命范五十八为公共关系经理，但范五十八有负面新闻。",
    "经安全委员会决议，聘任彭五十九为安全总监，但安全委员会已不存在。",
    "兹任命郎六十为质量副经理，但质量部只有经理一人。",
    "聘任鲁六十一为生产副厂长，但生产厂长已兼任副厂长。",
    "任命韦六十二为供应链副总监，但供应链总监已由他人兼任。",
    "经财务部推荐，聘任马六十三为财务分析经理，但马六十三未通过CPA考试。",
    "兹任命苗六十四为市场调研经理，但市场调研已外包。",
    "聘任花六十五为产品运营总监，但产品尚未上线。",
    "任命袁六十六为商务拓展经理，但袁六十六无商务经验。",
    "经技术委员会决议，聘任柳六十七为研发架构师，但技术委员会已撤销。",
    "兹任命鲍六十八为测试部经理，但测试部已并入研发部。",
    "聘任史六十九为运维总监，但系统已上云，无运维需求。",
    "任命唐七十为前端开发经理，但公司已决定全部外包前端开发。",
    "经项目部提名，聘任费七十一为项目经理，但项目已终止。",
    "兹任命廉七十二为后端开发经理，但后端团队已解散。",
    "聘任岑七十三为数据科学家，但公司无数据可用。",
    "任命雷七十四为算法工程师经理，但算法团队已解散。",
    "经人力部决议，聘任倪七十五为员工关系经理，但员工关系由HRBP兼任。",
    "兹任命汤七十六为薪酬专员主管，但薪酬专员只有一人。",
    "聘任殷七十七为绩效管理经理，但绩效管理职能已外包。",
    "任命罗七十八为招聘经理，但招聘已暂停。",
    "经培训部推荐，聘任毕七十九为培训讲师主管，但培训部已撤销。",
    "兹任命郝八十为行政主管，但行政部已合并到综合部。",
    "聘任邬八十一为后勤主管，但后勤已外包。",
    "任命安八十二为车队队长，但公司已无车队。",
    "经办公室决定，聘任常八十三为前台主管，但前台已外包。",
    "兹任命乐八十四为档案室主任，但档案室已撤销。",
    "聘任于八十五为保密办主任，但保密办已并入行政部。",
    "任命傅八十六为法务专员主管，但法务专员已离职。",
    "经风控部推荐，聘任成八十七为风控经理，但风控部已撤销。",
    "兹任命游八十八为内控经理，但内控职能由财务部代管。",
    "聘任易八十九为合规专员主管，但合规部已撤销。",
    "任命荀九十为知识产权经理，但公司已无知识产权。",
    "经技术转移中心决议，聘任贾九十一为技术转移经理，但技术转移中心已关闭。",
    "兹任命江九十二为标准化工程师主管，但标准化工作已停止。",
    "聘任童九十三为计量主管，但计量设备已报废。",
    "任命饶九十四为实验室主任，但实验室已关闭。",
    "经质量部推荐，聘任单九十五为质量体系主管，但质量体系已外包。",
    "兹任命顾九十六为检验室主任，但检验室已撤销。",
    "聘任欧九十七为售后经理，但售后已外包。",
    "任命梁九十八为客服主管，但客服已AI化。",
    "经客户部决议，聘任谢九十九为客户总监，但客户部已解散。",
    "兹任命魏一百为业务拓展总监，但业务拓展已暂停。",
]

def build_test_cases(num_positive=100, num_negative=100):
    """使用预定义的固定列表构造测试用例，每条唯一"""
    # 确保列表长度足够
    if len(VALID_CERTIFICATES) < num_positive:
        raise ValueError(f"VALID_CERTIFICATES 只有 {len(VALID_CERTIFICATES)} 条，需要 {num_positive} 条")
    if len(INVALID_CERTIFICATES) < num_negative:
        raise ValueError(f"INVALID_CERTIFICATES 只有 {len(INVALID_CERTIFICATES)} 条，需要 {num_negative} 条")
    
    test_cases = []
    # 正例：取前 num_positive 条
    for cert in VALID_CERTIFICATES[:num_positive]:
        prompt = f"请判断以下任命证书文本是否符合中文表达逻辑，只回答'合理'或'不合理'，不要有其他内容。\n证书文本：{cert}"
        test_cases.append((prompt, True))
    # 反例：取前 num_negative 条
    for cert in INVALID_CERTIFICATES[:num_negative]:
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