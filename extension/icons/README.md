# Extension Icons

This directory should contain the following icon files:

- `icon16.png` - 16x16 pixels (toolbar)
- `icon48.png` - 48x48 pixels (extension management)
- `icon128.png` - 128x128 pixels (Chrome Web Store)

## Generating Icons

You can create icons using any image editor or online tools. The icon should represent a workflow/process chart.

### Quick icon generation (using placeholder):

```bash
# Install ImageMagick if not already installed
# brew install imagemagick  # macOS
# apt-get install imagemagick  # Linux

# Create placeholder icons with different sizes
convert -size 16x16 xc:#667eea -fill white -pointsize 10 -gravity center -draw "text 0,0 'W'" icon16.png
convert -size 48x48 xc:#667eea -fill white -pointsize 30 -gravity center -draw "text 0,0 'W'" icon48.png
convert -size 128x128 xc:#667eea -fill white -pointsize 80 -gravity center -draw "text 0,0 'W'" icon128.png
```

### Recommended Design

- **Color scheme**: Purple gradient (#667eea to #764ba2) to match the app theme
- **Symbol**: A flowchart symbol, workflow diagram, or process icon
- **Style**: Modern, flat design

### Online Icon Generators

- https://www.favicon-generator.org/
- https://realfavicongenerator.net/
- https://www.canva.com/create/icons/
