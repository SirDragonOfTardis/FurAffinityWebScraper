from bs4 import BeautifulSoup

import re
import unicodedata

from fa_scraper import util
from fa_scraper.constant import *

import logging
logger = logging.getLogger('default')

from functools import reduce

class Parser(object):
    """
    Parser class to initialize from a html and parse information from it

    Attributes:
        bs - BeautifulSoup object to parse tags/attributes easily from DOM tree
    """
    # compiled url regex table
    URL_REGEX_TABLE = {}

    @classmethod
    def generate_url_regex_table(cls):
        """
        Generate compiled regex table to match url quickly from given html.

        Args:
            cls - Parser class
        """
        url_regex_table = {}

        for url_type in URL_TYPES:
            url_regex_table[url_type] = re.compile('^(/' + url_type + '/)')

        # user's regex is not exactly same with others
        # /user/history is banned from robots.txt, so to be excluded
        url_regex_table['user'] = re.compile('^(/user/)(?!history/)')

        logger.debug('url regex table(stores compiled regexes for url '
                     'match) generated.')
        cls.URL_REGEX_TABLE = url_regex_table

    @staticmethod
    def get_url_type(url):
        # get url type of given url, simply implements with find
        for url_type in URL_TYPES:
            sub_url = '/' + url_type + '/'
            if url.find(sub_url) != -1:
                return url_type

        logger.warning('unknown url type from url: %s.' % url)
        return 'unknown'

    def __init__(self, html, url):
        # lazy load, trying to generate compiled regex table when the first
        # instance initialized.
        if not Parser.URL_REGEX_TABLE:
            Parser.generate_url_regex_table()

        # initialize bs object for parsing
        self.bs = BeautifulSoup(html, "html.parser")
        self.url = url
        
        self.resume_on_user = resume_on_user

        logger.debug('parser initialized.')

    def get_all_urls(self):
        """
        Get all matched urls from html.

        Args:
            self - instance of class Parser

        Returns:
            urls - a list of all matched urls
        """
        urls = []
        url_count = 0
        scrapemode = "newest2pg"

        # for url_type in URL_TYPES:
        #    # look up directly from regex table
        #    temp_urls = self.bs.findAll('a', href = Parser.URL_REGEX_TABLE[url_type])
        #    if temp_urls:
        #        # use map to get href attribute(url) from matched tag
        #        temp_urls = list(map(lambda tag: tag.get('href'), temp_urls))
        #        url_count = url_count + len(temp_urls)
        #        urls = urls + temp_urls

        gallery_user_folders = self.bs.findAll('ul', {"class": "default-group"})

        #adds user gallery and scraps from a watch list
        if '/watchlist/' in self.url:
            temp_users = self.bs.findAll('a')
            temp_users_list = list(map(lambda tag: tag.get('href'), temp_users))

            # starts list from specified user
            if not self.resume_on_user == '':
                user_to_check = '/user/' + self.resume_on_user.lower() + '/'
                if temp_users_list.index(user_to_check):
                    temp_resume = temp_users_list
                    temp_resume_index = temp_users_list.index(user_to_check)
                    r = 0
                    while r < temp_resume_index:
                        temp_resume.pop(0)
                        r = r+1
                    temp_users_list = temp_resume
                    url_count = url_count + (len(temp_users_list) - (temp_resume_index + 1)) * 2
                else:
                    logger.debug("The user specified was not found.")
            else:
                url_count = url_count + len(temp_users_list)*2


            # adds all main galleries and scraps
            temp_user_urls = []
            for i in range(len(temp_users_list)):
                temp_users_list[i] = temp_users_list[i].replace('/user/','')
                temp_user_urls.append("/gallery/%s" %(temp_users_list[i]))
                logger.debug("/gallery/%s added to urls" %(temp_users_list[i]))
                temp_user_urls.append("/scraps/%s" %(temp_users_list[i]))
                logger.debug("/scraps/%s added to urls" %(temp_users_list[i]))
            
            temp_user_urls.reverse()
            urls = temp_user_urls + urls

        # adds users gallery if start url is user page
        if '/user/' in self.url:
            temp_single_user_urls = []
            temp_single_user = self.url.replace('https://www.furaffinity.net/user/','')
            temp_single_user_urls.append('/scraps/'+temp_single_user)
            temp_single_user_urls.append('/gallery/'+temp_single_user)
            url_count = url_count + len(temp_single_user_urls)
            urls = temp_single_user_urls + urls
        # adds next page url
        new_submissions_nextpage = self.bs.findAll('a', {"class": "more"})
        if new_submissions_nextpage:
            nextpage_urls = []
            found_next = False
            for more in new_submissions_nextpage:
                if not 'prev' in more['class'] and found_next is False:
                    nextpage_urls.append(more['href'])
                    found_next = True
            url_count = url_count + len(nextpage_urls)
            urls = nextpage_urls + urls
        new_submissions_nextpagealt = self.bs.findAll('a', {"class": "more-half"}, limit=1)
        if new_submissions_nextpagealt:
            nextpagealt_urls = list(map(lambda tag: tag.get('href'), new_submissions_nextpagealt))
            url_count = url_count + len(nextpagealt_urls)
            urls = urls + nextpagealt_urls
        gallery_nextpagealt = self.bs.findAll('a', {"class": "button-link right"}, limit=1)
        if gallery_nextpagealt:
            gallery_nextpagealt_urls = list(map(lambda tag: tag.get('href'), gallery_nextpagealt))
            url_count = url_count + len(gallery_nextpagealt_urls)
            urls = urls + gallery_nextpagealt_urls

        # adds view urls
        if not '/user/' in self.url:
            temp_urls = self.bs.findAll('figure')
            if temp_urls:
                temp_urls = list(map(lambda tag: tag.get('id'), temp_urls))
                url_count = url_count + len(temp_urls)
                for i in range(len(temp_urls)):
                    temp_urls[i] = temp_urls[i].replace('sid-','')
                    temp_urls[i] = "/view/%s/" %(temp_urls[i])
                temp_urls.reverse()
                urls = urls + temp_urls

        logger.info("retrieved %u available urls." % url_count)

        return urls


