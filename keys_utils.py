# -*- coding: utf-8 -*-
'''
Created on Oct 16, 2017

@author: marcoxzh3
'''

_debug = False
KEY_LENGTH = 1024
DUMMY = '`~!$%^&*-+=|\\;?/<>'

import getpass, json, random
from Crypto.Cipher import AES


def import_plain_keys(filename):
    """
    import  keys in plain json text
    :param str filename -- the name of the plain key file
    :param dict the author's information, see: https://uploadbeta.com/api/steemit/wechat/?cache
    """
    with open(filename, 'r') as handle:
        obj = json.load(handle)
    if _debug:
        print(obj)
    return obj
pass # def importplainkeys(filename)


def import_encrypted_keys(password, filename):
    """
    import keys from encrypted file
    :param str password -- the password for decryption
    :param str filename -- the name of the encrypted key file
    """
    # Load the keys
    f = open(filename, 'rb')
    arr_byte = f.read()
    f.close()

    # Decrypt, un-salt, and return
    decrypted = AES.new(password, AES.MODE_ECB).decrypt(arr_byte)
    swif = ''.join([x for x in decrypted.decode('utf-8') if x not in DUMMY])
    if _debug:
        print(bytes)
        print(decrypted)
        print(swif)
        print('import_encrypted_keys: raw=\'%s\'' % str(arr_byte))
        print('import_encrypted_keys: usl=\'%s\'' % decrypted)
        print('import_encrypted_keys: dec=\'%s\'' % swif)
    pass # if _debug
    return json.loads(swif.replace('\'', '"'))
pass # def import_encrypted_keys(password, filename)


def export_plain_keys(wif, filename):
    """
    export keys to file in plain json text
    :param dict wif -- the keys
    :param str filename -- the name of the target file
    """
    f = open(filename, 'w')
    f.write(json.dumps(wif, indent=4))
    f.close()
    if _debug:
        with open(filename, 'r') as handle:
            wif2 = json.load(handle)
        assert len(wif.keys()) == len(wif2.keys())
        for k in wif.keys():
            assert wif[k] == wif2[k]
    pass # if _debug
pass # def export_plain_keys(wif, filename)


def export_encrypted_keys(wif, filename):
    """
    export keys to file in encrypted bytes
    :param dict wif -- the keys
    :param str filename -- the name of the target file
    """
    # Salt the keys with dummies
    swif = str(wif)
    if _debug:
        for d in DUMMY:
            assert d not in swif
    pass # for - if _debug
    while len(swif) < KEY_LENGTH:
        idx = random.randint(0, len(swif))
        if idx == 0:
            swif += random.choice(DUMMY)
        elif idx == len(swif):
            swif = random.choice(DUMMY) + swif
        else:
            swif = swif[:idx] + random.choice(DUMMY) + swif[idx:]
        pass # else - elif - if
    pass # while len(swif) < KEY_LENGTH

    # Encrypt and write to file
    encrypted = AES.new(pw, AES.MODE_ECB).encrypt(swif)
    if _debug:
        tmp = ''.join([x for x in swif if x not in DUMMY])
        assert tmp == str(wif)
        print('export_encrypted_keys: raw=\'%s\'' % str(wif))
        print('export_encrypted_keys: slt=\'%s\'' % swif)
        print('export_encrypted_keys: enc=\'%s\'' % encrypted)
    pass # if _debug
    f = open(filename, 'wb')
    f.write(encrypted)
    f.close()
pass # def export_encrypted_keys(wif, filename)


if __name__ == '__main__':
    pw = ''
    if _debug:
        pw = '0123456789ABCDEF'
        print(pw)
    else:
        pw = getpass.getpass()
        while len(pw) != 16:
            print('Error: length of password must be 16')
            pw = getpass.getpass()
        pass # while len(pw) != 16
    pass # if _debug

    # Import plain keys
    wif = import_plain_keys('keys0.json')
    if _debug:
        print(json.dumps(wif, indent=2))

    # Export encrypted keys
    export_encrypted_keys(wif, 'cnbuddy_keys')

    # Import encrypted keys
    wif2 = import_encrypted_keys(pw, 'cnbuddy_keys')
    if _debug:
        print(json.dumps(wif2, indent=2))
        assert len(wif.keys()) == len(wif2.keys())
        for k, v in wif.items():
            if type(v) is dict:
                for k1 in v:
                    assert v[k1] == wif2[k][k1]
            else:
                assert v == wif2[k]
            pass # else - for k in wif.keys()
        pass # for k, v in wif.items()
    pass # if _debug

    # Export plain keys
    export_plain_keys(wif2, 'keys1.json')

pass # if __name__ == '__main__'
