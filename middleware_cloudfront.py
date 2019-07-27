"""Munki middleware provider to generate signed CloudFront requests."""

import os
import time
import json
import base64
import objc
from rsa import PrivateKey, sign
from Foundation import CFPreferencesCopyAppValue, NSData

__version__ = '1.1'

BUNDLE = 'com.github.aaronburchfield.cloudfront'
CERT_PREFERENCE_NAME = 'cloudfront_certificate'
KEYFILENAME = 'munkiaccess.pem'
KEYFILEPATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           KEYFILENAME))


def read_preference(key, bundle):
    """Read a preference key from a preference domain."""
    value = CFPreferencesCopyAppValue(key, bundle)
    return value


def assemble_cloudfront_request(resource, key, access_id, expires):
    """Assemble a CloudFront request."""
    # Format a request policy for the resource
    request_policy = {
        "Statement": [{"Resource": resource, "Condition": {"DateLessThan":
                      {"AWS:EpochTime": expires}}}]
    }
    request_policy = json.dumps(request_policy).replace(' ', '')
    request_policy = request_policy.encode('utf8')
    # Sign and encode request policy
    signature = base64.b64encode(sign(request_policy, key, 'SHA-1'))
    # Decode as UTF-8 string
    signature = signature.decode('utf8')
    # Replace unsafe characters
    signature = signature.translate(str.maketrans('+=/', '-_~'))
    # Format the final request URL
    cloudfront_request = ("{0}?Expires={1}&Signature={2}&Key-Pair-Id={3}"
                          .format(resource, expires, signature, access_id))
    return cloudfront_request


def generate_cloudfront_url(url):
    """Read the required components to build a CloudFront request."""
    # Read our CloudFront key from preference (preferred) or file (fallback)
    pref_cert = read_preference(CERT_PREFERENCE_NAME, BUNDLE)
    if pref_cert and isinstance(pref_cert, NSData):
        key = PrivateKey.load_pkcs1(base64.b64decode(pref_cert))
    elif pref_cert and isinstance(pref_cert, objc.pyobjc_unicode):
        # If we have a string type decode the base64 blob
        key = PrivateKey.load_pkcs1(base64.b64decode(pref_cert))
    else:
        cert = open(KEYFILEPATH, 'r').read()
        key = PrivateKey.load_pkcs1(cert.encode('utf8'))
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

