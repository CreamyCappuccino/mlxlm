#!/bin/bash
# install.sh: Setup script - Register the mlxlm command to the system

# Get the absolute path of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/mlxlm.py"

# Path where the symlink will be created (macOS assumed)
TARGET_LINK="/usr/local/bin/mlxlm"

echo "🔧 Installing MLX-LM CLI..."
echo "📍 Linking: $PYTHON_SCRIPT → $TARGET_LINK"

# Remove existing symlink if it exists
if [ -L "$TARGET_LINK" ]; then
    echo "⚠️  Removing existing symlink at $TARGET_LINK"
    sudo rm "$TARGET_LINK"
elif [ -f "$TARGET_LINK" ]; then
    echo "⚠️  $TARGET_LINK exists and is a file. Backing up..."
    sudo mv "$TARGET_LINK" "${TARGET_LINK}.bak"
fi

# Create the symlink
sudo ln -s "$PYTHON_SCRIPT" "$TARGET_LINK"

# Make the script executable (just in case)
chmod +x "$PYTHON_SCRIPT"

echo "✅ Installed! You can now run: mlxlm help"