from framework.app import App
from machine import Pin, ADC

class Microphone:
    """
    Capteur audio pur:
    - Lit l'ADC
    - Filtre une baseline (drift) MAIS la bloque quand le signal est fort
    - Calcule une enveloppe (intensité sonore) avec Attack/Release
    - Expose self.level (int) et self.raw
    - Optionnel: callback on_level(level, raw, baseline)
    """

    def __init__(
        self,
        pin=32,
        alpha_base=0.01,     # vitesse de baseline quand on est "calme"
        attack=0.35,         # montée de l'enveloppe
        release=0.80,        # descente de l'enveloppe (plus haut = plus rapide)
        gate_ratio=0.60,     # plus bas = baseline gelée plus facilement
        gate_offset=2.0,     # marge minimale (ADC units)
        on_level=None,
        debug=False
    ):
        self.adc = ADC(Pin(pin))
        self.adc.atten(ADC.ATTN_11DB)
        self.adc.width(ADC.WIDTH_12BIT)

        self.alpha_base = alpha_base
        self.attack = attack
        self.release = release

        # Gate baseline
        self.gate_ratio = gate_ratio
        self.gate_offset = gate_offset

        self.on_level = on_level
        self.debug = debug

        # États init
        self.raw = self.adc.read()
        self.baseline = float(self.raw)
        self.level = 0.0

        App().update.append(self.update)

    def update(self):
        x = self.adc.read()
        self.raw = x

        # amplitude AC (avec baseline actuelle)
        amp = abs(x - self.baseline)

        # Gate : on n'update la baseline que si amp est "petit"
        # (sinon, on évite qu'elle monte pendant un souffle long)
        gate = (self.level * self.gate_ratio) + self.gate_offset
        if amp < gate:
            self.baseline = (1 - self.alpha_base) * self.baseline + self.alpha_base * x

        # recompute amp après (possible) update baseline
        amp = abs(x - self.baseline)

        # Envelope Attack/Release
        a = self.attack if amp > self.level else self.release
        self.level = (1 - a) * self.level + a * amp

        if self.debug:
            print(
                f"Mic raw={self.raw} base={int(self.baseline)} "
                f"amp={int(amp)} level={int(self.level)} gate={int(gate)}"
            )

        if self.on_level:
            self.on_level(int(self.level), self.raw, int(self.baseline))

    def get_level(self) -> int:
        return int(self.level)