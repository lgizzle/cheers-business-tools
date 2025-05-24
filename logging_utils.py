import os
import logging

def setup_logging(log_file='logs/app.log', level=logging.INFO):
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=level,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
