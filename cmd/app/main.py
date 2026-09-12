import os
import sys
from pathlib import Path

path_root = Path(__file__).parents[2]
sys.path.append(str(path_root))

import logging
import time

from omegaconf import OmegaConf

from internal.clicker import Clicker

CONFIG_PATH = './config/config.yaml'


def load_dotenv(path: str = ".env") -> None:
    env_file = Path(path)
    if not env_file.is_file():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key, value)


if __name__ == '__main__':
    load_dotenv()

    logging.basicConfig(filename='./data/log/clicker_log.log',
                        level=logging.INFO,
                        filemode="w")

    # load config
    config = OmegaConf.load(CONFIG_PATH)

    # set logger
    logger = logging.getLogger(__name__)

    # create clicker
    clicker = Clicker(config)

    ratio_white_green_time = 0

    # run
    logger.info("run app")
    while True:
        work_time = clicker.work_time()

        if not work_time:
            clicker.sleep()

        if ratio_white_green_time == 0:
            clicker.start_up_ad(up="green")

        clicker.start_up_ad(up="white")
        ratio_white_green_time = (ratio_white_green_time + 1) % \
                                 config.clicker.ratio_white_green_time
        time.sleep(config.clicker.loop_time)
