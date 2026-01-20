from .animation import Animation

class LightingAnimation(Animation):
    """
    Etat "chauffé" : couleur chaude vive.
    """

    def __init__(self, shroom):
        super().__init__(shroom)
        self.color = (255, 140, 30)  # chaud

    def on_enter(self):
        super().on_enter()
        self.shroom.display_color(self.color)

    def to_dead(self):
        from .dead_animation import DeadAnimation
        self.shroom.update_animation(DeadAnimation(self.shroom))

    def to_living(self):
        from .living_animation import LivingAnimation
        self.shroom.update_animation(LivingAnimation(self.shroom))