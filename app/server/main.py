import logging
import sys

# Configure logging to match server.py
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for this module
logger = logging.getLogger(__name__)

def main():
    logger.info("Hello from server!")


if __name__ == "__main__":
    main()
