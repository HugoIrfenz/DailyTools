# Color Contrast

Calculate the relative luminance contrast ratio for two opaque sRGB hex colors. Requires Python 3.9+ with no third-party packages.

```bash
python tools/color-contrast/color_contrast.py '#000' '#ffffff'
```

This prints `21.0000:1`. The tool accepts three or six hex digits with an optional leading hash. It does not model alpha blending, gradients, or rendered text.
