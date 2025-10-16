# script to test segmentation problem with ASR whisper
import whisper
m = whisper.load_model("tiny")
print("loaded", type(m))