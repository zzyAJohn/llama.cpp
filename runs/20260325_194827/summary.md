# 任命证书逻辑判断评测报告

## 运行配置

- **timestamp**: 2026-03-25T19:48:27
- **platform**: Windows-10-10.0.19045-SP0
- **python**: 3.9.19 (main, May  6 2024, 20:12:36) [MSC v.1916 64 bit (AMD64)]
- **exe_path**: build\bin\Release\local_llm.exe
- **model_path**: models\Qwen3.5-0.8B.Q4_K_M.gguf
- **max_new_tokens**: 64
- **num_positive**: 100
- **num_negative**: 100
- **output_dir**: runs\20260325_194827

## 评测指标

- **准确率 (Accuracy)**: 0.5450
- **精确率 (Precision)**: 0.6286
- **召回率 (Recall)**: 0.2200
- **F1 分数 (F1 Score)**: 0.3259

## 混淆矩阵

|               | 预测合理 | 预测不合理 |
|---------------|----------|------------|
| 实际合理     |     22 |         78 |
| 实际不合理   |     13 |         87 |
