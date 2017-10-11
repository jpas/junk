import json
import sys
import time
from base64 import b64decode, b64encode
from difflib import get_close_matches
from secrets import randbelow
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from fuzzywuzzy import process

def _as_bytes(data):
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode('UTF-8')
    raise ValueError('not bytes')


def _generate_id():
    # from: https://messenger.klinkerapps.com/resources/js/helper.js
    MAGIC = 922337203685477
    return randbelow(MAGIC - 1) + 1 # between 1 and MAGIC

class API:
    def __init__(self, local_storage):
        self.account = local_storage['accountId']
        self.secret = local_storage['hash']
        self.salt = local_storage['salt']

        self.key = PBKDF2(
            f'{self.account}:{self.secret}\n'.encode('utf-8'),
            self.salt.encode('utf-8'),
            dkLen=32,
            count=10000
        )

        self._contacts = None
        self._conversations = None

    def encrypt(self, data):
        if isinstance(data, str):
            data = data.encode('UTF-8')
        iv = Random.new().read(16)  # 128-bit iv
        cipher = AES.new(self.key, AES.MODE_CBC, iv)

        # pad with PKCS#5 to match sjcl.js
        pad = 16 - len(data) % 16
        if pad < 16:
            pad = bytes([pad] * pad)
            data += pad
        ciphertext = cipher.encrypt(data)

        return '-:-'.join(map(
            lambda b: str(b64encode(b), encoding='utf-8'),
            (iv, ciphertext)
        ))

    def decrypt(self, data):
        iv, ciphertext = map(b64decode, data.split('-:-'))
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext)

        # remove PKCS#5 padding
        pad = plaintext[-1]
        if pad <= 16 and plaintext[-pad] == pad:
            plaintext = plaintext[:-pad]

        return str(plaintext, encoding='utf-8')

    def _request(self, endpoint, data=None):
        url = 'https://api.messenger.klinkerapps.com/api' + endpoint
        if data is not None:
            data = urlencode(data).encode('utf-8')
        with urlopen(url, data=data) as res:
            return str(res.read(), encoding='utf-8')

    def send(self, to, message):
        if isinstance(to, str):
            best, _ = self.best_conversation(to)
            to = best['device_id']

        if not isinstance(to, int):
            raise ValueError('to is not an integer')

        if to not in self.conversation_device_ids:
            raise ValueError(f'to is not a conversation that exists: {to}')

        data = {
            'account_id': self.account,
            'device_id': _generate_id(),
            'device_conversation_id': to,
            'message_type': 2,
            'data': self.encrypt(message),
            'timestamp': str(round(time.time() * 1000)),
            'mime_type': self.encrypt('text/plain'),
            'read': 'true',
            'seen': 'true',
        }
        print(data)
        return self._request('/v1/messages/add', data)

    @property
    def conversations(self):
        if self._conversations is None:
            res = self._request(f'/v1/conversations?account_id={self.account}')
            self._conversations = json.loads(res)
            for convo in self._conversations:
                for key, value in convo.items():
                    if isinstance(value, str) and '-:-' in value:
                        convo[key] = self.decrypt(value)
        return self._conversations

    @property
    def conversation_device_ids(self):
        for convo in self.conversations:
            yield convo['device_id']

    def best_conversation(self, name, archive=False):
        if archive:
            convos = self.conversations
        else:
            # disallow archived conversations
            convos = (c for c in self.conversations if not c['archive'])

        best, score = process.extractOne(
            {'title': name},
            convos,
            processor=lambda c: c['title'],
        )

        if score < 90:
            raise RuntimeError(f'score not high enough: {best} with {score}')

        return best


def main():
    local_storage =  {
        'accountId': 'ed358e3a5673c8fd630775274ce5ba681f5cc6235fa986bfffb4a8499e14bdb4',
        'hash': 'HMBO3QFkxedykWcBr9PlijJM13towi/f0pBWZ1JIVU8=',
        'salt': '1266cdedc11efe8c',
    }
    api = API(local_storage)

    to = sys.argv[1]
    message = ' '.join(sys.argv[2:])
    to = api.best_conversation(to)

    if not message:
        print(to['title'])
        return

    print('to:', to['title'], '>', message)
    print(to)
    i = input('send? [yN] ')
    if i.lower() == 'y':
        print(api.send(to['device_id'], message))

if __name__ == '__main__':
    exit(main())
