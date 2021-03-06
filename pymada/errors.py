import pymada


class PymadaException(Exception):
    """Basic exception to add logging etc."""

    def __init__(self, message):
        self.message = message
        pymada.logger.error(message)
        super().__init__(self.message)


class DiceException(PymadaException):
    """Except raised for errors with Dice"""


class PositionException(PymadaException):
    """Except raised for errors in Piece"""


class PieceException(PymadaException):
    """Except raised for errors in Piece"""

    PIECE_TYPE = "Piece"

    def __init__(self, piece_instance, message):
        """Include extra name information for identifying offending instance"""

        self.message = "".join(
            (f"Error with {self.PIECE_TYPE} named '{piece_instance.name}'\n", message)
        )
        super().__init__(self.message)


class PlayerPieceException(PieceException):
    """Except raised for errors in PlayerPiece"""

    PIECE_TYPE = "PlayerPiece"


class ShipException(PlayerPieceException):
    """Except raised for errors in Ship"""

    PIECE_TYPE = "Ship"


class ShipSpeedError(ShipException):
    """Except raised for errors with Ship speed"""


class ShipYawError(ShipException):
    """Except raised for errors with Ship yaw"""


class ShipHullZoneError(ShipException):
    """Except raised for errors with Ship HullZones"""


class HullZoneError(PymadaException):
    """Except raised by HullZone"""

    def __init__(self, hull_zone_instance, message):
        """Include instance information"""

        self.message = message
        super().__init__(self.message)


class NoLoS(HullZoneError):
    """Except raised when no line of sight between HullZones"""


class NotInRange(HullZoneError):
    """Except raised when HullZone not in range"""


class PlotError(PymadaException):
    """Except raised when plotting"""
