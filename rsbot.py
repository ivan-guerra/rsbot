#!/usr/bin/env python3

"""Define a driver for running a RSbot script on the command line."""

import sys
import argparse
from random import uniform
from time import sleep, time
from vm import VirtualMachine


def run_script(config) -> None:
    """Execute the provided script on a virtual machine for a specified runtime.

    Args:
        config: Configuration object containing script and runtime information.
    """
    start_time = time()
    curr_time = start_time
    idle_time = start_time
    while (curr_time - start_time) < config.runtime:
        vm = VirtualMachine()
        vm.execute(config.script)

        if (curr_time - idle_time) > config.idle_period:
            idle_time_sec = uniform(config.idle_time[0] * 60,
                                    config.idle_time[1] * 60)
            sleep(idle_time_sec)
        idle_time = time()
        curr_time = time()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="run a runescape bot script",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("script", type=str,
                        help="path to rsbot script")
    parser.add_argument("--runtime", "-r", type=int, default=3600,
                        help="script runtime in seconds")
    parser.add_argument("--start-delay", "-d", type=int,
                        help="script start delay in seconds")
    parser.add_argument("--idle-period", "-p", type=float, default=900,
                        help="number of seconds until an idle wait is "
                        "started")
    parser.add_argument("--idle-time", "-i", nargs=2,
                        type=float, default=[2, 5],
                        help="defines a range in minutes from which an "
                        "idle time will be randomly chosen")
    args = parser.parse_args()

    try:
        if args.start_delay:
            sleep(args.start_delay)

        run_script(args)
    except KeyboardInterrupt:
        sys.exit(0)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}")
