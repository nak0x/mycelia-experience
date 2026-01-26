from .animation import Animation

class LivingAnimation(Animation):
    """
    Etat "chaud mais a besoin d'eau" : chaud mais moins intense.
    """

    def __init__(self, shroom):
        super().__init__(shroom)
        self.color = (180, 80, 10)  # ambré, moins agressif que Lighting

    def on_enter(self):
        super().on_enter()
        self.shroom.display_color(self.color)

    def to_dead(self):
        from .dead_animation import DeadAnimation
        self.shroom.update_animation(DeadAnimation(self.shroom))