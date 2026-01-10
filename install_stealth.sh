#!/bin/bash
# Install selenium-stealth for anti-detection

echo "Installing selenium-stealth..."
pip install selenium-stealth

echo ""
echo "✅ Installation complete!"
echo ""
echo "To verify installation, run:"
echo "python -c 'from selenium_stealth import stealth; print(\"✓ selenium-stealth installed successfully\")'"
