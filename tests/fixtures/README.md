# Test audio fixtures

## `sample.webm`

- 格式：WebM / Opus，48 kHz 编码输入，解码为 16 kHz mono float32
- 时长：约 1 秒
- 内容：440 Hz 正弦波（用于容器/解码测试，不是语音）
- 来源：由项目测试生成的 1 秒 16 kHz mono PCM WAV，通过 PyAV（libopus）转码
- 版权：项目自生成，无第三方素材、无个人信息
- 用途：T2.3/T2.6 验证浏览器录音容器（WebM/Opus）可被后端解码

重新生成方式（PyAV 已安装时）：

```python
# 以 tests/conftest.py 的 make_wav_bytes 生成 WAV，再用 PyAV libopus 编码为 WebM
```

不要求运行期安装系统 ffmpeg；PyAV wheel 自带 FFmpeg 库。
