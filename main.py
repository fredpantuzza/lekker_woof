import datetime
import logging

import config
from app import app

if __name__ == '__main__':
    logging.basicConfig(
        filename=f'{config.logging_directory}/{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}_lekker_woof.log',
        format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.DEBUG)
    app.run()
