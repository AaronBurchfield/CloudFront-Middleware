"""Munki middleware provider to generate signed CloudFront requests."""

import os
import time
import json
import base64
import objc
import six

from Foundation import CFPreferencesCopyAppValue, NSData

PYTHONTHREE = six.PY3

if PYTHONTHREE:
    # Py3 imports
    from rsa import PrivateKey
    from rsa import sign
else:
    # Py2 imports
    from string import maketrans
    from OpenSSL.crypto import FILETYPE_PEM
    from OpenSSL.crypto import load_privatekey
    from OpenSSL.crypto import sign

__version__ = '2.0'

BUNDLE = 'com.github.aaronburchfield.cloudfront'
CERT_PREFERENCE_NAME = 'cloudfront_certificate'
KEYFILENAME = 'munkiaccess.pem'
KEYFILEPATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           KEYFILENAME))


def read_preference(key, bundle):
    """Read a preference key from a preference domain."""
    value = CFPreferencesCopyAppValue(key, bundle)
    return value


def private_key_from_pref_data(pref_cert):
    """Load private key from NSData."""
    if PYTHONTHREE:
        private_key = PrivateKey.load_pkcs1(bytes(pref_cert))
    else:
        private_key = load_privatekey(FILETYPE_PEM, str(pref_cert))

    return private_key


def private_key_from_pref(pref_cert):
    """Load private key from string."""
    if PYTHONTHREE:
        private_key = PrivateKey.load_pkcs1(base64.b64decode(pref_cert))
    else:
        private_key = load_privatekey(FILETYPE_PEM, base64.b64decode(pref_cert))

    return private_key


def private_key_from_file(key_file):
    """Load private key from file path."""
    with open(key_file, 'r') as f:
        data = f.read()

    if PYTHONTHREE:
        private_key = PrivateKey.load_pkcs1(data.encode('utf8'))
    else:
        private_key = load_privatekey(FILETYPE_PEM, data)

    return private_key


def sign_request_policy(key, request_policy):
    """Return a request policy signature."""
    if PYTHONTHREE:
        request_policy = request_policy.encode('utf8')
        signature = base64.b64encode(sign(request_policy, key, 'SHA-1'))
        signature = signature.decode('utf-8')
        translation = str.maketrans('+=/', '-_~')
    else:
        signature = base64.b64encode(sign(key, request_policy, 'RSA-SHA1'))
        translation = maketrans('+=/', '-_~')

    return signature.translate(translation)


def assemble_cloudfront_request(resource, key, access_id, expires):
    """Assemble a CloudFront request."""
    # Format a request policy for the resource
    request_policy = {
        "Statement": [{"Resource": resource, "Condition": {"DateLessThan":
                      {"AWS:EpochTime": expires}}}]
    }
    request_policy = json.dumps(request_policy).replace(' ', '')
    # Sign and encode request policy
    signature = sign_request_policy(key, request_policy)
    # Format the final request URL
    cloudfront_request = ("{0}?Expires={1}&Signature={2}&Key-Pair-Id={3}"
                          .format(resource, expires, signature, access_id))
    return cloudfront_request


def generate_cloudfront_url(url):
    """Read the required components to build a CloudFront request."""
    # Read our CloudFront key from preference (preferred) or file (fallback)
    pref_cert = read_preference(CERT_PREFERENCE_NAME, BUNDLE)
    if pref_cert and isinstance(pref_cert, NSData):
        key = private_key_from_pref_data(pref_cert)
    elif pref_cert and isinstance(pref_cert, objc.pyobjc_unicode):
        # If we have a string type decode the base64 blob
        key = private_key_from_pref(pref_cert)
    else:
        key = private_key_from_file(KEYFILEPATH)
    # Read CloudFront access key id and resource expiration from preference
    access_id = read_preference('access_id', BUNDLE)
    expire_after = read_preference('expire_after', BUNDLE) or 60
    expires = int(time.time()) + 60 * int(expire_after)
    cloudfront_url = assemble_cloudfront_request(url, key, access_id, expires)
    return cloudfront_url


def process_request_options(options):
    """Return a signed request for CloudFront resources."""
    domain_name = read_preference('domain_name', BUNDLE) or 'cloudfront.net'
    if domain_name in options['url']:
        options['url'] = generate_cloudfront_url(options['url'])
    return options
