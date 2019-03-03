from io import BytesIO
from PIL import Image
import shutil
import arrow

from bs4 import BeautifulSoup
import requests


def get_stream_url(flickr_link):
    '''Processes a long flickr link to the main stream page'''

    parsed = flickr_link.replace('https://', '').split('/')
    url = '/'.join(parsed[:parsed.index('nlowell') + 1])

    return 'https://' + url


def get_last_stream_page(stream_url, album=False):
    '''Extracts the integer of the last page in a stream'''

    stream_page = requests.get(stream_url)
    ssoup = BeautifulSoup(stream_page.text, 'html.parser')
    
    if album:
        page_class = 'view pagination-view requiredToShowOnServer'
    
    else:
        page_class = 'view pagination-view requiredToShowOnServer photostream'
    
    pagination = list(ssoup.find(
        class_=page_class
    ).children)[-4:-3]
    last_page = int(pagination[0].text)

    return last_page


def get_photostream(stream_url, album=False):
    '''Returns a list of images from a photostream page'''

    photos = requests.get(stream_url)
    psoup = BeautifulSoup(photos.text, 'html.parser')

    stream_list = psoup.find_all(
        class_="view photo-list-photo-view requiredToShowOnServer photo"
        + "stream awake"
    )

    if album:
        stream_list = psoup.find_all(
        class_="view photo-list-photo-view requiredToShowOn"
        + "Server awake"
    )
    
    photo_url_list = []
    for photo in stream_list:

        photo_url = photo['style'][photo['style'].index(
            'url(//'):-1].replace(
            'url(//', 'https://')

        photo_url_list.append(photo_url)

    return photo_url_list


def build_flickr_archive(flickr_link, archive, album=False):
    '''Iterates through entire photostream to build archive'''

    
    if album:
        stream_url = flickr_link
    
    else:
        stream_url = get_stream_url(flickr_link)
    
    last_page = get_last_stream_page(stream_url, album)

    
    for page in (range(1, last_page)):
        url = stream_url + '/page' + str(page)
        print(url)
        stream = get_photostream(url, album)
        archive = process_photo_stream_page(stream, archive)

    return archive


def get_original_photo(photo_id):
    '''for a single photo id, returns dictionary of photo attributes'''

    info = {}

    original_page = 'https://www.flickr.com/photos/nlowell/' \
        + photo_id + '/sizes/o/'
    html = requests.get(original_page)
    soup = BeautifulSoup(html.text, 'html.parser')
    orig_link = soup.find(attrs={'id': 'allsizes-photo'})
    src = orig_link.contents[1]
    info['link'] = src.get('src')

    raw_title = soup.title.text

    title = soup.title.text.split('|')[1].strip()

    if title.find('.') > 0:

        try:
            info['condition'] = title.split('.')[-1].strip()
            full_title = title.split('.')[0].split(' ')
            info['tag'] = full_title[0]
            info['temp'] = full_title[1]
            info['sun'] = ' '.join(full_title[2:])
        except:
            info['tag'] = 'Error'

    elif title.find(',') > 0:

        try:
            info['condition'] = title.split(',')[-1].strip()
            full_title = title.split(',')[0].split(' ')
            info['tag'] = full_title[0]
            info['temp'] = full_title[1]
            info['sun'] = ' '.join(full_title[2:])

        except:
            info['tag'] = 'Error'

    info['raw_title'] = raw_title  # incase titles need to be reprocessed

    if info.get('tag') not in ['#tommw', '#tommy']:
        info = None

    return info


def process_photo_stream_page(stream, archive=None):

    if not archive:
        archive = get_archive()

    for photo in stream:
        image_name = photo.split('/')[-1]
        photo_id = image_name.split('_')[0]

        if photo_id in archive['meta']['ids']:
            # skip photos already recorded
            continue

        # Save the thumb size image
        thumb_name = 'images/' + photo_id + '.jpg'
        image = requests.get(photo, stream=True)

        with open(thumb_name, 'wb') as image_file:
            shutil.copyfileobj(image.raw, image_file)

        # Only the original has EXIF data
        info = get_original_photo(photo_id)

        # Format the EXIF data
        if info:
            info['photo_id'] = photo_id
            info['thumb'] = thumb_name
            p_url = info.get('link')
            if p_url:
                camera, timestamp = get_exif(p_url)
            else:
                camera, timestamp = ('Error', 'Error')
            info['camera'] = camera
            info['timestamp'] = timestamp
            
            date = timestamp.split(' ')[0]
    
            info['date'] = date
            
            archive['data'].append(info)
            archive['meta']['ids'].append(photo_id)
            
            print(photo_id + ' added')

        else:
            print('no #tommow tag found')

    return archive


def get_exif(url):
    photo = requests.get(url)
    im = Image.open(BytesIO(photo.content))
    exif_data = im._getexif()
    camera = exif_data[272]
    raw_timestamp = exif_data[306]
    timestamp = raw_timestamp.replace(':', '-', 2)

    return (camera, timestamp)
