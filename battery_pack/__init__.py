"""BatteryPack: Electro-thermal N-cell pack modeling, analysis, and visualization."""

__all__ = [
    "__version__",
    "UPSBackupSystem",
    "UPSRequirements",
    "BackupPowerAnalysis",
    "design_ups_system",
]

__version__ = "0.1.0"

# Import UPS/backup power features
from .ups_backup import (
    UPSBackupSystem,
    UPSRequirements,
    BackupPowerAnalysis,
    design_ups_system,
)
