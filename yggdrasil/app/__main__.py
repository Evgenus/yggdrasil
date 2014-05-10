if __name__ == '__main__' and __package__ is None:
    import sys, os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    import yggdrasil.app
    __package__ = str("yggdrasil.app")
    del sys, os

from metaconfig import Config

def parse_args():
    import argparse

    parser = argparse.ArgumentParser(description='Repository web application.')
    
    parser.add_argument('-c', '--config', 
        dest='config', help='path to config file (should be yaml)')

    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()

    config = Config()
    config.load(args.config)

    server = config.get_dependency("server")

    server['extra_files'] = [
        args.config,
        ]

    from werkzeug.serving import run_simple
    run_simple(**server)