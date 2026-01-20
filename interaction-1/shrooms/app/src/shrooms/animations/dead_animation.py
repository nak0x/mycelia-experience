from .animation import Animation

class DeadAnimation(Animation):
    """
    Etat "froid" : une couleur bleutée très faible.
    """

    def __init__(self, shroom):
        super().__init__(shroom)
        self.color = (0, 6, 18)  # < 25, froid

    def on_enter(self):
        super().on_enter()
        # Allume juste les pixels du shroom
        self.shroom.display_color(self.color)

    def to_lighting(self):
        from .lighting_animation import LightingAnimation
        self.shroom.update_animation(LightingAnimation(self.shroom))