include /usr/local/share/luggage/luggage.make
TITLE=CloudFrontMiddleware
REVERSE_DOMAIN=com.github.aaronburchfield.cloudfrontmiddleware
PACKAGE_VERSION=2.0
PAYLOAD=pack-middleware \
        pack-script-postinstall

pack-middleware:
		@sudo mkdir -p ${WORK_D}/usr/local/munki
		@sudo ${CP} ./middleware_cloudfront.py ${WORK_D}/usr/local/munki
		@sudo ${CP} ./munkiaccess.pem ${WORK_D}/usr/local/munki
		@sudo chown root:wheel ${WORK_D}/usr/local/munki/middleware_cloudfront.py
		@sudo chmod 600 ${WORK_D}/usr/local/munki/middleware_cloudfront.py
		@sudo chown root:wheel ${WORK_D}/usr/local/munki/munkiaccess.pem
		@sudo chmod 400 ${WORK_D}/usr/local/munki/munkiaccess.pem
