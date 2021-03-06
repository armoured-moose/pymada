"""Game and context
"""

import os, sys
import numpy as np
import itertools

import pymada
import pymada.errors
from pymada.classes.board import Board
from pymada.classes.decision import Decision
from pymada.classes.plotter import Plotter


class Game:
    """
    """

    MAX_TURNS = 6

    def __init__(
        self, players, fleets,
    ):
        """
        """

        self.turn = 0
        self.players = {}
        for player in players:
            self.players[player.name] = player
        self.player_turn = itertools.cycle(players)
        self.board = Board()
        self.fleets = fleets
        self.plotter = Plotter()
        self.winner = None

    @property
    def is_over(self):
        """
        """

        # XXX CHECK FOR VICTORY CONDITIONS HERE

        if self.turn >= self.MAX_TURNS:
            return True
        elif self.winner:
            return True
        else:
            return False

    @pymada.log(message="beginning game")
    def play(self):
        """
        """

        self.plotter.draw(self.board, clear=False)

        self.deploy()

        self.plotter.show()

        while not self.is_over:
            self.play_turn()

        return self.winner

    @pymada.log(message="deploying ships")
    def deploy(self):
        """
        """

        # XXX how to do squadrons?

        # XXX just deploy all ships at once for now
        ship_speed = 2  # XXX add player choices here in future

        # TODO exception handling for ships lying outside deployment zone
        for (player_name, player), fleet in zip(self.players.items(), self.fleets):
            for model, name, faction, upgrades in zip(
                fleet.models, fleet.names, fleet.factions, fleet.upgrades
            ):

                # XXX choose random position but pointing towards board centre
                x = (
                    np.random.random()
                    * self.board.zones["deployment"].width
                    * (np.random.random() - 0.5)
                )
                y = (
                    np.random.random()
                    * self.board.zones["deployment"].height
                    * (np.random.random() - 0.5)
                )
                theta = np.asarray(np.arctan2(y, x)) * 180.0 / np.pi + 180

                self.board.add_ship(
                    player_name=player_name,
                    model=model,
                    name=name,
                    faction=faction,
                    speed=ship_speed,
                    upgrades=upgrades,
                    x=x,
                    y=y,
                    theta=theta,
                )

            self.plotter.draw(self.board.ships[name])

    def play_turn(self):
        """
        """

        self.play_ship_phase()
        self.play_squadron_phase()
        self.play_status_phase()

        self.turn += 1

    @pymada.log(message="beginning ship phase")
    def play_ship_phase(self):
        """
        """

        finished_ship_phase = False
        finished_players = []

        while not finished_ship_phase:

            current_player = next(self.player_turn)

            # check player is not eliminated

            if current_player.is_eliminated:

                if current_player.name not in finished_players:
                    finished_players.append(current_player.name)

            # check player is not winner

            elif {current_player.name} == {player for player in self.players} - {
                player.name for player in self.players.values() if player.is_eliminated
            }:
                self.winner = current_player
                finished_ship_phase = True

            # play turn

            else:

                # check player has ships to activate

                if not all(
                    [
                        ship.has_activated
                        for ship_name, ship in self.board.ships.items()
                        if ship.faction == current_player.faction
                    ]
                ):

                    # determine player ships, friendlies and enemies

                    player_ships = {
                        ship_name
                        for ship_name, ship in self.board.ships.items()
                        if ship.player_name == current_player.name
                    }

                    allied_targets = {
                        ship_name
                        for ship_name, ship in self.board.ships.items()
                        if ship.faction == current_player.faction
                    }

                    enemy_targets = {ship for ship in self.board.ships} - allied_targets

                    # XXX add more information here to tell player what they are selecting

                    ship_to_activate_name = self.players[current_player.name].choose(
                        Decision("select_piece", options=player_ships)
                    )

                    self.board.ships[ship_to_activate_name].activate()

                    # TODO reveal command

                    # shoot
                    # XXX ADD CATCHING HERE IF CHOOSES A SHIP THEY CANNOT FIRE ON FOR EXAMPLE i.e. IF FIRE RAISES EXCEPTION
                    # XXX what if firing on squadron?

                    # XXX add more information here to tell player what they are selecting

                    target_options = []
                    attacking_hull_zone_options = []
                    for attacking_hull_zone in self.board.ships[
                        ship_to_activate_name
                    ].hull_zones:
                        for target in enemy_targets:
                            for defending_hull_zone in self.board.ships[
                                target
                            ].hull_zones:
                                if self.board.ships[ship_to_activate_name].can_fire(
                                    self.board.ships[target],
                                    attacking_hull_zone=attacking_hull_zone,
                                    defending_hull_zone=defending_hull_zone,
                                ):
                                    target_options.append(target)
                                    attacking_hull_zone_options.append(
                                        attacking_hull_zone
                                    )
                    target_options = set(target_options)
                    attacking_hull_zone_options = set(attacking_hull_zone_options)

                    target_piece = self.players[current_player.name].choose(
                        Decision("select_piece", options=set(target_options) | {None})
                    )

                    # if firing

                    if target_piece is not None:

                        attacking_hull_zone = self.players[current_player.name].choose(
                            Decision(
                                "select_hull_zone", options=attacking_hull_zone_options
                            )
                        )

                        defending_hull_zone = self.players[current_player.name].choose(
                            Decision(
                                "select_hull_zone",
                                options={
                                    defending_hull_zone
                                    for defending_hull_zone in self.board.ships[
                                        target_piece
                                    ].hull_zones.keys()
                                    if self.board.ships[ship_to_activate_name].can_fire(
                                        self.board.ships[target],
                                        attacking_hull_zone=attacking_hull_zone,
                                        defending_hull_zone=defending_hull_zone,
                                    )
                                },
                            )
                        )

                        self.board.ships[ship_to_activate_name].fire(
                            self.board.ships[target_piece],
                            attacking_hull_zone=attacking_hull_zone,
                            defending_hull_zone=defending_hull_zone,
                        )

                        if self.board.ships[target_piece].is_destroyed:

                            self.plotter.erase(self.board.ships[target_piece])

                            if all(
                                self.board.ships[ship].is_destroyed
                                for ship in enemy_targets
                                if self.board.ships[ship].player_name
                                == self.board.ships[target_piece].player_name
                            ):
                                self.players[
                                    self.board.ships[target_piece].player_name
                                ].is_eliminated = True

                                # check for win

                                if {current_player.name} == {
                                    player for player in self.players
                                } - {
                                    player.name
                                    for player in self.players.values()
                                    if player.is_eliminated
                                }:
                                    self.winner = current_player
                                    finished_ship_phase = True

                    # move

                    clicks_to_move = self.players[current_player.name].choose(
                        Decision(
                            "clicks_to_move",
                            options=self.board.ships[
                                ship_to_activate_name
                            ].move_options,
                        )
                    )
                    self.board.ships[ship_to_activate_name].move(clicks_to_move)

                    # plot ship

                    self.plotter.draw(self.board.ships[ship_to_activate_name])
                    self.plotter.show()

                # player out of ships to activate so add to finished_players

                elif current_player.name not in finished_players:

                    finished_players.append(current_player.name)

            # if all players finished then end ship phase

            if all(
                [
                    self.players[player].name in finished_players
                    for player in self.players
                ]
            ):
                finished_ship_phase = True

    @pymada.log(message="beginning squadron phase")
    def play_squadron_phase(self):
        """
        """

        pass

    @pymada.log(message="beginning status phase")
    def play_status_phase(self):
        """
        """

        for ship in self.board.ships:
            self.board.ships[ship].deactivate()
