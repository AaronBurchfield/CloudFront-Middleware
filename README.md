### What is CloudFront Middleware?
CloudFront Middleware enables managed clients to securely access a [munki][0] repo from Amazon's [CloudFront][1] Global Content Delivery Network. CloudFront has lower transit costs than using S3 directly and can offer better performance to managed clients that are outside of an S3 bucket's region.

CloudFront Middleware uses a CloudFront private key to create and sign requests for private CloudFront resources. Each signed request includes an expiration date after which the request is longer valid.

CloudFront key pairs are available from the AWS [Security Credentials][2] dashboard. Each AWS account can have a maximum of two CloudFront key pairs (active or inactive) at a time, allowing for periodic rotation of the private key. It is possible to grant an AWS account [other than the CloudFront distribution owner][3] the ability to sign CloudFront requests.

#### Requirements
* [Amazon S3][4] bucket with your munki repo inside.
* CloudFront distribution serving this origin with [restricted access][5] to your S3 content.
* CloudFront private key of an AWS account that is a [trusted signer][3] of this CloudFront distribution.

#### Configure a managed client to access the CloudFront munki repo.
1. Install ```middleware_cloudfront.py``` to ```/usr/local/munki/```.
2. Set the munki preference ```SoftwareRepoURL``` to your CloudFront Distribution URL.
3. Set CloudFront Middleware preferences for your Access Key ID and the resource expiration timeout in minutes. If unset expiration will default to 60 minutes.

    ```
    sudo defaults write com.github.aaronburchfield.cloudfront access_id -string "YOURACCESSKEYID"
    sudo defaults write com.github.aaronburchfield.cloudfront expire_after -int 30
    ```
4. If you are using an [Alternate Domain Name][6], set the preference for your domain name.

    ```
    sudo defaults write com.github.aaronburchfield.cloudfront domain_name -string "munki.megacorp.com"
    ```
5. Install a trusted signer's CloudFront private key and set strict permissions.

    ```
    sudo cp pk-YOURACCESSKEYID.pem /usr/local/munki/munkiaccess.pem
    sudo chown root:wheel /usr/local/munki/munkiaccess.pem
    sudo chmod 400 /usr/local/munki/munkiaccess.pem
    ```
6. Run munki and verify that signed CloudFront requests are being made.

    ```
    sudo managedsoftwareupdate --checkonly -vvv
    ```

[0]: https://github.com/munki/munki
[1]: https://aws.amazon.com/cloudfront/
[2]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html#private-content-creating-cloudfront-key-pairs
[3]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-trusted-signers.html
[4]: https://aws.amazon.com/s3/
[5]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
[6]: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/CNAMEs.html
