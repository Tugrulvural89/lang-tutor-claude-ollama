# 🌍 Language Tutor - M1 MacBook Air Edition

AI-powered language learning assistant optimized for M1 MacBook Air (8GB RAM). Best of both worlds: Apple Silicon performance + memory efficiency.

## ✨ Why M1 Edition?

- 🚀 **MLX Whisper** - Apple Silicon hardware acceleration (3-5x faster than Intel)
- 💾 **Claude Desktop default** - Cloud AI = less RAM usage (~3GB vs 6GB with Ollama)
- ⚡ **Fast transcription** - M1's Neural Engine optimized
- 🎯 **8GB RAM optimized** - Smart model choices for memory efficiency

## 🎯 Features

- 🎙️ **Voice-based learning** - Press Cmd+Shift to speak, get instant feedback
- 🤖 **Claude Desktop powered** - Best-in-class AI responses
- 🗣️ **MLX Whisper** - Hardware-accelerated speech recognition
- 🔊 **Edge TTS** - Natural text-to-speech
- 📚 **Multi-level support** - A1 (beginner) to C2 (mastery)
- 💬 **Natural corrections** - Learn from mistakes conversationally
- 🇹🇷 **Turkish explanations** - Complex grammar in your native language
- 💾 **Memory efficient** - Optimized for 8GB RAM

## 🎯 Supported Languages

- 🇬🇧 **English** - American English
- 🇪🇸 **Spanish** - Latin American Spanish
- 🇹🇷 **Turkish** - Explanation language

## 📋 System Requirements

- **Mac**: M1/M2/M3 MacBook Air/Pro
- **RAM**: 8GB minimum
- **OS**: macOS 11.0+ (Big Sur or later)
- **Storage**: ~1.5GB for models
- **Internet**: Required for Claude Desktop

## 🚀 Quick Setup

### Option 1: Automated (Recommended)

```bash
chmod +x setup_m1.sh
./setup_m1.sh
```

### Option 2: Manual Installation

```bash
# 1. Install Python packages
pip3 install pyaudio mlx-whisper numpy pynput edge-tts requests --break-system-packages

# 2. Install Claude Desktop CLI
npm install -g @anthropic-ai/claude-cli
claude login

# 3. Test
python3 lang_m1.py --lang en --level B1
```

## 🎮 Usage

### Basic Usage

```bash
# Interactive setup - choose language and level
python3 lang_m1.py
```

### Quick Start Examples

```bash
# English - Intermediate (default Claude)
python3 lang_m1.py --lang en --level B1

# Spanish - Beginner
python3 lang_m1.py --lang es --level A2

# Slower speech for beginners
python3 lang_m1.py --lang es --level A1 --slow

# Use Ollama instead (more RAM, fully local)
python3 lang_m1.py --ollama --lang en --level B1
```

## ⌨️ Keyboard Controls

- **Cmd+Shift** (hold): Record voice
- **Cmd+Q**: Quit application

## 📊 Performance (M1 8GB)

| Component | Time | Notes |
|-----------|------|-------|
| MLX Whisper | 0.5-1s | Apple Silicon optimized |
| Claude API | 2-4s | Cloud processing |
| Edge TTS | 1-2s | Natural speech |
| **Total** | **3.5-7s** | Very responsive! |

### M1 vs Intel Comparison

| Metric | M1 (This) | Intel Mac | M4 Pro |
|--------|-----------|-----------|---------|
| Whisper | MLX (fast) | faster-whisper | MLX (fastest) |
| Speed | 0.5-1s | 2-3s | 0.3-0.5s |
| RAM Usage | 3-4GB | 3-4GB | 8-10GB |
| Total Latency | 3.5-7s | 6-10s | 2-5s |

## 💡 Memory Management Tips

### Why Claude Desktop for 8GB?

```
Ollama (local):  6-8GB RAM → May cause swapping on 8GB Macs
Claude Desktop:  3-4GB RAM → Comfortable on 8GB
```

### If You Want Fully Local (Ollama)

```bash
# Install Ollama
brew install ollama
ollama pull qwen2.5:7b

# Use it
python3 lang_m1.py --ollama

# Monitor memory
Activity Monitor → Memory tab → Watch "Memory Pressure"
```

**Recommendation:** Stick with Claude Desktop unless you really need offline mode.

## 🎓 Learning Levels (CEFR)

### A1 - Absolute Beginner
Simple words, short sentences, lots of Turkish explanations

### A2 - Elementary
Basic phrases, new words explained in Turkish

### B1 - Intermediate (Recommended Start)
Natural conversations, target language mostly, Turkish for complex grammar

### B2 - Upper Intermediate
Abstract topics, Turkish only when asked

### C1 - Advanced
Nuanced conversations, subtle corrections

### C2 - Mastery
Near-native level, idioms and cultural nuance

## 💡 Learning Tips

### Getting Started
1. **Start at B1** even if you feel A2 - the tutor adapts
2. **15 min daily** beats occasional long sessions
3. **Don't worry about perfection** - focus on communication

