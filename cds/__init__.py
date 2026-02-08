import warnings

# Silence PendingDeprecationWarning emitted by the 'cloudflare' library
# during client initialization; we pin <2.20 but some releases still warn.
warnings.filterwarnings('ignore', category=PendingDeprecationWarning)

from .cds import cf
