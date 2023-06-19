import enum

bootstrappers = ['ci', 'ci-static', 'ignition', 'none']


class BootstrapKind(enum.Enum):
    CI = 'ci'
    CI_STATIC = 'ci-static'
    IGNITION = 'ignition'
    NONE = 'none'
