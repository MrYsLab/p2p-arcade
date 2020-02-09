"""
 Based on the example included with arcade: Sprite Collect Moving and Bouncing Coins
 https://github.com/pvcraven/arcade/blob/master/arcade/examples/sprite_collect_coins_move_bouncing.py

 This program demonstrates using arcade in a peer to peer configuration, across
 2 computers. It takes advantage of python-banyan to provide distributed computing support.
 https://github.com/MrYsLab/python_banyan

 Copyright (c) 2020 Alan Yorinks All right reserved.

 Python Banyan is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA



Artwork from http://kenney.nl

"""
import arcade
import argparse
import psutil
from python_banyan.banyan_base import BanyanBase
import random
import signal
import sys
import subprocess
import threading

# --- Constants ---
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_COIN = 0.2
COIN_COUNT = 50

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Arcade P2P Example Player"


class Coin(arcade.Sprite):
    """
    Coin sprite definition
    """

    def __init__(self, filename, sprite_scaling):
        super().__init__(filename, sprite_scaling)

        self.change_x = 0
        self.change_y = 0

        # Assign an index number to each coin
        # so that we can track coins across game instances.
        self.my_index = None

    def update(self):
        """
        Updates will be controlled in the second thread
        using python-banyan.
        """
        return


# noinspection PyMethodMayBeStatic
class MyGame(arcade.Window, threading.Thread, BanyanBase):
    """
    This class creates a gaming instance to support p2p
    gaming with Arcade.

    The game has 2 "players". Player 0 are the coins and
    player 1 is the female person sprite.

    To run the game, first make sure the backplane is running.
    Next start an instance of the game with no command line parameters.
    Finally start the second instance of the game with the -p 1 command
    line option.

    If you are running the game across multiple computers, add the -b option
    with the IP address of the backplane to the second instance.
    """

    def __init__(self, back_plane_ip_address=None,
                 process_name=None, player=0):
        """

        :param back_plane_ip_address: specify if running across multiple computers
        :param process_name: the name in the banyan header for this process
        :param player: 0=coins 1=female sprite
        """
        # Call the parent class initializer
        title = SCREEN_TITLE + str(player)
        arcade.Window.__init__(self, SCREEN_WIDTH, SCREEN_HEIGHT, title)

        # Variables that will hold sprite lists
        self.all_sprites_list = None
        self.coin_list = None

        # Set up the player info
        self.player_sprite = None

        # save the player for this instance
        self.player = player

        # set score to zero
        self.score = 0

        # Don't show the mouse cursor
        self.set_mouse_visible(False)

        # initially turn collision detection off.
        # pressing the right mouse button will enable it.
        self.run_collision_detection = False

        # initialize the threading.Thread parent
        threading.Thread.__init__(self)

        # create a threading lock
        self.the_lock = threading.Lock()

        # set this thread as a daemon thread
        self.daemon = True

        # create a threading event that will allow the start
        # and stopping of thread processing
        self.run_the_thread = threading.Event()

        # initially allow the thread to run
        self.run_the_thread = True

        # if not backplane address is specified, try to start
        # the backplane. If an address is specified, the user
        # is trying to connect to an already running backplane
        if not back_plane_ip_address:
            self.start_backplane()

        # initialize the python-banyan base class parent
        BanyanBase.__init__(self, back_plane_ip_address=back_plane_ip_address,
                            process_name=process_name, loop_time=.00001)

        # add banyan subscription topics
        self.set_subscriber_topic('update_coins')
        self.set_subscriber_topic('p1_move')
        self.set_subscriber_topic('bump_score')
        self.set_subscriber_topic('remove_coin')

        arcade.set_background_color(arcade.color.AMAZON)

        # flag to start coin movement - change flag state
        # by pressing the left mouse button
        self.go = False

        # initialize some things
        self.setup()

        # start the second thread
        self.start()

        # start the arcade loop
        try:
            arcade.run()
        except KeyboardInterrupt:
            # stop the thread from further processing
            self.stop_event = False
            # we are outta here!
            sys.exit(0)

    # noinspection DuplicatedCode
    def setup(self):
        """
        Initialize the game
        """
        # Sprite lists
        self.all_sprites_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()

        # Set up the player 1
        # Character image from kenney.nl
        self.player_sprite = arcade.Sprite(":resources:images/animated_characters/female_person/femalePerson_idle.png",
                                           SPRITE_SCALING_PLAYER)
        self.player_sprite.center_x = 50
        self.player_sprite.center_y = 50
        self.all_sprites_list.append(self.player_sprite)

        # Create the coins which constitute player 2
        for i in range(50):
            # Create the coin instance
            # Coin image from kenney.nl
            coin = Coin(":resources:images/items/coinGold.png", SPRITE_SCALING_COIN)

            # Position the coin
            coin.center_x = random.randrange(SCREEN_WIDTH)
            coin.center_y = random.randrange(SCREEN_HEIGHT)
            coin.change_x = random.randrange(-3, 4)
            coin.change_y = random.randrange(-3, 4)
            coin.my_index = i

            # Add the coin to the lists
            self.all_sprites_list.append(coin)
            self.coin_list.append(coin)

    def on_draw(self):
        """ Draw everything """
        arcade.start_render()
        self.all_sprites_list.draw()

        # Put the text on the screen.
        # score is updated in the banyan received thread
        output = f"Score: {self.score}"
        arcade.draw_text(output, 10, 20, arcade.color.WHITE, 14)

    def on_mouse_motion(self, x, y, dx, dy):
        """
        Mouse motion detection and handling
        :param x: x position
        :param y: y position
        :param dx: change in x
        :param dy: change in y
        """
        # Move the center of the player sprite to match the mouse x, y
        # by publishing the position as a banyan message.
        if self.player == 1:
            payload = {'p1_x': x, 'p1_y': y}
            topic = 'p1_move'
            self.publish_payload(payload, topic)

    def on_mouse_press(self, x, y, button, modifiers):
        # start the coins in motion
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.go = True

        # start collision detection
        if button == arcade.MOUSE_BUTTON_RIGHT:
            self.run_collision_detection = True

    def on_update(self, delta_time):
        """
        Update the sprites.
        :param delta_time:
        """

        # Call update on all sprites (The sprites don't do much in this
        # example though.)
        self.all_sprites_list.update()

        if self.go:
            # build a list of all the coin positions using a list comprehension.
            # publish this list with the updated coin positions.
            with self.the_lock:
                coin_updates = [[self.coin_list.sprite_list[i].center_x,
                                 self.coin_list.sprite_list[i].center_y] for i in range(len(self.coin_list))]
                payload = {'updates': coin_updates}

                self.publish_payload(payload, 'update_coins')

    def start_backplane(self):
        """
        Start the backplane
        """

        # check to see if the backplane is already running
        try:
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if 'backplane' in proc.info['name']:
                    # its running - return its pid
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

        # backplane is not running, so start one
        if sys.platform.startswith('win32'):
            return subprocess.Popen(['backplane'],
                                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP |
                                    subprocess.CREATE_NO_WINDOW)
        else:
            return subprocess.Popen(['backplane'],
                                    stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                                    stdout=subprocess.PIPE)

    # Process banyan subscribed messages
    def run(self):
        """
        This is thread continually attempts to receive
        incoming Banyan messages. If a message is received,
        incoming_message_processing is called to handle
        the message.

        """
        # start the banyan loop - incoming messages will be processed
        # by incoming_message_processing in tghis thread.
        self.receive_loop()

    def incoming_message_processing(self, topic, payload):
        """
        Process the incoming Banyan messages

        :param topic: Message Topic string.

        :param payload: Message Data.
        """
        if self.external_message_processor:
            self.external_message_processor(topic, payload)
        else:
            # update the coins positions
            if topic == 'update_coins':
                # get the new coordinates
                the_coordinates = payload['updates']
                # update the coin positions with the new coordinates
                with self.the_lock:
                    for i in range(len(the_coordinates)):
                        try:
                            self.coin_list.sprite_list[i].center_x = the_coordinates[i][0] \
                                + self.coin_list.sprite_list[i].change_x
                            self.coin_list.sprite_list[i].center_y = the_coordinates[i][1] \
                                + self.coin_list.sprite_list[i].change_y

                            # If we are out-of-bounds, then 'bounce'
                            if self.coin_list.sprite_list[i].left < 0:
                                self.coin_list.sprite_list[i].change_x *= -1

                            if self.coin_list.sprite_list[i].right > SCREEN_WIDTH:
                                self.coin_list.sprite_list[i].change_x *= -1

                            if self.coin_list.sprite_list[i].bottom < 0:
                                self.coin_list.sprite_list[i].change_y *= -1

                            if self.coin_list.sprite_list[i].top > SCREEN_HEIGHT:
                                self.coin_list.sprite_list[i].change_y *= -1
                        # this should not happen, but if it does,
                        # just ignore and go along our merry way.

                        except (TypeError, IndexError):
                            continue

                # perform hit detection if enabled with the right mouse button.
                if self.run_collision_detection:
                    hit_list = arcade.check_for_collision_with_list(self.player_sprite,
                                                                    self.coin_list)
                    # hit detected
                    if hit_list:
                        for coin in hit_list:
                            # publish a remove_coin message using the coin
                            # index as the payload. The index is necessary
                            # so that we can remove coins for both players.
                            coin_index = coin.my_index
                            payload = {'coin': coin_index}
                            self.publish_payload(payload, 'remove_coin')

                            # bump up the score by publishing a bump_score
                            # message
                            payload = {'bump': 1}
                            self.publish_payload(payload, 'bump_score')
            # move player 2 on the screen
            elif topic == 'p1_move':
                self.player_sprite.center_x = payload['p1_x']
                self.player_sprite.center_y = payload['p1_y']
            # now actually remove the coin identified in hit detection
            # by using its index.
            elif topic == 'remove_coin':
                with self.the_lock:
                    coin_index = payload['coin']
                    for coin in self.coin_list.sprite_list:
                        if coin_index == coin.my_index:
                            coin.remove_from_sprite_lists()
            # bump the score variable.
            elif topic == 'bump_score':
                self.score += 1


def p2p_arcade():
    parser = argparse.ArgumentParser()
    # allow user to bypass the IP address auto-discovery.
    # This is necessary if the component resides on a computer
    # other than the computing running the backplane.
    parser.add_argument("-b", dest="back_plane_ip_address", default="None",
                        help="None or Common Backplane IP address")
    parser.add_argument("-n", dest="process_name", default="Arcade p2p",
                        help="Banyan Process Name Header Entry")
    parser.add_argument("-p", dest="player", default="0",
                        help="Select player 0 or 1")

    args = parser.parse_args()

    if args.back_plane_ip_address == 'None':
        args.back_plane_ip_address = None
    kw_options = {'back_plane_ip_address': args.back_plane_ip_address,
                  'process_name': args.process_name + ' player' + str(args.player),
                  'player': int(args.player)
                  }
    # instantiate MyGame and pass in the options
    MyGame(**kw_options)


# signal handler function called when Control-C occurs
# noinspection PyShadowingNames,PyUnusedLocal,PyUnusedLocal
def signal_handler(sig, frame):
    print('Exiting Through Signal Handler')
    raise KeyboardInterrupt


# listen for SIGINT
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == '__main__':
    p2p_arcade()
