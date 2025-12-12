import json

from src.utils.frames.frame import Frame

class FrameParser:

    def __init__(self, raw_frame):
        self.frame = self.load(raw_frame)
        self.validate()

    def load(self, raw_frame):
        try:
            return json.loads(raw_frame)
        except Exception as e:
            print(f"FrameParser: Cannot load frame. Reason: {e}")

    def validate(self):
        # TODO: Frame validation
        try:
            self.frame = Frame(
                metadata=self.frame["metadata"],
                payloads=self.frame["payloads"]
            )
        except Exception as e:
            print(f"FrameParser: Cannot validate frame. Reason: {e}")