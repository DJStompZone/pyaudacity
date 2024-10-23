from enum import Enum

class AudacityOptionEnum(Enum):
    def __str__(self):
        return self.value


class ChirpWaveform(AudacityOptionEnum):
    SINE = "Sine"
    SQUARE = "Square"
    SAWTOOTH = "Sawtooth"
    SQUARE_NO_ALIAS = "Square, no alias"
    TRIANGLE = "Triangle"  # Note: This option doesn't appear in the scripting documentation but does in the UI.

class ChirpInterpolation(AudacityOptionEnum):
    LINEAR = "Linear"
    LOGARITHMIC = "Logarithmic"

class PitchType(AudacityOptionEnum):
    PITCHTEMPO = "PitchTempo"
    LQPITCHSHIFT = "LQPitchShift"

class DelayType(AudacityOptionEnum):
    REGULAR = "Regular"
    BOUNCINGBALL = "BouncingBall"
    REVERSEBOUNCINGBALL = "ReverseBouncingBall"

class NoiseType(AudacityOptionEnum):
    WHITE = "White"
    PINK = "Pink"
    BROWNIAN = "Brownian"

class ToneWaveform(AudacityOptionEnum):
    SINE = "Sine"
    SQUARE = "Square"
    SAWTOOTH = "Sawtooth"
    SQUARE_NO_ALIAS = "Square, no alias"
    TRIANGLE = "Triangle"  # Note: This option doesn't appear in the scripting documentation but does in the UI.

class PluckFade(AudacityOptionEnum):
    ABRUPT = "Abrupt"
    GRADUAL = "Gradual"

class NoiseType(AudacityOptionEnum):
    WHITE = "White"
    PINK = "Pink"
    BROWNIAN = "Brownian"

class RhythmTrackBeatSound(AudacityOptionEnum):
    METRONOME = "Metronome"
    PING_SHORT = "Ping (short)"
    PING_LONG = "Ping (long)"
    COWBELL = "Cowbell"
    RESONANT_NOISE = "ResonantNoise"
    NOISE_CLICK = "NoiseClick"
    DRIP_SHORT = "Drip (short)"
    DRIP_LONG = "Drip (long)"

class FadeType(AudacityOptionEnum):
    UP = "Up"
    DOWN = "Down"
    SCURVEUP = "SCurveUp"
    SCURVEDOWN = "SCurveDown"

class FadeUnits(AudacityOptionEnum):
    DB = "dB"
    PERCENT = "Percent"

class MeasurementScale(AudacityOptionEnum):
    DB = "dB"
    LINEAR = "Linear"

class IndexFormat(AudacityOptionEnum):
    NONE = "None"
    DECIMAL = "Decimal"
    HEX = "Hex"

class IncludeHeaderInformation(AudacityOptionEnum):
    NONE = "None"
    SHORT = "Short"
    FULL = "Full"

class ChannelLayoutForStereo(AudacityOptionEnum):
    LR_SAME_LINE = "L-R on Same Line"
    LR_DIFFERENT_LINES = "L-R on Different Lines"

class ShowMessages(AudacityOptionEnum):
    YES = "Yes"
    NO = "No"

class Rolloff(AudacityOptionEnum):
    DB6 = "dB6"
    DB12 = "dB12"
    DB24 = "dB24"
    DB36 = "dB36"
    DB48 = "dB48"

class LimiterType(AudacityOptionEnum):
    SOFTLIMIT = "SoftLimit"
    HARDLIMIT = "HardLimit"
    SOFTCLIP = "SoftClip"
    HARDCLIP = "HardClip"

class VRAIAction(AudacityOptionEnum):
    REMOVETOMONO = "RemoveToMono"
    REMOVE = "Remove"
    ISOLATE = "Isolate"
    ISOLATEINVERT = "IsolateInvert"
    REMOVECENTERTOMONO = "RemoveCenterToMono"
    REMOVECENTER = "RemoveCenter"
    ISOLATECENTER = "IsolateCenter"
    ISOLATECENTERINVERT = "IsolateCenterInvert"
    ANALYZE = "Analyze"

class YesNo(AudacityOptionEnum):
    YES = "Yes"
    NO = "No"