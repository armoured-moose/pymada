"""
"""

import copy, itertools
import numpy as np

import pymada
import pymada.errors
import pymada.data.ships
import pymada.data.tools
from pymada.classes.base import Base
from pymada.classes.position import Position
from pymada.classes.player_piece import PlayerPiece
from pymada.classes.hull_zone import HullZone

# TODO add command_dial list via command value from lookup
# TODO add command token functionality e.g. if brace in Ship.command_tokens and brance is not 'exhausted':


class Ship(PlayerPiece):
    """Class describing a Ship
    """

    def __init__(
        self,
        model,
        name,
        faction,
        player_name=None,
        speed=0,
        upgrades=None,
        x=0.0,
        y=0.0,
        theta=0.0,
    ):
        """Constructor for Ship
        args:
            theta - [float, deg]
        """

        super().__init__(
            model=model,
            name=name,
            faction=faction,
            upgrades=upgrades,
            player_name=player_name,
        )

        self._data = pymada.data.ships.ships[model]  # attach basic data
        self.hull = self._data["hull"]
        self.damage_cards = []

        # XXX should be property - since speed cannot ever go over max([speed for speed in self._data["move"]])
        # TODO check here if speed is valid
        self.speed = speed  # XXX for a squadron this is move range

        self.position = Position(x=0.0, y=0.0, theta=0.0)

        # add base - make sure to swap x and y since ship starts facing East at theta = 0
        self.base = Base(
            outline_points_x=pymada.data.ships.bases[self._data["size"]]["outline"][
                "y"
            ],
            outline_points_y=pymada.data.ships.bases[self._data["size"]]["outline"][
                "x"
            ],
        )

        self.hull_zones = {}  # add hull-zones
        for zone in self._data["hull_zones"]:
            self.hull_zones[zone] = HullZone(
                armament=self._data["armament"][zone],
                shields=self._data["shields"][zone],
                LoS_dot=self._data["LoS_dots"][zone],
                arc_left=self._data["arc_left"][zone],
                arc_right=self._data["arc_right"][zone],
            )

            self.position.add_observer(
                # attach this hull_zone.move() method as observer of Ship position
                self.hull_zones[zone].move
            )
        self.position.add_observer(
            # add base as observer
            self.base.move
        )

        self.position.move(
            x=x,
            y=y,
            theta_rotate_last=theta,
            centre_x_rotate_last=x,
            centre_y_rotate_last=y,
        )

    @property
    def damage(self):
        """Ship damage defined by number of damage cards
        """
        return len(self.damage_cards)

    @property
    def is_destroyed(self):
        """
        """

        # XXX add logger here or ShipDestroyedEvent(exception) ?

        return True if self.damage >= self.hull else False

    @property
    def move_options(self):
        """
        """

        options = []
        move_options = []
        for sub_speed in range(self.speed):
            clicks = self._data["move"][self.speed][sub_speed]
            clicks = np.linspace(-clicks, clicks, 2 * clicks + 1, dtype=int)
            move_options.append(clicks)

        return list(itertools.product(*move_options))

    def create_attack_pool(self, attacking_hull_zone, *args, **kwargs):
        """Return deep copy of attacking Dice armament
        """

        # XXX this needs to be multiple dispatch for anti squad
        attack_pool = copy.deepcopy(self.hull_zones[attacking_hull_zone].armament)

        # XXX do attacking dice mods here

        return attack_pool

    def suffer(self, attack, defending_hull_zone, *args, **kwargs):
        """

        args:
            attack - [Dice] 
            defending_hull_zone - 
        """

        damage = attack.damage_normal + attack.damage_critical

        damage_remaining = damage - self.hull_zones[defending_hull_zone].shields
        self.hull_zones[defending_hull_zone].shields -= damage
        if self.hull_zones[defending_hull_zone].shields < 0:
            self.hull_zones[defending_hull_zone].shields = 0
            for card in range(int(damage_remaining)):
                self.damage_cards.append("card")

    def move(self, clicks):
        """Ship-specific implementation of move() method - translates list of clicks to cartesian transforms

        args:
        notes:
            ships in armada move THEN rotate
        XXX add ship rotations from corner - .base.corner below as centre_x_rotate_last,centre_y_rotate_last
        XXX TODO implement collision checks, move can just call itself recursively with decreasing speed until no overlap event - could raise events.ShipOverlap()?
        """

        # first test move is valid
        # XXX if changing speed
        # if self.speed not in self._data["move"]:
        #    raise pymada.errors.ShipSpeedError(
        #        self,
        #        f"requested speed={self.speed} not available - options = {[speed for speed in self._data['move']]}",
        #    )

        if not all(
            [
                np.abs(clicks[sub_speed]) <= self._data["move"][self.speed][sub_speed]
                for sub_speed in range(self.speed)
            ]
        ):

            # TODO this will need to regard command dial effects
            raise pymada.errors.ShipYawError(
                self,
                f"requested yaw too high in maneuver {[clicks[sub_speed] for sub_speed in range(self.speed)]} - maximum = {[self._data['move'][self.speed][sub_speed] for sub_speed in range(self.speed)]}",
            )

        # allow clicks at higher speeds to be specified - if testing for collisions we just repeat but with speed-=1
        assert len(clicks) >= self.speed

        # loop over sub_moves
        for click_values, sub_move_dist, click_options in zip(
            clicks,
            pymada.data.tools.maneuver["distance"][self.speed],
            pymada.data.tools.maneuver["yaw"][self.speed],
        ):

            # calculate total theta change for this sub_move
            rotation_theta = 0.0
            rotation_dir = (
                click_values if click_values == 0 else click_values / abs(click_values)
            )
            for click_value in range(abs(click_values)):
                # -1. factor since +ve click means turn clockwise (opposite to global +ve theta)
                rotation_theta += click_options[click_value] * rotation_dir * -1.0

            # split move into two since we want to rotate about point we do not yet know the location of
            # first translate forward at current heading theta
            self.position.move(
                r=sub_move_dist, theta_translate=self.position.theta,
            )
            # then rotate to new theta about ship position - this same method will be passed to all observers
            self.position.move(
                theta_rotate_last=rotation_theta,
                # XXX these should be some corner of the Base
                centre_x_rotate_last=self.position.x,
                centre_y_rotate_last=self.position.y,
            )

    def LoS_to(self, defender, attacking_hull_zone, *args, **kwargs):
        """
        """

        # XXX this will need to check the enemy base is within our arc and check we are not obstructed
        """
        attacking_hull_zone = kwargs.get("attacking_hull_zone", None)

        if not attacking_hull_zone in self.hull_zones:
            raise ShipHullZoneError(
                self, f"'{attacking_hull_zone}' hull zone not found in {self.name}"
            )
            return False

        for point in defender.base.outline: #XXX only 100% accurate for base outlines fully-described by finite list of points e.g. square
            point.x
            point.y
        x1=self.hull_zones[attacking_hull_zone].LoS_dot_x
        y1=self.hull_zones[attacking_hull_zone].LoS_dot_y


        if LOGIC and enemy.LoS_from(self, *args, **kwargs):
            return True

        else:
            raise pymada.errors.NoLoS(
                self.hull_zones[attacking_hull_zone],
                f"'{attacking_hull_zone}' hull zone of {self.name} is not in range '{defending_hull_zone}' hull zone of {defender.name}",
            )

            return False
        """
        return True

    def LoS_from(self, attacker, defending_hull_zone, *args, **kwargs):
        """
        """

        # XXX attacker must have specified defending_hull_zone since they are attacking us, a ship

        # XXX check enemy LoS does not overlap our hull zone

        """
        if defending_hull_zone:
            if not defending_hull_zone in defender.hull_zones:
                raise ShipHullZoneError(
                    self,
                    f"'{defending_hull_zone}' hull zone not found in {defender.name}",
                )
                return False

        #XXX for squadron this function will just return true, since LoS disregards ship's base

        #XXX at this point we will need to check line from enemy does not cross our hullzone lines 
        if LOGIC
        """

        return True

    def range_to(self, defender, attacking_hull_zone, *args, **kwargs):
        """
        XXX this currently just returns distance between base centres - in future:
            range_from will need to do most of the work by taking attacking_hull_zone and attacker's base and comparing with defender's

        XXX so something like:
            return defender.range_from(self.base,attacking_hull_zone,*args,**kwargs)
        """
        
        distance=defender.base.centre-self.base.centre
        r=np.sqrt(distance.x**2+distance.y**2)
        for colour in ["black","blue","red"]:
            if r<=pymada.data.tools.rulers["range"][colour]:
                return colour
        return False 

    def range_from(self, attacker, attacking_hull_zone, defending_hull_zone, *args, **kwargs):
        """

        XXX calculate range in this function and pass upwards, something like:

            attacker_base=kwargs.get("base",None)
            then find line joining closest point on our base and attacker base
            then return the range IN THIS FUNCTION - which is just passed upwards in range_to
        """

        return True