class ArtworkParser(Parser):
    """
    ArtworkParser class inherit from Parser and parse information from a artwork
website.

    Attributes:
        bs - inherit from super class Parser
        stats_tag - status tag where most attributes are included
        cat_tag - cat tag where name and author attributes are included
        keywords_tag - keywords tag in status tag
        posted_tag - posted tag in status tag
    """
    ARTWORK_ATTRIBUTES = ['Category', 'Theme', 'Species', 'Gender', 'Favorites',
                          'Comments', 'Views', 'Resolution', 'Keywords', 'Author',
                          'Name', 'Adult'] # attributes used by regex table and tag table
    INT_ATTRIBUTES = set(['Views', 'Comments', 'Favorites'])
    # attributes needs to be convert to int

    REGEX_TABLE = {} # compiled regex table
    TAG_TABLE = {} # tag table

    FILENAME_EXTENSION_REGEX = re.compile('.*\.(.+)') # compiled regex to get file extension from download url

    @classmethod
    def generate_regex_table(cls):
        """
        Generate compiled regex table to extract attribute quickly from certain
        tag.

        Args:
            cls - ArtworkParser class
        """
        regex_table = {}

        for attribute in cls.ARTWORK_ATTRIBUTES:
            regex_table[attribute] = re.compile('<b>' + attribute + ':</b>\s*(.+?)\s*<br/>')

        # keywords author name uses different regexes
        regex_table.update({'Keywords'  : re.compile('<a href=".*">(.+?)</a>'),
                            'Author'    : re.compile('<a href=".*">(.+)</a>'),
                            'Name'      : re.compile('<b>(.+)</b>')})

        logger.debug('artwork parser\'s regex table(stores compiled regexes for '
                     'extract artwork attribute) generated.')
        cls.REGEX_TABLE = regex_table

    @classmethod
    def generate_tag_table(cls):
        """
        Generate tag table to map attribute to tag(property of ArtworkParser).

        Args:
            cls -ArtworkParser class
        """
        tag_table = {}

        for attribute in cls.ARTWORK_ATTRIBUTES:
            tag_table[attribute] = 'stats_tag'

        # keywords author name uses different tags
        tag_table.update({'Name'        : 'cat_tag',
                          'Author'      : 'cat_tag',
                          'Keywords'    : 'keywords_tag'})

        logger.debug('artwork parser\'s tag table(stores tag name each attribute '
                     'uses) generated.')
        cls.TAG_TABLE = tag_table

    def parse_tags(self):
        """
        Parse tags that used to extract attributes from html, tags to be parsed
        are stas_tag, cat_tag, keywords_tag and posted_tag.

        Args:
            self - instance of class ArtworkParser
        """
        self.stats_tag = self.bs.find('td', {'class': 'alt1 stats-container'})
        self.cat_tag = self.bs.find('td', {'class': 'cat'})
        if self.stats_tag:
            self.keywords_tag = self.stats_tag.find('div', {'id': 'keywords'})
            self.posted_tag = self.stats_tag.find('span', {'class': 'popup_date'}).string
            logger.debug(self.posted_tag)
            self.rating_tag = self.stats_tag.find('div', {'align': 'left'})
            self.rating_tag = self.rating_tag.find('img') if self.rating_tag else None
        else:
            # even cannot get stats_tag, still set tag to None to make sure other
            # method can access property accordingly
            self.keywords_tag = None
            self.posted_tag = None
            self.rating_tag = None
            logger.debug('cannot parse stats_tag, set keywords_tag and posted_'
                         'tag to None.')
        logger.debug('parsed tags used to retrieve artwork attribute.')

    def __init__(self, html, url):
        # lazy load similar to Parser, will compile regex for only once
        if not ArtworkParser.REGEX_TABLE:
            ArtworkParser.generate_regex_table()
        if not ArtworkParser.TAG_TABLE:
            ArtworkParser.generate_tag_table()

        # call super class's init method
        super(ArtworkParser, self).__init__(html, url)
        # parse tags
        self.parse_tags()

        logger.debug('artwork parser initialized.')


    def get_download_link(self):
        """
        Get download link from html.

        Args:
            self - instance of class ArtworkParser

        Returns:
            download_link - the download link of artwork, '' if cannot get
        """
        try:
            download_link = ''
            image_tag = self.bs.find('img', {'id': 'submissionImg'})
            object_tag = self.bs.find('object', {'id':'flash_embed'})
            if image_tag and image_tag.has_attr('src'):
                download_link = 'https:' + image_tag['src']
                logger.info('retrieved download link - "%s".' % download_link)
            # looks for .swf
            elif object_tag and object_tag.has_attr('data'):
                download_link = 'https:' + object_tag['data']
                logger.info('retrieved download link - "%s".' % download_link)
            else:
                logger.info('unable to retrieve download link.')
            return download_link
        except:
            logger.info('unable to retrieve download link.')

    def get_alt_and_description(self):
        """
        return true if story is mentioned in category or title.
        or if submission is a flash or music
        """
        try:
            self.category = self.bs.find('b', text='Category:').next_sibling
            logger.debug('Category found = %s' % self.category)
            # for getting title of submission
            self.posted_title = self.get_posted_title()
            logger.debug('Title = %s' % self.posted_title)
            # for checking the description
            desc_table = self.bs.findAll('table', {'class': 'maintable'})[1]
            desc_row = desc_table.findAll('tr')[2]
            # desc = desc_table.find('td', {'class': 'alt1'})
            desc = str(desc_row)
            if DESCRIPTION_KEYWORDS:
                for keyword in DESCRIPTION_KEYWORDS:
                    if keyword.lower() in self.category.lower():
                        logger.debug('Matched category to %s' % keyword)
                        return True
                    elif keyword.lower() in self.posted_title.lower():
                        logger.debug('Matched %s in title' % keyword)
                        return True
                    elif keyword.lower() in desc.lower():
                        logger.debug('Matched %s in description' % keyword)
                        return True
            else:
                logger.info('Found no match for description needed.')
                return False
        except:
            return False
    def get_alt_download_link(self):
        """
        Get download link from the download link in view page.
        """
        try:
            download_link = ''
            download_not_tag = self.bs.find('a', text='Download')
            download_link = 'https:' +  download_not_tag['href']
            return download_link
        except:
            logger.info('unable to retrieve download link.')

    def get_filename(self):
        """
        Gets filename to save the post as.
        """
        try:
            self.stats_tag = self.bs.find('td', {'class': 'alt1 stats-container'})
            self.posted_title = self.get_posted_title()
            self.posted_time = self.get_posted_time()
            filename = "%s %s" %(self.posted_time,self.posted_title)
            filename = filename.replace('/'," ,' ")
            filename = re.sub(r'[\\/*?:"<>|]',"",filename)
            return filename
        except:
            filename = 'error'

    def get_description(self, filename):
        """
        returns the table containing tags and description
        """
        try:
            desc_table = self.bs.findAll('table', {'class': 'maintable'})[1]
            desc = str(desc_table)
            desc = unicodedata.normalize('NFKD', desc)
            desc = (desc.encode('ascii','ignore')).decode('utf-8')
            style = """
                    <link type="text/css" rel="stylesheet" href="../../../css/dark.css" />
                    <link type="text/css" rel="stylesheet" href="../../css/dark.css" />
                    <link type="text/css" rel="stylesheet" href="../css/dark.css" />
                    <link type="text/css" rel="stylesheet" href="http://www.furaffinity.net/themes/classic/css/dark.css" />
                    """

            data = '<html><body>' + style + desc + '</body></html>'
            with open('images/' + filename + ' Description.html', 'wb') as description:
                description.write(data.encode())
                description.close()
                logger.info('Description saved.')
                return True
        except:
            return False
        return desc
    
    def get_artist(self):
        try:
            self.td_title_by_artist = self.bs.find('td', {'class': 'cat'})
            self.artist_url = self.td_title_by_artist.contents[3]
            self.artist = self.artist_url.contents[0]
            return self.artist
        except:
            return '_user_unknown_'

    def get_tag(self, tag):
        try:
            self.category = self.bs.find('td', {'class':'alt1 stats-container'})
            for index, content in enumerate( self.category.contents, start=0):
                if self.category.contents[index].string == tag:
                    tag_index = index + 1
                    self.category_tag = self.category.contents[tag_index].string
                    logger.debug(tag + " " + self.category_tag)
                    return self.category_tag
        except:
            logger.info("Category tag not found.")

    def get_tag_category(self):
        try:
            category = self.get_tag('Category:')
            return category
        except:
            logger.info("Unable to retrieve Category.")

    def get_tag_gender(self):
        try:
            gender = self.get_tag('Gender:')
            return category
        except:
            logger.info("Unable to retrieve Gender.")

    def get_tag_resolution(self):
        try:
            resolution = self.get_tag('Resolution:')
            return category
        except:
            logger.info("Unable to retrieve Resolution.")

    def get_tag_species(self):
        try:
            species = self.get_tag('Species:')
            return category
        except:
            logger.info("Unable to retrieve Species.")

    def get_tag_theme(self):
        try:
            theme = self.get_tag('Theme:')
            return category
        except:
            logger.info("Unable to retrieve Theme.")

    def get_id(self):
        try:
            if self.url.find('/view/') != -1:
                id = self.url.split('/view/',1)[1]
                if '/' in id:
                    id = id.split('/',1)[0]
                logger.debug("post id = " + id)
                return id
            elif self.url.find('/full/') != -1:
                id = self.url.split('/full/',1)[1]
                if '/' in id:
                    id = id.split('/',1)[0]
                logger.debug("post id = " + id)
                return id
        except:
            logger.debug("id not returned")

    def get_maturity_rating(self):
        try:
            self.rating = self.bs.find('meta', {'name', 'twitter:data2'})
            self.rating = self.rating['content']
            logger.debug("Content Rating is: " + self.rating)
        except:
            logger.debug("Content Rating not found")
            return 'Unknown'

    def get_posted_time(self): # something needs to change
        # get posted time from meta content
        try:
            self.posted_time = self.stats_tag.find('span', {'class': 'popup_date'}).string
            logger.debug("Posted time is: " + self.posted_time)
            self.posted_time = util.parse_datetime(self.posted_time)
            self.posted_time = self.posted_time.strftime("%Y-%m-%d_%H-%M")
            return self.posted_time
        except:
            return 

    def get_posted_title(self):
        # get posted time from posted_tag
        # returns "title by artist"
        try:
            self.posted_titlename = self.bs.find('meta', {'property': 'og:title'})
            if self.posted_titlename.has_attr('content'):
                return self.posted_titlename['content']
        except:
            logger.info("No title found for post. using '_no title_")
            return '_no title_'

    @staticmethod
    def get_matched_string(tag, regex):
        # use findall to get all matched string from tag and regex
        match = re.findall(regex, str(tag))
        if match:
            return match

    @staticmethod
    def format_resolution(resolution):
        # convert from resolution like "1920x1080" to a attribute dictionary
        resolution = resolution.split('x')
        if (len(resolution) >= 2):
            # convert string to int here
            formatted_resolution = {'Width'     : int(resolution[0]),
                                    'Height'    : int(resolution[1])}
            return formatted_resolution
            
    @staticmethod
    def combine_keywords(keywords):
        # use reduce to combine all keywords to a string seperate by space
        return reduce(lambda x, y : x + ' ' + y, keywords)

    @staticmethod
    def generate_unparsed_attributes_log(unparsed_attributes):
        # use unparsed_attributes set to generate log message
        # convert set to list
        unparsed_attributes = list(unparsed_attributes)
        if unparsed_attributes:
            # use reduce to combine all attributes together seperate by space
            return 'unparsed attributes: ' + reduce(lambda x, y : x + ' ' + y, unparsed_attributes) + '.'
        else:
            return 'all attributes parsed.'

    @staticmethod
    def get_adult(rating_tag):
        # use rating tag(img) to get if artwork contains adult content
        # True if content, False if not
        if rating_tag.has_attr('alt'):
            if rating_tag['alt'] == 'Adult rating':
                return True
            return False
        return False

    def get_artwork_attributes(self):
        """
        Get artwork's attributes from html.

        Args:
            self - instance of class ArtworkParser

        Returns:
            attributes - attribute dictionary
        """
        # generate unparsed attributes set
        unparsed_set = set(ArtworkParser.ARTWORK_ATTRIBUTES)
        # initalize attributes
        attributes = {}

        # get posted time
        if self.posted_tag:
            posted_time = self.posted_tag
            if posted_time:
                # parse posted time and format it to string that will
                # recognized by sqlite
                posted_time = util.parse_datetime(posted_time)
                attributes['Posted'] = posted_time.strftime("%Y-%m-%d %H:%M")
            else:
                unparsed_set.add('Posted')

        # get adult
        if self.rating_tag:
            attributes['Adult'] = self.get_adult(self.rating_tag)

        # get other attributes
        for attribute in ArtworkParser.ARTWORK_ATTRIBUTES:
            # regular form - get tag and regex, and use regex to match from tag
            tag_name = ArtworkParser.TAG_TABLE[attribute]
            try:
                tag = getattr(self, tag_name)
            except AttributeError as error:
                # failed to get tag, skip
                continue
            regex = ArtworkParser.REGEX_TABLE[attribute]
            content = self.get_matched_string(tag, regex)

            if not content:
                # cannot extract attribute from tag, skip
                continue
            else:
                if attribute == 'Keywords':
                    # combine keywords
                    content = self.combine_keywords(content)
                else:
                    # other attributes
                    content = content[0]
                    if attribute in ArtworkParser.INT_ATTRIBUTES:
                        # convert string to int if necessary
                        content = int(content)

            if attribute == 'Resolution':
                # format resolution here
                resolution = self.format_resolution(content)
                if resolution:
                    attributes.update(resolution)
                    unparsed_set.remove('Resolution')
            else:
                # other attribute
                attributes[attribute] = content
                unparsed_set.remove(attribute)

        logger.info(self.generate_unparsed_attributes_log(unparsed_set))

        return attributes

    @staticmethod
    def get_filename_extension(link):
        # get filename extension from given download link
        match = re.search(ArtworkParser.FILENAME_EXTENSION_REGEX, link)
        if match:
            if not len(match.group(1)) > 4:
                return match.group(1)
            else:
                logger.warning('Did not retrieve filename extention. Using JPG extension. Be sure to check file.')
                return 'jpg'

    @staticmethod
    def view_to_full(url):
        # convert url like /view/ to /full/
        return url.replace('view', 'full')
