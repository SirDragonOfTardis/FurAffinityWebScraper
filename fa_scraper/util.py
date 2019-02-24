import os
from fa_scraper import parse

import time

import json
import pickle

from dateutil.parser import parse

from fa_scraper.constant import *

import logging
logger = logging.getLogger('default')

def if_images_directory_exists():
    """
    Checks if ./images/ exists.

    Args:
        None

    Returns:
        A boolean indicates whether exists directory 'images' in current working
    directory.
    """
    if os.path.exists('images'):
        if os.path.isdir('images'):
            logger.debug('images directory exists.')
            return True
    return False

def create_images_directory():
    """
    Create ./images/ if not exists.

    Args:
        None

    Returns:
        False if there exists a FILE named 'images', which means cannot create a
    directory named 'images'.
        True if successfully create 'images' directory or there exists a directory
    named 'images'.
    """
    if not if_images_directory_exists():
        if os.path.isfile('images'):
            logger.fatal('exists file named "images".')
            return False
        os.mkdir('images')
        logger.info('directory "images" created.')
        return True
    return True

def if_sub_directory_exists(sub_directory):
    """
    Checks if sub-directory exists.

    Args:
        None

    Returns:
        A boolean indicates whether sub_directory exists in current working
    directory.
    """
    if os.path.exists(sub_directory):
        if os.path.isdir(sub_directory):
            logger.debug(sub_directory + ' directory exists.')
            return True
    return False

def create_sub_directory(sub_directory):
    """
    Create sub-directory if not exists.

    Args:
        None

    Returns:
        False if there exists a FILE named 'images/*', which means cannot create a
    directory named 'images/*'.
        True if successfully create 'images/*' directory or there exists a directory
    named 'images/*'.
    """
    sub_directory = "images/" + sub_directory
    if not if_sub_directory_exists(sub_directory):
        if os.path.isfile(sub_directory):
            logger.fatal('exists file named "images/' + sub_directory + '".')
            return False
        os.mkdir(sub_directory)
        logger.info('directory "images/'+sub_directory+'" created.')
        return True
    return True

def combine_filename(filename_new, filename_extension):
    # artwork_id here is a str
    if filename_extension:
        return filename_new + '.' + filename_extension
    else:
        return filename_new

def parse_datetime(date):
    return parse(date)

def get_current_time():
    # the format string can be recognized by sqlite
    return time.strftime("%Y-%m-%d %H:%M", time.localtime())

def convert_boolean(boolean):
    # convert boolean to int, used by sqlite
    return 1 if boolean else 0

def generate_url_from_id(artwork_id):
    # artwork_id here is an int
    return '/view/' + str(artwork_id)

def if_cache_exists():
    if os.path.exists('scraper.cache'):
        if os.path.isfile('scraper.cache'):
            logger.debug('scraper.cache exists.')
            return True
    return False

def get_cookies(cookies_file):
    # open files and deserialzed cookies as dictionary
    with open(cookies_file, 'r') as file:
        cookies = json.load(file)
    return cookies
