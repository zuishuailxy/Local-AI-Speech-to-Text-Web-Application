class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    const size =
      (options && options.processorOptions && options.processorOptions.frameSize) ||
      4096;
    this.frameSize = size;
    this.buffer = new Float32Array(size);
    this.offset = 0;
  }

  process(inputs) {
    const input = inputs[0] && inputs[0][0];
    if (!input || input.length === 0) {
      return true;
    }

    let index = 0;
    while (index < input.length) {
      const remaining = this.frameSize - this.offset;
      const take = Math.min(remaining, input.length - index);
      this.buffer.set(input.subarray(index, index + take), this.offset);
      this.offset += take;
      index += take;

      if (this.offset >= this.frameSize) {
        this.port.postMessage(this.buffer);
        this.buffer = new Float32Array(this.frameSize);
        this.offset = 0;
      }
    }
    return true;
  }
}

registerProcessor("pcm-capture", PcmCaptureProcessor);
