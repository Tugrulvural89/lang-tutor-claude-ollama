# 🔧 Installation Guide - Language Tutor (Intel Mac)

Complete step-by-step installation guide for Intel MacBook Air/Pro (8GB RAM).

## Prerequisites Check

Before starting, verify your system:

```bash
# Check macOS version (should be 10.14+)
sw_vers

# Check architecture (should show x86_64)
uname -m

# Check available RAM (should be at least 8GB)
sysctl hw.memsize | awk '{print $2/1024/1024/1024 " GB"}'
```

## Method 1: Automated Installation (Recommended)

### Step 1: Download Files
Download these files:
- `lang_intel.py`
- `setup_intel.sh`
- `requirements.txt`

### Step 2: Run Setup Script
```bash
cd ~/Downloads  # or wherever you saved the files
chmod +x setup_intel.sh
./setup_intel.sh
```

The script will:
1. ✅ Install PortAudio via Homebrew
2. ✅ Install Python packages
3. ✅ Install Claude Desktop CLI
4. ✅ Authenticate with Claude

### Step 3: Test
```bash
python3 lang_intel.py --lang en --level B1
```

---

## Method 2: Manual Installation (Step by Step)

### Step 1: Install Homebrew

If you don't have Homebrew:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Verify:
```bash
brew --version
```

### Step 2: Install PortAudio

```bash
brew install portaudio
```

Verify:
```bash
brew list portaudio
```

### Step 3: Install Python Packages

**Option A: Using requirements.txt**
```bash
pip3 install -r requirements.txt --break-system-packages
```

**Option B: Manual installation**
```bash
pip3 install pyaudio --break-system-packages
pip3 install faster-whisper --break-system-packages
pip3 install numpy --break-system-packages
pip3 install pynput --break-system-packages
pip3 install edge-tts --break-system-packages
pip3 install requests --break-system-packages
```

**Why `--break-system-packages`?**
macOS Monterey+ has system-wide Python protection. This flag allows installation into the system Python (safe for development).

### Step 4: Install Node.js (if needed)

Check if you have Node.js:
```bash
node --version
npm --version
```

If not installed:
```bash
brew install node
```

### Step 5: Install Claude Desktop CLI

```bash
npm install -g @anthropic-ai/claude-cli
```

Verify:
```bash
which claude
claude --version
```

### Step 6: Authenticate with Claude

```bash
claude login
```

This will:
1. Open your browser
2. Ask you to sign in to claude.ai
3. Generate an API token
4. Save it locally

Verify:
```bash
claude whoami
```

### Step 7: Test Installation

```bash
# Test Whisper (first run will download model ~150MB)
python3 -c "from faster_whisper import WhisperModel; print('✓ Whisper OK')"

# Test Edge TTS
edge-tts --text "Hello world" --write-media test.mp3 && afplay test.mp3 && rm test.mp3

# Test PyAudio
python3 -c "import pyaudio; print('✓ PyAudio OK')"

# Test Claude CLI
claude --help
```

### Step 8: Run Language Tutor

```bash
python3 lang_intel.py --lang en --level B1
```

---

## Method 3: Using Virtual Environment (Cleanest)

For a cleaner installation that doesn't affect system Python:

### Step 1: Create Virtual Environment

```bash
cd ~/Projects  # or your preferred location
mkdir language-tutor
cd language-tutor

# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
# Install PortAudio system-wide first
brew install portaudio

# Install Python packages in venv (no --break-system-packages needed)
pip install -r requirements.txt
```

### Step 3: Install Claude CLI (still global)

```bash
npm install -g @anthropic-ai/claude-cli
claude login
```

### Step 4: Run

```bash
# Make sure venv is activated
source venv/bin/activate

python lang_intel.py --lang en --level B1
```

### Step 5: Deactivate When Done

```bash
deactivate
```

---

## Verification Checklist

After installation, verify everything works:

- [ ] PortAudio installed: `brew list portaudio`
- [ ] PyAudio working: `python3 -c "import pyaudio; print('OK')"`
- [ ] faster-whisper working: `python3 -c "from faster_whisper import WhisperModel; print('OK')"`
- [ ] Edge TTS working: `edge-tts --text "Test" --write-media t.mp3`
- [ ] Claude CLI installed: `which claude`
- [ ] Claude authenticated: `claude whoami`
- [ ] Node.js installed: `node --version`

---

## First Run: What to Expect

When you run for the first time:

```bash
python3 lang_intel.py --lang en --level B1
```

**You'll see:**

1. **Whisper model download** (150MB, happens once)
   ```
   Downloading model...
   [==========] 100%
   ```

2. **Component initialization**
   ```
   [1/4] Claude Desktop
     ✓ Claude CLI: /opt/homebrew/bin/claude
   
   [2/4] Whisper STT (Intel Mac - faster-whisper)
     Using 'base' model for 8GB RAM compatibility
     ✓ Whisper ready
   
   [3/4] Edge TTS
     ✓ Edge TTS ready
     Voice: en-US-MichelleNeural, Rate: +5%
   
   [4/4] Microphone
     ✓ Microphone ready
   ```

3. **Initial greeting**
   ```
   🇬🇧 Tutor: Hey Tuğrul! Okay so... what do you want to talk about today?
   
   [Cmd+Shift] hold to speak | [Cmd+Q] quit
   ```

4. **First interaction** (after you speak)
   - Whisper processes your voice (~2-3 sec)
   - Claude generates response (~3-5 sec)
   - TTS speaks the response (~1-2 sec)

**Total first interaction: 6-10 seconds is normal.**

---

## Optional: Ollama Installation

If you prefer fully local processing (no Claude API costs):

### Install Ollama

```bash
brew install ollama

# Start Ollama service
ollama serve &

# Pull model (2.5GB download)
ollama pull qwen2.5:7b
```

### Use with Language Tutor

```bash
python3 lang_intel.py --ollama --lang en --level B1
```

**Trade-offs:**
- ✅ Fully local (no internet needed)
- ✅ Free (no API costs)
- ✅ Privacy (nothing leaves your Mac)
- ❌ Slower responses (3-8 seconds vs 1-3 with Claude)
- ❌ Lower quality (Qwen 7B < Claude Sonnet)
- ❌ Higher RAM usage (~6-8GB vs 3-4GB)

---

## Uninstallation

To completely remove Language Tutor:

```bash
# Remove Python packages
pip3 uninstall pyaudio faster-whisper numpy pynput edge-tts requests -y

# Remove Claude CLI
npm uninstall -g @anthropic-ai/claude-cli

# Remove PortAudio (optional, might be used by other apps)
brew uninstall portaudio

# Remove Ollama (if installed)
brew uninstall ollama

# Remove downloaded models
rm -rf ~/.cache/whisper
rm -rf ~/.ollama
```

---

## Next Steps

After installation:

1. **Read the README** for usage examples
2. **Start with B1 level** - the tutor adapts to you
3. **Practice 15 minutes daily** - consistency beats length
4. **Review corrections** at the end of each session

Happy learning! 🎉