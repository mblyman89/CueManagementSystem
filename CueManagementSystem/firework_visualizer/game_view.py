"""
Main Game View - Orchestrates the entire firework visualization
"""

import arcade
import config
from firework_visualizer.camera import Camera3D
from firework_visualizer.scene_renderer import SceneRenderer
from firework_visualizer.water_system import WaterSystem
from firework_visualizer.dock import WoodenDock
from firework_visualizer.sky_system import SkySystem
from firework_visualizer.background_elements import BackgroundElements
from firework_visualizer.rack_system import RackSystem
from firework_visualizer.particle_manager import ParticleManager


class FireworkGameView(arcade.View):
    """
    Main game view that manages the firework visualization
    """
    
    def __init__(self):
        """Initialize the game view"""
        super().__init__()
        
        # Core systems
        self.camera = Camera3D()
        self.renderer = SceneRenderer()
        
        # Performance tracking
        self.frame_count = 0
        self.fps_display_timer = 0
        self.current_fps = 0
        
        # === Phase 2: Environment Systems ===
        self.sky = SkySystem()
        self.water = WaterSystem(self.camera)
        self.dock = WoodenDock(self.camera)
        self.background = BackgroundElements(self.camera)
        
        # === Phase 3: Mortar Rack System ===
        self.rack_system = RackSystem()
        
        # === Phase 4: Particle System ===
        self.particle_manager = ParticleManager(self.camera)
        
        # === Phase 5: Launch System ===
        from launch_system import LaunchSystem
        self.launch_system = LaunchSystem(self.rack_system, self.particle_manager)
        
        # === Phase 9: Audio System ===
        from audio_system import AudioSystem
        self.audio_system = AudioSystem(config.CAMERA_POSITION)
        
        # === Phase 5: Launch System (with audio) ===
        self.launch_system.audio_system = self.audio_system
        
        # === Phase 6: Firework Types ===
        from firework_factory import FireworkFactory
        self.active_fireworks = []
        self.launch_system.set_burst_callback(self._on_shell_burst)
        
        print("=" * 60)
        print("Firework Visualizer - Phase 9 Complete")
        print("=" * 60)
        print(f"Window: {config.SCREEN_WIDTH}x{config.SCREEN_HEIGHT} @ {config.TARGET_FPS}fps")
        print(f"Camera Position: {config.CAMERA_POSITION}")
        print(f"Camera Rotation: {config.CAMERA_ROTATION}")
        print(f"\nEnvironment Systems:")
        print(f"  - Sky with {len(self.sky.stars)} stars")
        print(f"  - Water with {len(self.water.waves)} wave components")
        print(f"  - Wooden dock: {config.DOCK_WIDTH}x{config.DOCK_DEPTH}x{config.DOCK_HEIGHT} cm")
        print(f"  - Background with {len(self.background.trees)} trees")
        print(f"\nMortar Rack System:")
        print(f"  - {len(self.rack_system.racks)} racks in {config.RACK_ROWS}×{config.RACK_COLS} grid")
        print(f"  - {self.rack_system.get_total_tubes()} total tubes")
        print(f"  - {len(self.rack_system.get_available_tubes())} tubes ready to fire")
        bounds = self.rack_system.get_grid_bounds()
        if bounds:
            width = bounds['max_x'] - bounds['min_x']
            depth = bounds['max_y'] - bounds['min_y']
            print(f"  - Grid size: {width:.1f} × {depth:.1f} cm")
        print(f"\nParticle System:")
        print(f"  - Particle pool: {config.PARTICLE_POOL_SIZE} particles")
        print(f"  - Max active: {config.MAX_PARTICLES}")
        print(f"  - Physics: Gravity={config.GRAVITY} cm/s², Drag={config.AIR_DRAG}")
        print(f"\nLaunch System:")
        print(f"  - Launch velocity: {config.LAUNCH_VELOCITY} cm/s")
        print(f"  - Target altitude: {config.BURST_HEIGHT} cm ({config.BURST_HEIGHT/30.48:.0f} feet)")
        print(f"  - Shell mass: {config.SHELL_MASS}g")
        print(f"\nFirework Types:")
        from firework_factory import FireworkFactory
        types = FireworkFactory.get_available_types()
        variants = FireworkFactory.get_available_variants()
        print(f"  - {len(types)} base types available: {', '.join(types)}")
        print(f"  - {len(variants)} Excalibur variants available")
        print(f"\nVisual Effects:")
        import visual_effects_config as vfx
        print(f"  - Quality preset: {vfx.QUALITY_PRESET}")
        print(f"  - Bloom: {'Enabled' if vfx.BLOOM_ENABLED else 'Disabled'}")
        print(f"  - Water reflections: {'Enabled' if vfx.WATER_REFLECTIONS_ENABLED else 'Disabled'}")
        print(f"  - Atmospheric glow: {'Enabled' if vfx.ATMOSPHERIC_GLOW_ENABLED else 'Disabled'}")
        print(f"\nAudio System:")
        print(f"  - Status: {'Enabled' if self.audio_system.audio_enabled else 'Disabled'}")
        print(f"  - Master volume: {self.audio_system.master_volume:.1f}")
        print(f"  - Max distance: {self.audio_system.max_audio_distance/100:.0f}m")
        print("=" * 60)
        print("\nKEYBOARD CONTROLS:")
        print("  ESC     - Exit")
        print("  F       - Toggle FPS display")
        print("  P       - Toggle particle count")
        print("  D       - Toggle debug mode")
        print("  R       - Print rack system info")
        print("  T       - Print random tube info")
        print("  V       - Print all Excalibur variants")
        print("  E       - Print visual effects settings")
        print("  A       - Toggle audio on/off")
        print("  SPACE   - Launch random Excalibur variant")
        print("  L       - Launch 8 different variants")
        print("  1       - Launch Peony (classic sphere)")
        print("  2       - Launch Chrysanthemum (trailing)")
        print("  3       - Launch Brocade (gold crackling)")
        print("  4       - Launch Willow (drooping)")
        print("  5       - Launch Palm (rising trails)")
        print("  6       - Launch Dahlia (petals)")
        print("  7       - Launch Crackle (popping)")
        print("  8       - Launch MultiEffect (stages)")
        print("  S       - Print statistics")
        print("  C       - Clear all shells and particles")
        print("=" * 60)
    
    def on_show_view(self):
        """Called when this view is shown"""
        arcade.set_background_color(config.SKY_COLOR_BOTTOM)
    
    def on_update(self, delta_time: float):
        """
        Update game logic
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update FPS counter
        self.frame_count += 1
        self.fps_display_timer += delta_time
        
        if self.fps_display_timer >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.fps_display_timer = 0
        
        # === Phase 2: Update environment systems ===
        self.sky.update(delta_time)
        self.water.update(delta_time)
        
        # === Phase 4: Update particle system ===
        self.particle_manager.update(delta_time)
        
        # === Phase 5: Update launch system ===
        self.launch_system.update(delta_time)
        
        # === Phase 6: Update active fireworks ===
        for firework in self.active_fireworks:
            firework.update(delta_time)
            firework.spawn_particles(delta_time)
        
        # Remove completed fireworks
        self.active_fireworks = [f for f in self.active_fireworks if not f.is_complete]
    
    def on_draw(self):
        """Render the scene"""
        # Clear the screen
        self.clear()
        
        # Clear all rendering layers
        self.renderer.clear_all_layers()
        
        # === BACKGROUND LAYER ===
        # Phase 2: Enhanced sky system with stars and atmosphere
        self.sky.render(self.renderer)
        
        # Phase 2: Background elements (distant shore, trees)
        self.background.render(self.renderer)
        
        # === WATER LAYER ===
        # Phase 2: Animated water surface with waves
        self.water.render(self.renderer)
        
        # === ENVIRONMENT LAYER ===
        # Phase 2: Wooden dock with 3D perspective
        self.dock.render(self.renderer)
        
        # Phase 3: Mortar racks with tubes
        self.rack_system.render(self.camera, self.renderer)
        
        # === PARTICLES LAYER ===
        # Phase 4: Render particle system
        self.particle_manager.render(self.renderer)
        
        # === EFFECTS LAYER ===
        # Phase 5: Render launch flashes
        self._render_launch_flashes()
        
        # === UI LAYER ===
        if config.SHOW_FPS:
            self._draw_fps()
        
        if config.SHOW_PARTICLE_COUNT:
            self._draw_particle_count()
        
        # Render all layers
        self.renderer.render_all()
    
    def _draw_fps(self):
        """Draw FPS counter"""
        def draw():
            arcade.draw_text(
                f"FPS: {self.current_fps}",
                10, config.SCREEN_HEIGHT - 30,
                arcade.color.WHITE,
                14,
                bold=True
            )
        
        self.renderer.add_to_layer('ui', draw)
    
    def _draw_particle_count(self):
        """Draw particle count"""
        def draw():
            count = self.particle_manager.get_active_count()
            arcade.draw_text(
                f"Particles: {count}",
                10, config.SCREEN_HEIGHT - 55,
                arcade.color.WHITE,
                14,
                bold=True
            )
        
        self.renderer.add_to_layer('ui', draw)
    
    def _render_launch_flashes(self):
        """Render launch flash effects."""
        flashes = self.launch_system.get_active_flashes()
        
        for flash in flashes:
            render_data = flash.get_render_data()
            
            # Project 3D position to screen
            screen_pos = self.camera.project_to_screen(render_data['position'])
            if screen_pos is None:
                continue
            
            x, y = screen_pos
            radius = render_data['radius'] * 0.5  # Scale for screen space
            color = render_data['color']
            alpha = render_data['alpha']
            
            # Draw flash as a bright circle
            def draw_flash(x=x, y=y, radius=radius, color=color, alpha=alpha):
                arcade.draw_circle_filled(
                    x, y, radius,
                    (*color, alpha)
                )
                # Add outer glow
                arcade.draw_circle_filled(
                    x, y, radius * 1.5,
                    (*color, alpha // 2)
                )
            
            self.renderer.add_to_layer('effects', draw_flash)
    
    def _on_shell_burst(self, burst_data):
        """
        Callback when a shell bursts.
        Creates the appropriate firework effect.
        
        Args:
            burst_data: Dictionary with burst parameters
        """
        from firework_factory import FireworkFactory
        
        firework = FireworkFactory.create_firework(
            burst_data['shell_type'],
            burst_data['position'],
            burst_data['velocity'],
            burst_data['color'],
            self.particle_manager
        )
        
        self.active_fireworks.append(firework)
    
    def on_key_press(self, key, modifiers):
        """Handle key presses"""
        if key == arcade.key.ESCAPE:
            # Exit the application
            arcade.close_window()
        
        elif key == arcade.key.F:
            # Toggle FPS display
            config.SHOW_FPS = not config.SHOW_FPS
        
        elif key == arcade.key.P:
            # Toggle particle count display
            config.SHOW_PARTICLE_COUNT = not config.SHOW_PARTICLE_COUNT
        
        elif key == arcade.key.D:
            # Toggle debug mode
            config.DEBUG_MODE = not config.DEBUG_MODE
            print(f"Debug mode: {'ON' if config.DEBUG_MODE else 'OFF'}")
        
        elif key == arcade.key.R:
            # Print rack system info
            print("\n" + self.rack_system.get_rack_info())
        
        elif key == arcade.key.T:
            # Test: Print info about a random tube
            import random
            tube = random.choice(self.rack_system.get_available_tubes())
            if tube:
                print(f"\nRandom Tube Info:")
                print(f"  Tube ID: {tube.tube_id}")
                print(f"  Position: {tube.position}")
                print(f"  Angle: pitch={tube.angle_pitch:.1f}°, yaw={tube.angle_yaw:.1f}°")
                print(f"  Muzzle: {tube.get_muzzle_position()}")
                direction = tube.get_firing_direction()
                print(f"  Direction: ({direction[0]:.3f}, {direction[1]:.3f}, {direction[2]:.3f})")
        
        elif key == arcade.key.V:
            # Print all Excalibur variants
            from firework_factory import FireworkFactory
            FireworkFactory.print_available_variants()
        
        elif key == arcade.key.E:
            # Print visual effects settings
            import visual_effects_config as vfx
            vfx.print_current_settings()
        
        elif key == arcade.key.A:
            # Toggle audio
            status = self.audio_system.toggle_audio()
        
        elif key == arcade.key.SPACE:
            # Test: Launch a random Excalibur variant
            import random
            from firework_factory import FireworkFactory
            from excalibur_variants import get_random_variant
            variant = get_random_variant()
            print(f"\nLaunching {variant}...")
            self.launch_system.launch_random_shell(
                shell_type=variant,
                color=(255, 150, 50)  # Color will be overridden by variant
            )
        
        elif key == arcade.key.L:
            # Launch multiple Excalibur variants
            print("\nLaunching 8 different Excalibur variants...")
            from excalibur_variants import ALL_VARIANTS
            import random
            # Select 8 random variants
            selected = random.sample(ALL_VARIANTS, min(8, len(ALL_VARIANTS)))
            for variant in selected:
                self.launch_system.launch_random_shell(
                    shell_type=variant,
                    color=(255, 150, 50)  # Color overridden by variant
                )
        
        elif key == arcade.key.KEY_1:
            # Launch Peony
            print("\nLaunching Peony (classic sphere)...")
            self.launch_system.launch_random_shell("Peony", (255, 100, 50))
        
        elif key == arcade.key.KEY_2:
            # Launch Chrysanthemum
            print("\nLaunching Chrysanthemum (trailing)...")
            self.launch_system.launch_random_shell("Chrysanthemum", (100, 150, 255))
        
        elif key == arcade.key.KEY_3:
            # Launch Brocade
            print("\nLaunching Brocade (gold crackling)...")
            self.launch_system.launch_random_shell("Brocade", (255, 215, 0))
        
        elif key == arcade.key.KEY_4:
            # Launch Willow
            print("\nLaunching Willow (drooping)...")
            self.launch_system.launch_random_shell("Willow", (150, 255, 150))
        
        elif key == arcade.key.KEY_5:
            # Launch Palm
            print("\nLaunching Palm (rising trails)...")
            self.launch_system.launch_random_shell("Palm", (255, 200, 100))
        
        elif key == arcade.key.KEY_6:
            # Launch Dahlia
            print("\nLaunching Dahlia (petals)...")
            self.launch_system.launch_random_shell("Dahlia", (255, 100, 200))
        
        elif key == arcade.key.KEY_7:
            # Launch Crackle
            print("\nLaunching Crackle (popping)...")
            self.launch_system.launch_random_shell("Crackle", (255, 255, 255))
        
        elif key == arcade.key.KEY_8:
            # Launch MultiEffect
            print("\nLaunching MultiEffect (stages)...")
            self.launch_system.launch_random_shell("MultiEffect", (200, 100, 255))
        
        elif key == arcade.key.S:
            # Print particle, launch, firework, and audio statistics
            self.particle_manager.print_statistics()
            self.launch_system.print_stats()
            print(f"\n=== Firework Statistics ===")
            print(f"Active Fireworks: {len(self.active_fireworks)}")
            if self.active_fireworks:
                for i, fw in enumerate(self.active_fireworks[:5]):  # Show first 5
                    stats = fw.get_stats()
                    print(f"  {i+1}. {stats['type']}: age={stats['age']:.1f}s, particles={stats['particles_spawned']}")
            print("=" * 60)
            self.audio_system.print_stats()
        
        elif key == arcade.key.C:
            # Clear all particles, shells, and fireworks
            self.launch_system.clear_all()
            self.active_fireworks.clear()
            print("\nCleared all shells, fireworks, and particles")
            self.particle_manager.clear_all()
            print("All particles cleared")
        
        # TODO: Add firework launch keys (Phase 5)
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Handle mouse clicks"""
        # TODO: Add click-to-launch firework (Phase 5)
        pass