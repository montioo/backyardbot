#
# gpio.py
# backyardbot
#
# Created: June 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

"""
Defines a GPIO interface and gives two implementations for this interface
which can be used by the backyardbot to interact with the devices that
control the watering.
"""

from framework.utility import create_logger

try:
    import gpiozero
except:
    pass


class GpioInterface:
    """ Interface that defines interactions with GPIO ports. """

    def __init__(self, config, pins):
        """ Set pin to output pin and so on. """
        # config is only necessary to define the logger
        pass

    def set_state(self, pin, new_state):
        """ Change state of the pin. """
        pass

    def is_pin_active(self, pin):
        """ Return the state of the pin as bool. """
        pass


class DebugGpioInterface(GpioInterface):
    """
    Implements a GPIO interface dummy that can be used for testing
    on machines that don't have GPIO ports.
    """
    def __init__(self, config, pins):
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = create_logger(logger_name, config)
        self._states = {p: 0 for p in pins}
        self.logger.debug("Activated GPIO port {}".format(pins))

    def set_state(self, pin, new_state):
        if pin not in self._states.keys():
            self.logger.error("Can't change state of " + str(pin))
            raise EnvironmentError("Can't switch unknown GPIO port: {}".format(pin))

        if new_state not in [0, 1]:
            self.logger.error("Unknown new state {}".format(new_state))
            raise RuntimeError("Unknown GPIO state: {}".format(new_state))

        if self._states[pin] == int(new_state):
            self.logger.debug("Kept state {} on port {}".format(new_state, pin))
            return

        self._states[pin] = int(new_state)
        self.logger.debug("Set port {} to state {}".format(pin, new_state))

    def is_pin_active(self, pin):
        if pin not in self._states.keys():
            self.logger.error("Can't get state of " + str(pin))
            raise EnvironmentError("Don't know state of GPIO port: {}".format(pin))
        return bool(self._states[pin])


class RaspiGpioInterface(GpioInterface):
    """
    GPIO interface for a Raspberry Pi. This is basically just a bridge
    between the gpiozero library and the GpioInterface defined above.
    Can only control one GPIO pin at a time.
    """

    def __init__(self, config, pins):
        logger_name = __name__ + "." + self.__class__.__name__
        self.logger = create_logger(logger_name, config)
        self.pin = pins[0]
        self.sprinkler_gpio = gpiozero.LED(self.pin)
        self.pin_state = 0
        self.logger.debug("Activated port " + str(self.pin))

    def set_state(self, pin, new_state):
        if pin != self.pin:
            self.logger.error("Can't change state of " + str(pin))
            raise EnvironmentError("Can't switch unknown GPIO port: {}".format(pin))

        if new_state not in [0, 1]:
            self.logger.error("Unknown new state {}".format(new_state))
            raise RuntimeError("Unknown GPIO state: {}".format(new_state))

        if self.pin_state == int(new_state):
            self.logger.debug("Kept state {} on port {}".format(new_state, pin))
            return

        if new_state == 1:
            self.sprinkler_gpio.on()
        else:
            self.sprinkler_gpio.off()

        self.pin_state = new_state
        self.logger.debug("Set port {} to state {}".format(pin, new_state))

    def is_pin_active(self, pin):
        if pin != self.pin:
            self.logger.error("Can't get state of " + str(pin))
            raise EnvironmentError("Don't know state of GPIO port: {}".format(pin))
        return bool(self.pin_state)