import datetime
import json

from bs4 import BeautifulSoup
import requests
import toml
import twitterscraper as tws
import twython as tw

tw_creds = toml.load('credentials.toml')

mm = {'Jan': '01',
      'Feb': '02',
      'Mar': '03',
      'Apr': '04',
      'May': '05',
      'Jun': '06',
      'Jul': '07',
      'Aug': '08',
      'Sep': '09',
      'Oct': '10',
      'Nov': '11',
      'Dec': '12'}


def get_new_twitter_token(cred):
    tw_creds = cred['api']['twitter']

    twitter = tw.Twython(tw_creds['consumer_key'],
                         tw_creds['consumer_secret'],
                         oauth_version=2)

    ACCESS_TOKEN = twitter.obtain_access_token()

    tw_creds['api']['twitter']['access_token'] = ACCESS_TOKEN

    with open('credentials.toml', 'w') as f:

        toml.dump(cred, f)

    return ACCESS_TOKEN


def get_token(cred):

    token = tw_creds['api']['twitter'].get('access_token')

    if token is None:
        token = get_new_twitter_token(cred)

    return token


def get_twitter(token):

    twitt = tw.Twython(tw_creds['consumer_key'],
                       access_token=token)

    return twitt


def format_tweet_time(tweet_time):
    '''Transforms tweet date time
    format "5:11 AM - 16 Jun 2011"
    to timestamp "2011-06-16 05:11:00" '''

    dt_parts = tweet_time.split(' ')
    year = dt_parts[-1]

    # Convert text month to digits
    month = mm[dt_parts[-2]]

    day = dt_parts[-3]
    raw_time = dt_parts[0].split(':')
    hour = raw_time[0].rjust(2, '0')
    minute = raw_time[-1]
    second = '00'

    # Adjust time for am vs pm
    if dt_parts[1] == 'PM':
        hour_num = int(hour) + 12
        hour = str(hour_num)

    tw_date = '-'.join([year, month, day])
    tw_time = ':'.join([hour, minute, second])
    tw_timestamp = ' '.join([tw_date, tw_time])

    return tw_timestamp, tw_date, tw_time


def clean_twsrapper_time(tweet_data):
    '''Converts date time object in scrapper dict data to string'''

    for tweet in tweet_data:
        tweet['timestamp'] = datetime.datetime.strftime(
            tweet['timestamp'], '%Y-%m-%d %H:%M:%S')
        tweet['date'] = tweet['timestamp'].split(' ')[0]

    return tweet_data


# TODO Use this function to process flicker titles too
def process_tweet_body(body):
    '''Formats tweet body into weather and data parts. '''

    info = {}

    try:
        raw_title = body.split('"')[1]

    except IndexError:

        raw_title = body

    # Early tweets have a dash
    raw_title = raw_title.replace(' -', '')

    comma = raw_title.find(',')

    # Find a period with a space after it.
    period = raw_title.find('. ')

    if comma > 0:
        tag_temp = raw_title[:comma]
        wind_link = raw_title[comma:]

    elif comma < 0 and period > 0:

        tag_temp = raw_title[:period]
        wind_link = raw_title[period:]

    else:
        print('Unable to parse title')
        info['tag'] = 'Error'
        return info

    info['tw_title'] = raw_title

    # TODO refactor using deque to improve performance
    t_parts = tag_temp.split(' ')

    if len(t_parts) < 2:
        print('Unable to parse title')
        info['tag'] = 'Error'
        return info

    info['tag'] = t_parts.pop(0)
    info['temp'] = t_parts.pop(0).strip('F')
    info['sun'] = ' '.join(t_parts)

    w_parts = wind_link.split(' ')
    info['photo_link'] = w_parts.pop()
    info['wind'] = ' '.join(w_parts).strip(', ')

    return info


def process_tweet(tweet_url):
    '''Extracts text, timestamp and date from a tweet by url.'''

    tweet = requests.get(tweet_url)
    tsoup = BeautifulSoup(tweet.text, 'html.parser')

    body = tsoup.title.text
    info = process_tweet_body(body)

    tweet_time = str(tsoup.find(class_="client-and-actions").text.strip())
    tw_time = format_tweet_time(tweet_time)

    info['tweet_timestamp'], info['date'], info['time'] = tw_time

    info['tweet_id'] = tweet_url.split('/')[-1]

    return info


