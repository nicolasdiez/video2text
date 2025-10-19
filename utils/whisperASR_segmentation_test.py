# /utils/whisperASR_segmentation_test.py

# IMPORTANT!!!:
# this is a snippet code, NOT part of the application code base. 
# What´s this script used for? --> script to test segmentation problem with ASR whisper. If this code snippet does not throw a "segmentation" error, then the whisper module works fine. The problem is on my app logic.

"""
- name: Whisper model id (e.g., "tiny", "base", "small").
- device: "cpu" or "cuda".
"""

import whisper
m = whisper.load_model(name="tiny", device="cpu")
print("loaded", type(m))