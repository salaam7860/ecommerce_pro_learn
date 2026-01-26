import logging



def setup_logger():
    #create Handler

    stream_handler = logging.StreamHandler() #logging.DEBUG


    # Formater 
    formater = logging.Formatter(fmt="{asctime} - {name} - {levelname} - {filename}:{funcName}:{lineno} - {message}", style="{")

    # Set Formater
    stream_handler.setFormatter(formater)

    # Logger Name
    logger = logging.getLogger("account")
    logger.setLevel(logging.DEBUG)

    # Clear previous handlers
    logger.handlers.clear()

    # Prevent double logging
    logger.propagate = False

    logger.addHandler(stream_handler)

    return logger


logger = setup_logger()

# Test
#logger.debug("Logger initialized successfully")