### Effective Practice
- Say **"Anlamadım"** when confused (gets Turkish explanation)
- Request specific practice: "Let's practice past tense"
- Review corrections in session summary
- Practice consistently, same time each day

### Common Mistakes to Avoid
- Don't interrupt the tutor mid-sentence
- Speak naturally, no need to over-enunciate
- If misunderstood, rephrase instead of repeating

## 🔧 Troubleshooting

### "Claude not found"

```bash
npm install -g @anthropic-ai/claude-cli
claude login
```

### MLX Whisper Issues

```bash
# Reinstall MLX Whisper
pip3 uninstall mlx-whisper
pip3 install mlx-whisper --upgrade --break-system-packages
```

### Out of Memory

```bash
# Close unnecessary apps
# Activity Monitor → Sort by Memory

# Use Claude (not Ollama)
python3 lang_m1.py  # Claude is default

# Reduce history (edit lang_m1.py)
memory = ConversationMemory(max_size=10)  # Was 20
```

### Audio Issues

```bash
# System Preferences → Security & Privacy → Microphone
# Enable Terminal/iTerm

# Test microphone
rec -r 16000 test.wav trim 0 3
```

## 🆚 When to Use What?

### Use Claude Desktop (Default)
- ✅ 8GB RAM Mac
- ✅ Best quality responses
- ✅ Lower memory usage
- ✅ Faster than local Ollama
- ❌ Requires internet
- ❌ API costs (minimal)

### Use Ollama (`--ollama`)
- ✅ Fully offline/local
- ✅ No API costs
- ✅ Complete privacy
- ❌ Higher RAM (6-8GB)
- ❌ Slower responses
- ❌ Lower quality

## 📝 Example Session

```bash
$ python3 lang_m1.py --lang en --level B1

🌍 LANGUAGE TUTOR — M1 Mac Air (8GB)
══════════════════════════════════════

[1/4] Claude Desktop (Recommended for M1 8GB)
  ✓ Claude CLI: /opt/homebrew/bin/claude

[2/4] Whisper STT (MLX - Apple Silicon)
  Using 'base' model for M1 8GB RAM
  ✓ Whisper ready

[3/4] Edge TTS
  ✓ Edge TTS ready

[4/4] Microphone
  ✓ Microphone ready

  ✓ Her şey hazır!
════════════════════════════════════════

  🇬🇧 Tutor: Hey! So what's been going on with you lately?

  [Cmd+Shift] hold to speak | [Cmd+Q] quit
════════════════════════════════════════

[You press Cmd+Shift and say: "I go to work yesterday"]

● REC
○ Processing...

🎧 Whisper (en): "I go to work yesterday" (0.8s)

────────────────────────────────────────
🎤 [14:32:15] You (🇬🇧): I go to work yesterday
────────────────────────────────────────

⚡ Response: 3.2s
🔊 Speaking...

  🇬🇧 Tutor: Almost! Bak burada "go" değil "went" demen lazım 
  çünkü "yesterday" diyorsun. "I went to work yesterday." 
  Türkçe'de de "gittim" dersin, "giderim" demezsin değil mi? 
  Hadi tekrar dene!

  [Cmd+Shift] speak | [Cmd+Q] quit
```

## 📦 Files

```
language-tutor-m1/
├── lang_m1.py              # Main program
├── requirements_m1.txt     # Python dependencies
├── setup_m1.sh            # Auto-installer
├── README_M1.md           # This file
└── TROUBLESHOOTING_M1.md  # Debug guide
```

## 🔐 Privacy

- **MLX Whisper**: Runs locally on your Mac
- **Claude Desktop**: Conversations sent to Anthropic API
- **Edge TTS**: Text sent to Microsoft edge services
- **No storage**: Conversation memory is session-only

## 🎨 Customization

### Faster Whisper (less accuracy)

Edit `lang_m1.py`:
```python
WHISPER_MODEL_MLX = "mlx-community/whisper-tiny"  # Was "base"
```

### Slower TTS for Beginners

```bash
python3 lang_m1.py --slow
```

Or edit `lang_m1.py`:
```python
profile["tts_rate"] = "-20%"
```

### More Conversation Memory

Edit `lang_m1.py`:
```python
memory = ConversationMemory(max_size=30)  # Was 20
```

## 📊 Session Summary

After each session:
```
═══════════════════════════════════════
  📊 Session Summary
═══════════════════════════════════════
  Duration: 18 min
  Messages: 14 exchanges
  Corrections: 3

  Common mistakes:
  - "I go" → "I went" (past tense)
  - "Since three years" → "For three years"
═══════════════════════════════════════
```

## 🤝 Contributing

Found a bug? Have a suggestion? Open an issue!

## 📄 License

Educational purposes. Respect API terms:
- Anthropic Claude API
- Microsoft Edge TTS

---

**Made for M1/M2/M3 Mac users** 🚀

Happy learning! 🎉