def build_twitter_archive(start_year, end_year):

    tweet_data = []

    for y in range(start_year, end_year):

        for m in range(1, 13):

            e = m + 1
            ye = y

            if e == 13:
                e = 1
                ye = y + 1

            # TODO use the new_tweets function
            tommw_search = tws.query_tweets('#tommw',
                                            limit=None,
                                            begindate=datetime.date(y, m, 2),
                                            enddate=datetime.date(ye, e, 1),
                                            poolsize=30, lang='')

            for tweet in tommw_search:

                tweet.timestamp = datetime.datetime.strftime(
                    tweet.timestamp,
                    '%Y-%m-%d %H:%M:%S')

                # Not tested jan-2019
                tweet.date = tweet.timestamp.split(' ')[0]

                # Only archive Nate's tweets
                if tweet.user == 'nlowell':

                    tweet_data.append(vars(tweet))

    return tweet_data


def new_tweets(archive, start_date=None, end_date=None):
    '''Check for tweets not in archive since last update or by range.'''

    tweet_data = []
    
    if isinstance(start_date, datetime.date):
        start = start_date

    else:

        ts = archive['meta']['last_updated']

        # In 3.7 can use datetime.fromisotime()
        by, bm, bd = tuple(map(int,ts.split('T')[0].split('-')[:3]))
        
        start = datetime.date(by, bm, bd)

    if isinstance(end_date, datetime.date):
        end = end_date

    else:
        today = datetime.date.today()
        # End search tomorrow to avoid invalid search dates
        end = today.replace(day=today.day + 1)

    tommw_search = tws.query_tweets('#tommw',
                                    limit=None,
                                    begindate=start,
                                    enddate=end,
                                    poolsize=30, lang='')

    for tweet in tommw_search:

        tweet.timestamp = datetime.datetime.strftime(
            tweet.timestamp,
            '%Y-%m-%d %H:%M:%S')

        # Not tested jan-2019
        tweet.date = tweet.timestamp.split(' ')[0]

        # Only return Nate's tweets not in the archive
        if (tweet.user == 'nlowell') and (tweet.id not in archive['meta']['tw_ids']):

            tweet_data.append(vars(tweet))

    return tweet_data



def filter_twitter_search(tw_archive):
    '''Breaks list of dictionaries from twitter search
    into walks, errors and unknown lists'''

    walks = []
    unknown = []
    errors = []

    for item in tw_archive:
        tweet = process_tweet_body(item['text'])
        try:
            del item['html']

        except KeyError:
            # If the data is already deleted, that is good
            pass

        item.update(tweet)

        if item['tag'] == '#tommw':

            if item['temp'].isnumeric():
                item['walk'] = 1
                walks.append(item)

            else:
                unknown.append(item)

        else:
            errors.append(item)
    
    walks = tw_key_rename(walks)

    return {'walks':walks, 'unknown':unknown, 'errors':errors}


def tw_key_rename(walks):
    '''Utility to rename identical keys except for date.'''
    
    for walk in walks:
        walk['tw_id'] = walk.pop('id')
        walk['tw_timestamp'] = walk.pop('timestamp')
        
    return walks


def merge_tw_walks_into_photo_walks(archive, walks):
    '''Utility to combine twitter and photo data'''
    
    for walk in walks:

        for item in archive['data']:

            if walk['date'] == item['date']:
                
                # Check the tweet id before merging avoid duplicates
                if walk['tw_id'] not in archive['meta']['tw_ids']:
                    item.update(walk)
                    archive['meta']['tw_ids'].append(walk['tw_id'])


        if walk['tw_id'] not in archive['meta']['tw_ids']:
            archive['data'].append(walk)

            archive['meta']['tw_ids'].append(walk['tw_id'])

    return archive


def save_tweets(archive, record='tweets'):

    filename = record + '.json'

    with open(filename, 'w') as file:

        file.write(json.dumps(archive, indent=4))

    return True


if __name__ == "__main__":

    pass
