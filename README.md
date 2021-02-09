# What is CloudFront Middleware

CloudFront Middleware enables managed clients to securely access a [munki][0] repo from Amazon's [CloudFront][1] Global Content Delivery Network. CloudFront has lower transit costs than using S3 directly and can offer better performance to managed clients that are outside of an S3 bucket's region.

CloudFront Middleware uses a CloudFront private key to create and sign requests for private CloudFront resources. Each signed request includes an expiration date after which the request is no longer valid.

CloudFront private keys are available from the AWS [Security Credentials][2] dashboard. Each AWS root account can have a maximum of two CloudFront private keys (active or inactive) at a time, allowing for periodic rotation of the private key. It is possible to grant an AWS account [other than the CloudFront distribution owner][3] the ability to sign CloudFront requests.

CloudFront now supports [public key management][9] through IAM user permissions for signed URLs and cookies. This is now the preferred method for signing urls as it has various benefits such as [key groups][10], which are sets of multiple public keys which can be created by IAM users based on permissions you grant, and the ability to manage and rotate public keys via CloudFront's api.

## Requirements

* Customized Munkitools with additional Python modules.
* [Amazon S3][4] bucket with your munki repo inside.
* CloudFront distribution serving this origin with [restricted access][5] to your S3 content.
* CloudFront private key of an AWS account that is a [trusted signer][3] of this CloudFront distribution _OR_
* CloudFront private key of a [key pair][11], of which the public key is added to CloudFront and associated with a [key group][10] allowed access to this CloudFront distribution

## Munki 4 and Python 3

Munki 4 introduces an embedded Python runtime which does not include the same set of Python modules that were available in Python runtimes provided by Apple. To use CloudFront Middleware with Munki 4's embedded Python framework you must rebuild the munkitools installer with additional Python modules and deploy this to your clients.

Additional information about customizing Munki's Python framework is available on the [Munki wiki][8].

CloudFront Middleware 2.0 is backwards compatible with Munki 3.6 and Apple's Python 2.7 runtime. Python 2.7 support will be removed in a future version.

### Adding required modules to Munki's Python

1. Clone [munki/munki][0] locally and change into that directory. (use the `Munki3dev` branch until Munki 4 is released).
2. Append `rsa` to `code/tools/py3_requirements.txt`. It should now look like this:

    ```text
    xattr==0.9.6
    pyobjc==5.1.2
    six
    rsa
    ```

3. Run `code/tools/build_python_framework.sh` to build Munki's Python.framework.
4. Run `code/tools/make_munki_mpkg.sh` to build the munkitools package containing our Python.framework.
5. Install the resulting munkitools package.

### Configure a managed client to access the CloudFront munki repo

1. Install ```middleware_cloudfront.py``` to ```/usr/local/munki/```.
2. Set the munki preference ```SoftwareRepoURL``` to your CloudFront Distribution URL.
3. Set CloudFront Middleware preferences for your Access Key ID and the resource expiration timeout in minutes. If unset expiration will default to 60 minutes.

    ```shell
    sudo defaults write com.github.aaronburchfield.cloudfront access_id -string "YOURACCESSKEYID"
    sudo defaults write com.github.aaronburchfield.cloudfront expire_after -int 30
    ```

4. If you are using an [Alternate Domain Name][6], set the preference for your domain name.

    ```shell
    sudo defaults write com.github.aaronburchfield.cloudfront domain_name -string "munki.megacorp.com"
    ```

5. Install a trusted signer's CloudFront private key and set strict permissions.

    ```shell
    sudo cp pk-YOURACCESSKEYID.pem /usr/local/munki/munkiaccess.pem
    sudo chown root:wheel /usr/local/munki/munkiaccess.pem
    sudo chmod 400 /usr/local/munki/munkiaccess.pem
    ```

6. Run munki and verify that signed CloudFront requests are being made.

    ```shell
    sudo managedsoftwareupdate --checkonly -vvv
    ```

## Packaging CloudFront Middleware

The included [luggage][7] makefile can be used to create an installer package for CloudFront Middleware.

1. With an AWS Root account generate a CloudFront Key Pair, saving the private key as ```munkiaccess.pem``` in the root of this repo.
2. Replace the Access Key ID on line 4 of the **postinstall** script with the ID of your CloudFront Key Pair.
3. ```make pkg``` and install.
4. Set your ```SoftwareRepoURL``` to your CloudFront Distribution address and run munki.

## Configuring with a profile

An alterative to setting values via `defaults` is to use a profile. As of version 1.1, you can now include the CloudFront certificate and all other settings via a profile. This allows easy rotation of the certificate via alterative delivery methods like Mobile Device Management or a configuration management tool. It is still required to drop the `middleware_cloudfront.py` file on disk into the proper directory.

To create a profile use the `create_profile.py` script. See the help menu `--help` for all options. Example usage can be seen below:

```shell
./create_profile.py --cert ~/Desktop/cloudfront.pem --access_id "XXXXXXX" --org_name "Example Org" --desc "Munki CloudFront Settings"
```

[0]: https://github.com/munki/munki
[1]: https://aws.amazon.com/cloudfront/
[2]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#private-content-creating-cloudfront-key-pairs
[3]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html
[4]: https://aws.amazon.com/s3/
[5]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
[6]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CNAMEs.html
[7]: https://github.com/unixorn/luggage
[8]: https://github.com/munki/munki/wiki/About-Munki-4's-Embedded-Python
[9]: https://aws.amazon.com/about-aws/whats-new/2020/10/cloudfront-iam-signed-url/
[10]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#choosing-key-groups-or-AWS-accounts
[11]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#private-content-creating-cloudfront-key-pairs
