#!/bin/bash
# TRM実験: 3モード比較（Baseline / Outer / Layer）

PROMPT_FILE="prompts/experiment.txt"
LOG_DIR="logs/comparison"
mkdir -p "$LOG_DIR"

echo "================================"
echo "TRM Experiment: 3-Mode Comparison"
echo "================================"
echo ""
echo "Prompt:"
cat "trm_exp/$PROMPT_FILE"
echo ""
echo "================================"

# モードA: Baseline (no recursion)
echo ""
echo "[Mode A] Baseline - No Recursion"
echo "--------------------------------"
python3 -c "
from mlx_lm import load, generate
model, tokenizer = load('TinyLlama/TinyLlama-1.1B-Chat-v1.0')
with open('trm_exp/$PROMPT_FILE', 'r') as f:
    prompt = f.read()
result = generate(model, tokenizer, prompt, max_tokens=150, temperature=0.9, top_p=0.95)
print('[Baseline Output]')
print(result)
print()
with open('$LOG_DIR/baseline.txt', 'w') as f:
    f.write(result)
"

# モードB: Outer (external loop recursion)
echo ""
echo "[Mode B] Outer - External Loop Recursion"
echo "----------------------------------------"
cd trm_exp && python3 -m trm_exp.recurse_outer --prompt-file "$PROMPT_FILE" > "../$LOG_DIR/outer_log.txt" 2>&1
tail -20 "$LOG_DIR/outer_log.txt"

# モードC: Layer (internal layer recursion)
echo ""
echo "[Mode C] Layer - Internal Layer Recursion"
echo "-----------------------------------------"
cd trm_exp && python3 -m trm_exp.recurse_layer --prompt-file "$PROMPT_FILE" > "../$LOG_DIR/layer_log.txt" 2>&1
tail -20 "$LOG_DIR/layer_log.txt"

echo ""
echo "================================"
echo "Experiment Complete!"
echo "Results saved to: $LOG_DIR/"
echo "================================"
