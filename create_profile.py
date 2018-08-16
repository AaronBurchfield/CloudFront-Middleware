#!/usr/bin/python
"""Convert our CloudFront PEM file to a mobileconfig."""

import os
import plistlib
import argparse
import base64

PROFILE_DISPLAY_NAME = 'Munki CloudFront Settings'
BUNDLE = 'com.github.aaronburchfield.cloudfront'
PROFILE_FILENAME = 'munki_middleware_cloudfront'


def main():
    """Handle cli arguments and core processing logic."""
    parser = argparse.ArgumentParser(prog='Munki middleware profile creator',
                                     description='Create a profile to manage'
                                     'the munki middleware script.')
    parser.add_argument('-c', '--cert', required=True,
                        help='File path to the CloudFront pem encoded '
                        'certificate.')
    parser.add_argument('-b', '--base64', default=False,
                        type=lambda x:
                            (str(x).lower() in ['true', 'yes', '1']),
                        help='Encode the certificate as a base64 encoded '
                        'string instead of the default data type. '
                        'Accepts: true')
    parser.add_argument('-e', '--expire_after', required=False,
                        help='Time in minutes to expire '
                        'the requests. (Optional)')
    parser.add_argument('-a', '--access_id', required=False,
                        help='AWS access_id associated with the CloudFront '
                        'identity. (Optional)')
    parser.add_argument('-d', '--domain_name', required=False,
                        help='Set the alterative domain name if using a '
                        'domain. (Optional)')
    parser.add_argument('--org_name', required=False, default='',
                        help='Set the profile organization. (Optional)')
    parser.add_argument('--desc', required=False, default='',
                        help='Set the profile description text. (Optional)')
    args = parser.parse_args()

    template = {
        'PayloadUUID': '8217A278-D22A-4591-9620-945E63B6D9B4',
        'PayloadDescription': args.desc,
        'PayloadVersion': 1,
        'PayloadContent': [{
            'PayloadUUID': '1FF25978-1717-4FD6-967E-DC0DCBEA20A1',
            'PayloadDescription': args.desc,
            'PayloadOrganization': args.org_name,
            'PayloadIdentifier': '1FF25978-1717-4FD6-967E-DC0DCBEA20A1',
            'PayloadDisplayName': PROFILE_DISPLAY_NAME,
            'PayloadType': BUNDLE,
            'PayloadEnabled': True,
            'PayloadVersion': 1,
            }],
        'PayloadIdentifier': BUNDLE,
        'PayloadDisplayName': PROFILE_DISPLAY_NAME,
        'PayloadType': 'Configuration',
        'PayloadScope': 'System',
        'PayloadEnabled': True,
        'PayloadOrganization': args.org_name,
        'PayloadRemovalDisallowed': True
    }

    cert_file = os.path.abspath(args.cert)
    print("Certificate file is: {}".format(cert_file))

    with open(cert_file, 'rb') as f:
        content = f.read()

    # Encode as base64 string or use data type
    if args.base64:
        cert_data = base64.b64encode(content)
    else:
        cert_data = plistlib.Data(content)

    # Include the certificate in the profile
    template['PayloadContent'][0]['cloudfront_certificate'] = cert_data

    # Include the AWS access id if passed through
    if args.access_id:
        template['PayloadContent'][0]['access_id'] = args.access_id

    # Include a custom expire_time if passed through
    if args.expire_after:
        template['PayloadContent'][0]['expire_after'] = args.expire_after

    # Include the alterative domain name if passed through
    if args.domain_name:
        template['PayloadContent'][0]['domain_name'] = args.domain_name

    # Write out the profile to disk
    profile_output = '{}.mobileconfig'.format(PROFILE_FILENAME)
    plistlib.writePlist(template, profile_output)
    print("Profile was written to: {}".format(os.path.abspath(profile_output)))


if __name__ == '__main__':
    main()
