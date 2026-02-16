# 🔍 Troubleshooting Guide - Language Tutor

Common issues and solutions for Intel Mac (8GB RAM).

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [Performance Issues](#performance-issues)
4. [Audio Problems](#audio-problems)
5. [Claude Desktop Issues](#claude-desktop-issues)
6. [Memory Issues](#memory-issues)

---

## Installation Issues

### ❌ PyAudio Installation Failed

**Error:**
```
error: command 'clang' failed
fatal error: 'portaudio.h' file not found
```

**Solution:**
```bash
# Install PortAudio first
brew install portaudio

# Then install PyAudio
pip3 install pyaudio --break-system-packages
```

**Alternative (if still fails):**
```bash
# Install with specific compiler flags
CFLAGS="-I/opt/homebrew/include -L/opt/homebrew/lib" pip3 install pyaudio --break-system-packages
```

---

### ❌ "externally-managed-environment" Error

**Error:**
```
error: externally-managed-environment
```

**Solution:**
Use `--break-system-packages` flag:
```bash
pip3 install -r requirements.txt --break-system-packages
```

**Or use virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### ❌ Claude CLI Not Found

**Error:**
```
⚠ Claude not found, falling back to Ollama
```

**Solution 1: Install Node.js**
```bash
# Check if you have Node.js
node --version

# If not, install it
brew install node
```

**Solution 2: Install Claude CLI**
```bash
npm install -g @anthropic-ai/claude-cli

# Verify
which claude
```

**Solution 3: Fix PATH**
```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="/usr/local/bin:$PATH"
export PATH="/opt/homebrew/bin:$PATH"

# Reload
source ~/.zshrc
```

---

### ❌ Homebrew Not Found

**Error:**
```
brew: command not found
```

**Solution:**
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Follow the instructions to add Homebrew to PATH
```

---

## Runtime Errors

### ❌ "No module named 'faster_whisper'"

**Error:**
```python
ModuleNotFoundError: No module named 'faster_whisper'
```

**Solution:**
```bash
pip3 install faster-whisper --break-system-packages
```

---

### ❌ Claude Authentication Failed

**Error:**
```
Error: Not authenticated with Claude
```

**Solution:**
```bash
# Login to Claude
claude login

# This opens browser - sign in with your claude.ai account

# Verify
claude whoami
```

**If browser doesn't open:**
```bash
# Manual authentication
claude login --api-key YOUR_API_KEY
```

Get API key from: https://console.anthropic.com/settings/keys

---

### ❌ Edge TTS Not Working

**Error:**
```
🔊 TTS error: ...
```

**Solution 1: Test Edge TTS**
```bash
edge-tts --text "Hello world" --write-media test.mp3

# If it fails, check internet connection
ping -c 3 speech.platform.bing.com
```

**Solution 2: Reinstall**
```bash
pip3 uninstall edge-tts
pip3 install edge-tts --upgrade --break-system-packages
```

**Fallback:**
The app will use macOS `say` command if Edge TTS fails.

---

### ❌ Whisper Model Download Failed

**Error:**
```
Error downloading model...
```

**Solution:**
```bash
# Clear cache
rm -rf ~/.cache/huggingface

# Try again - it will re-download
python3 lang_intel.py --lang en --level B1
```

**Manual download:**
```python
# In Python
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cpu", compute_type="int8")
```

---

### ❌ Keyboard Listener Crashes

**Error:**
```
Accessibility access denied
```

**Solution:**
1. Open **System Preferences** → **Security & Privacy**
2. Go to **Privacy** tab → **Accessibility**
3. Add **Terminal** (or **iTerm**)
4. Restart the app

---

## Performance Issues

### 🐌 Whisper Too Slow (5+ seconds)

**Current model: `base` (~400MB)**

**Faster option: Switch to `tiny`**

Edit `lang_intel.py`:
```python
WHISPER_MODEL_FASTER = "tiny"  # Was "base"
```

**Comparison:**
| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny  | 75MB | 1-2s  | 85%      |
| base  | 150MB | 2-3s | 90%      |
| small | 500MB | 4-5s | 93%      |

**Trade-off:** `tiny` is faster but less accurate with accents/noise.

---

### 🐌 Claude Response Slow (10+ seconds)

**Check your internet:**
```bash
ping -c 5 api.anthropic.com
```

**Possible causes:**
- Slow internet connection
- Claude API rate limits
- Server-side processing time

**Solutions:**
1. Use Ollama for local processing (slower but consistent)
2. Check API status: https://status.anthropic.com
3. Try again later

---

### 🐌 TTS Takes Too Long

**Speed up TTS:**

Edit `lang_intel.py` and increase rate:
```python
"tts_rate": "+20%",  # Was "+5%"
```

**Or use macOS say (faster but robotic):**
```python
# Comment out Edge TTS, use fallback
subprocess.run(["say", "-v", "Samantha", text])
```

---

## Audio Problems

### 🎤 Microphone Not Working

**Test microphone:**
```bash
# Record 5 seconds
rec -r 16000 -c 1 test.wav trim 0 5

# Play back
play test.wav
```

**Check permissions:**
1. **System Preferences** → **Security & Privacy** → **Privacy** → **Microphone**
2. Enable for **Terminal** or **iTerm**

**Select correct input:**
```bash
# List audio devices
system_profiler SPAudioDataType
```

---

### 🔇 No Sound Output

**Test speakers:**
```bash
say "Testing speakers"
afplay /System/Library/Sounds/Ping.aiff
```

**Check volume:**
- System volume not muted
- App not in focus-mode with sound off

---

### 🎧 Whisper Detects Nothing

**Problem:** "Filtered: (silence)" or "(too quiet)"

**Solutions:**

1. **Speak louder** - Whisper needs clear audio
2. **Get closer to mic** - 1-2 feet optimal
3. **Reduce background noise** - Close windows, turn off fans
4. **Check input level:**
   - System Preferences → Sound → Input
   - Speak and watch the level meter

**Lower detection threshold** (edit `lang_intel.py`):
```python
# Line ~946
if np.sqrt(np.mean(audio_data ** 2)) < 0.002:  # Was 0.005
```

---

### 🗣️ Whisper Misunderstands Everything

**Common causes:**

1. **Wrong language detected**
   - Whisper auto-detects language
   - May confuse similar sounds

2. **Too much background noise**
   - Use headset with mic
   - Record in quiet room

3. **Speaking too fast**
   - Speak clearly and slightly slower
   - Pause between sentences

**Force language detection** (edit `lang_intel.py`):
```python
# In transcribe() function, add:
segments, info = model.transcribe(
    audio,
    language="en",  # Force English
    beam_size=5
)
```

---

## Claude Desktop Issues

### ❌ Claude API Rate Limited

**Error:**
```
429 Too Many Requests
```

**Solution:**
1. **Wait 1 minute** - Rate limits reset quickly
2. **Check your plan** - Free tier has limits
3. **Use Ollama** - No rate limits

```bash
python3 lang_intel.py --ollama
```

---

### ❌ Claude API Key Invalid

**Error:**
```
401 Unauthorized
```

**Solution:**
```bash
# Re-authenticate
claude logout
claude login
```

---

### ❌ Claude Gives Generic Responses

**Problem:** Responses like "I'm an AI assistant..."

**Cause:** Claude isn't following the tutor persona.

**Solution:**
System prompt is working correctly, but may need adjustment. Edit `build_tutor_prompt()` function to strengthen persona.

---

## Memory Issues

### 💾 "Out of Memory" Error

**Check available RAM:**
```bash
vm_stat | head -5
```

**Solutions:**

1. **Close unnecessary apps**
   - Chrome tabs (biggest RAM hog)
   - Slack, Discord, etc.
   - Docker containers

2. **Use Activity Monitor**
   - Applications → Utilities → Activity Monitor
   - Sort by Memory
   - Quit memory-intensive apps

3. **Use Claude instead of Ollama**
   ```bash
   # Claude runs in cloud (3-4GB RAM)
   python3 lang_intel.py
   
   # Ollama runs locally (6-8GB RAM)
   python3 lang_intel.py --ollama
   ```

4. **Restart your Mac** - Clears cached memory

---

### 💾 App Crashes After 10 Minutes

**Cause:** Memory leak or insufficient RAM

**Check memory pressure:**
```bash
memory_pressure
```

**Solutions:**

1. **Reduce conversation history** (edit `lang_intel.py`):
   ```python
   memory = ConversationMemory(max_size=10)  # Was 20
   ```

2. **Clear Whisper cache:**
   ```bash
   rm -rf ~/.cache/huggingface
   ```

3. **Use `tiny` Whisper model** (smaller memory footprint)

---

## Debugging Tips

### Enable Verbose Logging

Add at top of `lang_intel.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Components Individually

**Test Whisper:**
```python
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cpu")
segments, info = model.transcribe("test.wav")
for segment in segments:
    print(segment.text)
```

**Test Edge TTS:**
```bash
edge-tts --list-voices | grep en-US
edge-tts --voice en-US-MichelleNeural --text "Test" --write-media test.mp3
```

**Test Claude:**
```bash
echo "Say hello" | claude
```

---

## Still Having Issues?

### Collect Debug Info

```bash
# System info
sw_vers
uname -m
sysctl hw.memsize

# Python info
python3 --version
pip3 --version
pip3 list | grep -E "pyaudio|whisper|edge-tts"

# Tool versions
which claude
claude --version
brew list portaudio

# Save to file
python3 lang_intel.py --lang en --level B1 2>&1 | tee debug.log
```

### Common Solutions Summary

| Issue | Quick Fix |
|-------|-----------|
| PyAudio fails | `brew install portaudio` |
| Claude not found | `npm install -g @anthropic-ai/claude-cli` |
| Out of memory | Close apps, use Claude not Ollama |
| Whisper slow | Use `tiny` model |
| Mic not working | Check System Preferences permissions |
| TTS not working | Check internet, reinstall edge-tts |

---

**Pro Tip:** Start with a fresh terminal session after installation. Some PATH changes require a new shell.

Need more help? Check the README.md or open an issue on GitHub.