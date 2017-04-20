"""Munki middleware provider to generate signed CloudFront requests."""

import os
import time
import json
import base64
from string import maketrans
from OpenSSL.crypto import FILETYPE_PEM
from OpenSSL.crypto import load_privatekey
from OpenSSL.crypto import sign
from Foundation import CFPreferencesCopyAppValue

__version__ = '1.0'

BUNDLE = 'com.github.aaronburchfield.cloudfront'
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
    # Sign and encode request policy
    signature = base64.b64encode(sign(key, request_policy, 'RSA-SHA1'))
    # Replace unsafe characters
    signature = signature.translate(maketrans('+=/', '-_~'))
    # Format the final request URL
    cloudfront_request = ("{0}?Expires={1}&Signature={2}&Key-Pair-Id={3}"
                          .format(resource, expires, signature, access_id))
    return cloudfront_request


def generate_cloudfront_url(url):
    """Read the required components to build a CloudFront request."""
    # Read our CloudFront key from file
    key = load_privatekey(FILETYPE_PEM, open(KEYFILEPATH, 'r').read())
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
