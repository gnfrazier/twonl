from io import BytesIO
from PIL import Image

from bs4 import BeautifulSoup
import requests


def get_photostream(flickr_link):
    '''Returns a list of images from the photostream page'''
    
    parsed = flickr_link.replace('https://','').split('/')
    url = '/'.join(parsed[:parsed.index('nlowell')+1])
    
    stream_url = 'https://' + url
    photos = requests.get(stream_url)
    psoup = BeautifulSoup(photos.text, 'html.parser')
    
    stream_list = psoup.find_all(
    class_="view photo-list-photo-view requiredToShowOnServer photostream awake"
    )
    
    photo_url_list = []
    for photo in stream_list:

        photo_url = photo['style'][photo['style'].index(
                    'url(//'):-1].replace(
                    'url(//', 'https://')

        photo_url_list.append(photo_url)

    
    return photo_url_list


def get_original_photo(photo_id):
    '''for a single photo id, returns dictionary of photo attributes'''
    
    info = {}
    
    original_page = 'https://www.flickr.com/photos/nlowell/' + photo_id + '/sizes/o/'
    html = requests.get(original_page)
    soup = BeautifulSoup(html.text, 'html.parser')
    orig_link =soup.find(attrs={'id':'allsizes-photo'})
    src = orig_link.contents[1]
    info['link'] = src.get('src')
    
    title = soup.title.text.replace(
    'All sizes | ','').replace(
    ' | Flickr - Photo Sharing!', '')
    
    if title.index('.'):
        info['condition'] = title.split('.')[-1].strip()
        full_title = title.split('.')[0].split(' ')
        info['tag'] = full_title[0]
        info['temp'] = full_title[1]
        
    elif title.index(','):
        info['condition'] = title.split(',')[-1].strip()
        full_title = title.split(',')[0].split(' ')
        info['tag'] = full_title[0]
        info['temp'] = full_title[1]        
        
        

    info['sun'] = ' '.join(full_title[2:])
    
    if info['tag'] != '#tommw':
        info = None

    return info



def get_exif(url):
    photo = requests.get(url)
    im = Image.open(BytesIO(photo.content))
    exif_data = im._getexif()
    camera = exif_data[272]
    timestamp = exif_data[306]
    
    return (camera, timestamp)
