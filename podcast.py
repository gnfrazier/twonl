
import requests
import tinytag


def get_mp3(podcast_link, archive):

    mp3_name = podcast_link.split('/')[-1]

    mp3_file = 'audio/' + mp3_name

    if mp3_name in archive['meta']['audio']:
        # skip files already downloaded
        return mp3_file, archive

    file = requests.get(podcast_link)

    if file.status_code != 200:

        return False

    with open(mp3_file, 'wb') as f:
        f.write(file.content)

    archive['meta']['audio'].append(mp3_name)

    return mp3_file, archive



def get_id3_tag(mp3_file):

    id_info = tinytag.TinyTag.get(mp3_file).as_dict()

    title = id_info.get('title')

    if title:
        date = title.split(' ')[-1]
    else:
        date = 'unknown'

    id_info['date'] = date

    id_info['audio'] = mp3_file
    

    return id_info


def match_photo_date(id_info, archive):
    '''Iterates through the archive to match audio
    to a photo record'''

    for walk in archive['data']:

        if walk['date'] == id_info['date']:

            walk.update(id_info)
            mp3_file = id_info.get('audio')
            
            if mp3_file.find('.mp3') > 1:
                mp3_name = mp3_file.strip('audio/')
                archive['meta']['audio'].append(mp3_name)
                
            else:
                print('Unable to get mp3 info from', id_info)

    return archive


def build_audio_archive(podcast_link, archive):
    # TODO complete this function
    # Parse URL into base, date, file_name
    podcast_link.rsplit('/', maxsplit=2)

    pass
