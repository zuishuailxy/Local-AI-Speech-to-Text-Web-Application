# T3.6 真实模型基线（Whisper small / CPU int8）

- 日期：2026-10-27
- 模型：`Systran/faster-whisper-small`（CTranslate2）
- 模型目录：`models/faster-whisper-small`（未提交 Git）
- 运行环境：macOS arm64 / Apple M1 / 16 GB RAM / CPU
- 运行参数：`device=cpu`、`compute_type=int8`、`cpu_threads=4`、`beam_size=5`、`vad_filter=True`
- 样本：`samples/chinese.wav`（12.0 s）、`samples/english.wav`（9.0 s）
- 参考文本：`samples/reference.txt`（用户已确认）

## 测量方法

1. 用 PyAV 解码为 16 kHz mono float32，记录解码耗时。
2. `WhisperTranscriber.warmup()` 加载本地模型，记录加载耗时。
3. 对每段样本连续推理 3 次，取中位数；RTF = inference_seconds / audio_duration。
4. 中文按去除空白/标点后的字符编辑距离计算 CER；英文按小写分词后的词编辑距离计算 WER。

## 结果

### 中文

```text
模型输出:
轻轻地我走了,占如我轻轻地来。我轻轻地抓手,做别西天的云彩。那河畔的金牛是西洋中的新娘。

参考:
轻轻的我走了，正如我轻轻的来；我轻轻的招手，作别西天的云彩。
那河畔的金柳，是夕阳中的新娘。

duration: 12.000 s
decode: 0.022 s
inference: [3.430, 2.949, 3.470] s, median 3.430 s
RTF: 0.286
CER: 0.231
```

### 英文

```text
模型输出:
Never give up. Never lose hope. Always have faith. It allows you to cope.

参考:
Never give up. Never lose hope. Always have faith. It allows you to cope.

duration: 9.000 s
decode: 0.009 s
inference: [1.608, 1.769, 1.600] s, median 1.608 s
RTF: 0.179
WER: 0.000
```

### 模型加载

```text
load: 0.987 s
```

## 质量分析

- 英文：完全匹配参考文本；标点/大小写正常。
- 中文：可辨认，但有明显同音/近音替换：
  - 正如 → 占如
  - 招手 → 抓手
  - 作别 → 做别
  - 金柳 → 金牛
  - 夕阳 → 西洋
- 中文输出为简体中文；句末标点基本存在；未观察到整段幻觉/重复。
- CER 0.231 在计划初定阈值 0.3 以内，英文 WER 0.000。
- 中文错误集中在近音词，属于 small 模型能力边界；样本清晰、语速正常，不是音频不可用导致。

## 决策

**维持 faster-whisper Whisper small（CPU int8）作为主模型。**

理由：

- 中英文均能完成真实识别，结果非空且可辨认；
- 英文准确率好，中文 CER 在可接受阈值内；
- CPU RTF 0.18–0.29，普通开发机可运行；
- 本地加载与离线路径已验证；
- 不触发 T3.11 的 SenseVoice 评估（当前不满足“准确率/延迟不达标”条件）。

风险：中文同音错误会出现在演示文本中；测试报告会如实记录，不用模型输出替代参考文本。若后续 F6 滚动窗口延迟明显，再按 T3.11 做 SenseVoice 时间盒评估。

## G2 门禁

- [x] 中文真实识别非空且可辨认
- [x] 英文真实识别非空且可辨认
- [x] 记录原始输出、耗时、RTF、CER/WER
- [x] 维持 small 的决策已记录

## 备注

- 本结果基于 2 段 9–12 秒清晰人声，不代表所有口音/噪声场景。
- 模型权重不进入 Git；真实模型测试的自动化用例在 T5.2。
