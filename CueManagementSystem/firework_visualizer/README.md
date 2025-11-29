# 🎆 Firework Visualizer - Python Arcade

A realistic firework visualization system featuring a lake scene with wooden mortar racks and 24 unique Excalibur shell effects.

## 📋 Project Status

### ✅ Phase 1: Core Architecture (COMPLETE)
- Project structure established
- Main window and game loop (1920x1080 @ 60fps)
- 3D camera system with perspective projection
- Coordinate system (X=right, Y=forward, Z=up)
- Scene renderer with layering system

### 🚧 In Progress
- Phase 2: Environment Assets (Lake & Dock Scene)

## 🚀 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the visualizer
python main.py
```

## 🎮 Controls

- **ESC** - Exit application
- **F** - Toggle FPS display
- **P** - Toggle particle count display
- **D** - Toggle debug mode
- **R** - Print rack system info
- **T** - Print random tube info (test)
- **SPACE** - Spawn test particle burst
- **S** - Print particle statistics
- **C** - Clear all particles

## 📁 Project Structure

```
FireworkVisualizer/
├── main.py                 # Entry point
├── config.py              # All configuration settings
├── game_view.py           # Main game view
├── camera.py              # 3D camera system
├── scene_renderer.py      # Rendering system with layers
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🎯 Features (Planned)

- **Realistic Environment**
  - Animated water surface with reflections
  - Weathered wooden dock (1219cm × 244cm × 61cm)
  - Sky gradient with atmospheric lighting

- **20 Wooden Mortar Racks**
  - 50 tubes per rack (1000 tubes total)
  - Proper positioning and angles
  - Wood texture and grain detail

- **24 Excalibur Shell Variants**
  - 8 base firework types
  - Unique colors and effects
  - Realistic physics simulation

- **Advanced Visual Effects**
  - Bloom/glow effects
  - Water reflections
  - Particle trails
  - Atmospheric lighting

- **Full Audio System**
  - Launch sounds
  - Explosion effects
  - Distance-based audio delay

## 🔧 Configuration

All settings can be customized in `config.py`:
- Window dimensions
- Camera position and rotation
- Physics constants
- Visual effects
- Audio settings
- Shell specifications

## 📊 Technical Specifications

- **Resolution**: 1920x1080
- **Target FPS**: 60
- **Max Particles**: 50,000
- **Coordinate System**: UE5-compatible (X=right, Y=forward, Z=up)
- **Units**: Centimeters

## 🎆 Shell Types

24 Excalibur shells across 8 effect types:
- Peony (4 variants)
- Chrysanthemum (4 variants)
- Brocade (4 variants)
- Willow (3 variants)
- Palm (3 variants)
- Dahlia (3 variants)
- Crackle (2 variants)
- Multi-Effect (1 variant)

## 📝 Development Progress

See `todo.md` for detailed development roadmap and progress tracking.

## 🤝 Integration

Designed for seamless integration with Python CueManagementSystem:
```python
from firework_visualizer import FireworkDisplay

display = FireworkDisplay()
display.launch_shell(shell_id=1, rack=5, tube=23)
```

---

**Status**: Phase 1 Complete - Foundation established and ready for environment building.