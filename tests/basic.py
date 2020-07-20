import pytest
import os, sys  # explicitly modify path to avoid having to constantly run setup.py to test code

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pymada
import pymada.errors
import pymada.data.ship_data
import pymada.classes.ship
from pymada.classes.base import Base
from pymada.classes.piece import Piece
from pymada.classes.player_piece import PlayerPiece
from pymada.classes.position import Position
from pymada.classes.dice import Dice


# ship_data tests


def test_ship_data():
    """
    """

    assert pymada.data.ship_data.ships["test_ship"]["armament"]["front"] == 1 * "red"


# Ship tests


def test_Ship():
    """
    """

    test_ship = pymada.classes.ship.Ship(
        model="test_ship", name="a ship for testing", faction="neutral", upgrades=None
    )
    assert test_ship._data["armament"]["front"] == 1 * "red"


# Piece tests


def test_piece_position():
    """Check setting a piece's position incorrectly raises TypeError
    """

    test_piece = Piece()
    test_piece.position = Position(x=5.0, y=5.0, theta=0.0)

    with pytest.raises(TypeError):
        test_piece.position = 5.0


def test_piece_base():
    """Check setting a piece's base incorrectly raises TypeError
    """

    test_piece = Piece()
    test_piece.base = Base()

    with pytest.raises(TypeError):
        test_piece.base = 5.0


# Dice tests


def test_dice_add():
    """Check adding two Die yields a Dice instance with correct number of Die
    """

    dice_1 = Dice("red")
    dice_2 = Dice(4 * "blue")

    assert isinstance(dice_1 + dice_2, Dice)
    assert (dice_1 + dice_2)["red"] == 1
    assert (dice_1 + dice_2)["blue"] == 4


def test_dice_multiply():
    """Check multiplying a Die yields a Dice instance with correct number of Die
    """

    dice_1 = Dice(2 * "red")

    assert isinstance(dice_1 * 4, Dice)
    assert (dice_1 * 4)["red"] == 8


# PlayerPiece tests


def test_player_piece_read():
    """
    """

    test_player_piece = PlayerPiece(
        name="ship for testing", model="test_ship", faction="imperial"
    )

    assert test_player_piece.faction is "imperial"