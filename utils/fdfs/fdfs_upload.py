from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client, get_tracker_conf
from django.conf import settings


class FdfsStorage(Storage):
    '''采用FDFS上传方式'''
    def __init__(self, client_conf=None, base_url=None):
        ''''''
        if not client_conf:
            client_conf = settings.FDFS_CLIENT_CONF

        if not base_url:
            base_url = settings.FDFS_URL

        self.client_conf = client_conf
        self.base_url = base_url

    def _open(self, name, mode='rb'):
        '''重写open'''
        pass

    def _save(self, name, content):
        '''上传到fdfs'''
        client_conf_obj = get_tracker_conf(self.client_conf)
        client = Fdfs_client(client_conf_obj)

        ret = client.upload_appender_by_buffer(content.read())

        if ret.get('Status') != 'Upload successed.':
            raise Exception('上传到fdfs失败')

        return ret.get('Remote file_id')

    def exists(self, name):
        ''''''
        return False


    def url(self, name):
        ''''''
        return self.base_url + name
