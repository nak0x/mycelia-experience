from framework.app import App
from machine import Pin, ADC

class Microphone:
    """
    Capteur audio pur:
    - Lit l'ADC
    - Filtre une baseline (drift)
    - Calcule une enveloppe (intensité sonore)
    - Expose self.level (int) et self.raw
    - Optionnel: callback on_level(level, raw, baseline)

    Pas de détection (souffle, trigger, seuil, cooldown, etc.)
    """

    def __init__(
        self,
        pin=32,
        alpha_base=0.01,   # vitesse d'adaptation de la baseline
        alpha_env=0.2,     # lissage de l'enveloppe
        on_level=None,
        debug=False
    ):
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)

        self.alpha_base = alpha_base
        self.alpha_env = alpha_env

        self.on_level = on_level
        self.debug = debug

        # Etats
        self.raw = self.adc.read()
        self.baseline = float(self.raw)
        self.level = 0.0   # enveloppe lissée

        App().update.append(self.update)

    def update(self):
        x = self.adc.read()
        self.raw = x

        # baseline (drift lent)
        self.baseline = (1 - self.alpha_base) * self.baseline + self.alpha_base * x

        # intensité sonore (enveloppe)
        amp = abs(x - self.baseline)
        self.level = (1 - self.alpha_env) * self.level + self.alpha_env * amp

        if App().config.debug or self.debug:
            print(f"Mic raw={self.raw} base={int(self.baseline)} level={int(self.level)}")

        if self.on_level:
            self.on_level(int(self.level), self.raw, int(self.baseline))

    def get_level(self) -> int:
        return int(self.level)