# Assets Directory

This directory contains media assets used by the TikTok automation bot for video creation.

## 📁 Directory Structure

```
assets/
├── bg/          # Background images and videos
├── overlays/    # Overlay elements (particles, icons, effects)
└── README.md    # This file
```

## 🎨 Background Assets (`bg/`)

Background images and videos used as the base layer for TikTok videos.

### **Accepted Formats**
- **Images**: JPG, PNG
- **Videos**: MP4, MOV
- **Resolution**: 1080p or higher (1920×1080 minimum)
- **Aspect Ratio**: Any (will be cropped/scaled to 9:16 for TikTok)

### **Recommended Themes**
- 🖥️ **Tech/Computing**: Data centers, server rooms, computer setups
- 🎮 **Gaming**: Gaming setups, RGB lighting, gaming peripherals
- 🤖 **AI/Machine Learning**: Neural networks, code visualizations, futuristic themes
- ⚡ **Performance**: Speed lines, energy effects, dynamic visuals
- 💎 **Premium**: Luxury tech, high-end equipment, professional setups

### **Quality Guidelines**
- **Resolution**: 1080p minimum, 4K preferred
- **File Size**: <50MB per file
- **Duration** (videos): 10-30 seconds (will be looped)
- **Content**: Professional, brand-safe, no copyrighted material

## 🎭 Overlay Assets (`overlays/`)

Transparent overlay elements used to enhance videos with effects and animations.

### **Accepted Formats**
- **Images**: PNG with transparency
- **Videos**: MP4 with alpha channel (if supported)

### **Recommended Elements**
- ⚡ **Particles**: Energy bursts, sparks, glowing particles
- 🔥 **Effects**: Fire, smoke, lightning, glow effects
- 💎 **Icons**: Tech icons, GPU symbols, performance indicators
- ✨ **Decorative**: Borders, frames, accent elements
- 🎯 **Call-to-Action**: Arrows, highlights, emphasis elements

### **Technical Requirements**
- **Format**: PNG with alpha transparency
- **Resolution**: High quality, scalable (512×512 minimum)
- **File Size**: <10MB per file
- **Background**: Transparent (alpha channel)

## 📄 License Requirements

**All assets must be:**
- ✅ **CC0 (Public Domain)** - No rights reserved
- ✅ **Original Work** - Created by you with full rights
- ✅ **Royalty-Free** - Licensed for commercial use
- ❌ **No Copyrighted Material** - No stock photos, movie clips, etc.

### **License Documentation**
When contributing assets, please include:
1. **Source**: Where the asset came from
2. **License**: CC0, original work, or specific license
3. **Attribution**: If required by license
4. **Modifications**: Any changes made to original

## 🤝 Contributing Assets

We welcome community contributions! Here's how to contribute:

### **1. Prepare Your Assets**
- Ensure proper format and quality
- Verify license compatibility (CC0 preferred)
- Optimize file sizes
- Test with the video builder

### **2. Organize Files**
```
assets/
├── bg/
│   ├── tech-datacenter-01.jpg
│   ├── gaming-setup-rgb.mp4
│   └── ai-neural-network.png
└── overlays/
    ├── particle-burst-blue.png
    ├── lightning-effect.png
    └── tech-icons-set.png
```

### **3. Submit Contribution**
1. Fork the repository
2. Add your assets to appropriate directories
3. Update this README with asset descriptions
4. Create a pull request with:
   - Asset descriptions
   - License information
   - Usage examples

### **4. Asset Naming Convention**
Use descriptive, lowercase names with hyphens:
- `tech-datacenter-blue.jpg`
- `particle-burst-gold.png`
- `gaming-setup-rgb-loop.mp4`

## 🎬 Usage Examples

### **Background Videos**
```python
# Automatic selection by video builder
bg_files = [f for f in os.listdir('assets/bg') 
           if f.lower().endswith(('.jpg', '.png', '.mp4'))]
selected_bg = random.choice(bg_files)
```

### **Overlay Effects**
```python
# Particle effects for energy template
particle_overlays = [f for f in os.listdir('assets/overlays') 
                    if 'particle' in f.lower()]
```

## 🎨 Asset Packs

### **Starter Pack** (Included)
- Gradient backgrounds (tech themes)
- Basic particle effects
- Simple overlay elements

### **Community Packs** (Contributions Welcome)
- **Gaming Pack**: RGB setups, gaming peripherals, esports themes
- **AI Pack**: Neural networks, code visualizations, futuristic UI
- **Data Center Pack**: Server rooms, cable management, enterprise tech
- **Performance Pack**: Speed effects, benchmark visuals, optimization themes

## 🔧 Technical Notes

### **Video Processing**
- Backgrounds are automatically resized to 1080×1920
- Videos are looped to match target duration
- Images get subtle zoom effect (1% over duration)
- All assets go through LUT color grading

### **Performance Considerations**
- Large files increase processing time
- 4K videos may require more RAM
- Optimize assets for 1080p output
- Consider file size for VPS deployments

### **Fallback Behavior**
If no assets are found:
- System generates gradient backgrounds
- Uses built-in particle effects
- Creates simple overlay elements
- Videos still render successfully

## 📊 Asset Statistics

Track your asset usage:
```bash
# Count assets
find assets/ -type f | wc -l

# Check total size
du -sh assets/

# List by type
find assets/ -name "*.jpg" | wc -l  # JPG images
find assets/ -name "*.png" | wc -l  # PNG images  
find assets/ -name "*.mp4" | wc -l  # MP4 videos
```

## 🆘 Troubleshooting

### **Common Issues**
- **"No assets found"**: Check file permissions and formats
- **"Video won't load"**: Verify codec compatibility (H.264 recommended)
- **"Poor quality"**: Use higher resolution source materials
- **"Large file sizes"**: Compress videos, optimize images

### **Asset Validation**
```python
# Test asset loading
from utils import validate_video_file
result = validate_video_file('assets/bg/your-video.mp4')
print(result)
```

## 📞 Support

Need help with assets?
- 📖 Check the main [README.md](../README.md)
- 🐛 Report issues on [GitHub](https://github.com/Jabsama/BOTTIKTOK/issues)
- 💬 Join discussions for asset requests
- 📧 Contact for licensing questions

---

**Happy creating! 🎬✨**

*Help us build the best open-source asset library for TikTok automation!*
