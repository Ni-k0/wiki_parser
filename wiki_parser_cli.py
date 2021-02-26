import argparse
import coloredlogs
from parser import WikipediaSeries

def get_arguments():
    parser = argparse.ArgumentParser(description='''A cli tool to search for TV shows on Wikipedia.''')
    parser.add_argument('--show-name',
                        '-n',
                        action='store',
                        dest='show_name',
                        help='The show name you are searching for',
                        required=True)
    args = parser.parse_args()
    return args

def setup_logging(level, config_file=None):
    """
    Sets up the logging.

    Needs the args to get the log level supplied

    Args:
        level: At which level do we log
        config_file: Configuration to use

    """
    # This will configure the logging, if the user has set a config file.
    # If there's no config file, logging will default to stdout.
    if config_file:
        # Get the config for the logger. Of course this needs exception
        # catching in case the file is not there and everything. Proper IO
        # handling is not shown here.
        try:
            with open(config_file) as conf_file:
                configuration = json.loads(conf_file.read())
                # Configure the logger
                logging.config.dictConfig(configuration)
        except ValueError:
            print(f'File "{config_file}" is not valid json, cannot continue.')
            raise SystemExit(1)
    else:
        coloredlogs.install(level=level.upper())

def main ():
    args = get_arguments()
    setup_logging('debug')
    if args.show_name:
        test = WikipediaSeries()
        results = test.search_by_name(args.show_name)
    #found = test.found(results)
    print(results)
    #print(test)


if __name__ == "__main__":
    main()