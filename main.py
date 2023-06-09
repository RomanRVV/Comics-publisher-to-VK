import requests
import os
from dotenv import load_dotenv, find_dotenv
from random import randint


def download_pic(url):
    response = requests.get(url)
    response.raise_for_status()
    with open('image.png', 'wb') as file:
        file.write(response.content)


def fetch_xkcd_comic_and_comments(url):
    response = requests.get(url)
    response.raise_for_status()
    comic = response.json()
    image_url = comic['img']
    comments = comic['alt']
    download_pic(image_url)
    return comments


def handle_vk_error(response):
    vk_answer = response.json()
    try:
        if vk_answer['error']:
            raise requests.HTTPError
    except requests.HTTPError:
        error_msg = vk_answer['error']['error_msg']
        error_code = vk_answer['error']['error_code']
        print('Код ошибки:', error_msg)
        print('Текст ошибки:', error_code)
    except KeyError:
        pass


def get_url_to_download_image(group_id, access_token):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    api_version = 5.131
    payload = {
        'group_id': group_id,
        'access_token': access_token,
        'v': api_version
    }
    response = requests.get(url, params=payload)
    handle_vk_error(response)
    response.raise_for_status()
    return response.json()


def upload_image_to_server(url):
    with open('image.png', 'rb') as file:
        upload_url = url['response']['upload_url']
        files = {
            'photo': file
        }
        response = requests.post(upload_url, files=files)
    handle_vk_error(response)
    response.raise_for_status()
    return response.json()


def save_image_in_album(photo, server, hash, group_id, access_token):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    api_version = 5.131
    payload = {
        'access_token': access_token,
        'group_id': group_id,
        'v': api_version,
        'photo': photo,
        'server': server,
        'hash': hash
    }
    response = requests.post(url, params=payload)
    handle_vk_error(response)
    response.raise_for_status()
    return response.json()


def post_image_on_wall(comments, group_id, access_token, media_id, owner_id):
    attachments = f'photo{owner_id}_{media_id}'
    url = 'https://api.vk.com/method/wall.post'
    api_version = 5.131
    payload = {
        'access_token': access_token,
        'v': api_version,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'attachments': attachments,
        'message': comments
    }
    response = requests.post(url, params=payload)
    handle_vk_error(response)
    response.raise_for_status()


def main():
    load_dotenv(find_dotenv())
    vk_access_token = os.environ['VK_ACCESS_TOKEN']
    vk_group_id = os.environ['VK_GROUP_ID']
    total_comics = 2786
    random_comic_number = randint(0, total_comics)
    comic_url = f'https://xkcd.com/{random_comic_number}/info.0.json'
    try:
        comments = fetch_xkcd_comic_and_comments(comic_url)
        data_to_save_image = upload_image_to_server(get_url_to_download_image(vk_group_id, vk_access_token))
        vk_photo = data_to_save_image['photo']
        vk_server = data_to_save_image['server']
        vk_hash = data_to_save_image['hash']
        data_to_post_image = save_image_in_album(vk_photo, vk_server, vk_hash, vk_group_id, vk_access_token)
        media_id = data_to_post_image['response'][0]['id']
        owner_id = data_to_post_image['response'][0]['owner_id']
        post_image_on_wall(comments, vk_group_id, vk_access_token, media_id, owner_id)
    finally:
        os.remove('image.png')


if __name__ == '__main__':
    main()
