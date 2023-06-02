#!/bin/bash

echo Compiling translations
python manage.py compilemessages

# Need to create and set permissions on the logs so that we can run as the django user and
# still have permission to write to the logs directory using docker-compose.override.yml
echo Setting up logs
touch log/django.log
chown -R django:django log/*

echo -e "\nChecks:"
gosu django python manage.py check --settings=fdw.settings.production --deploy || exit $?
echo Check for missing migrations
gosu django python manage.py makemigrations --check --dry-run || exit $?

echo -e "\nTest Results:"
gosu django nice coverage run --branch --parallel-mode \
    --source=apps \
    --omit="*/migrations/*" \
    ./manage.py test --noinput $*
TEST_RESULT=$?

echo Test Coverage:
coverage report --skip-covered

# Also save the full coverage report
coverage report --show-missing >coverage.txt

if [ -z "$CHECK_SAFETY" ]; then
    echo "CHECK_SAFETY not set"
else
    echo "CHECK_SAFETY=${CHECK_SAFETY}"
fi

# Report package vulnerabilities
# Ignore various GDAL issues (42369, 42370, 48545, 51832) as the GDAL version is dependent on the operating system
# @TODO remove the ignore when Debian upgrades to GDAL >= 3.6.0 in the release we are using (currently buster/stable)

# Ignore reportlab vulnerability:
# All versions of package reportlab are vulnerable to Server-side Request
# Forgery (SSRF) via img tags. See CVE-2020-28463. id 39642
# There is no fix for this issue. We don't use <img> tags.
# @TODO look for alternatives

# Ignore spurious dash vulnerability (issue 40962) - see https://github.com/pyupio/safety/issues/349

# Ignore PyJWT error regarding the choice of signing algorithm
# @TODO remove the ignore when djangorestframework-jwt is replaced
# Currently djangorestframework-jwt cannot be updated to drf-jwt due to https://fewsnet.atlassian.net/browse/HELP-471
# 48542 - The PyJWT library requires that the application chooses what algorithms are supported to prevent
# attacks where the agent chooses the signing algorithm.

# Vulnerability found in sqlalchemy version 1.3.22
# @TODO remove the ignore when luigi has a fix
# Vulnerability ID: 51668
# Affected spec: <2.0.0b1
# ADVISORY: Sqlalchemy 2.0.0b1 avoids leaking cleartext passwords to
# the open for careless uses of str(engine.URL()) in logs and prints.
# https://github.com/sqlalchemy/sqlalchemy/pull/8563
# PVE-2022-51668
# For more information, please visit https://pyup.io/v/51668/f17

# Ignore two vulnerabilities in Werkzeug
# @TODO remove this ignores when we unpin Werkzeug after upgrading Dash
# Vulnerability found in werkzeug version 2.0.3
# Vulnerability ID: 53325
# Affected spec: <2.2.3
# ADVISORY: Werkzeug 2.2.3 includes a fix for CVE-2023-25577: Prior to
# version 2.2.3, Werkzeug's multipart form data parser will parse an unlimited
# number of parts, including file parts.
#
# Vulnerability found in werkzeug version 2.0.3
# Vulnerability ID: 53326
# Affected spec: <2.2.3
# ADVISORY: Werkzeug 2.2.3 includes a fix for CVE-2023-23934: Browsers
# may allow "nameless" cookies that look like '=value' instead of 'key=value'.

# Ignore vulnerability in Luigi until upgraded in DATA-2714
# Vulnerability found in luigi version 3.0.3
# Vulnerability ID: 53644
# Affected spec: <3.2.1
# ADVISORY: Luigi 3.2.1 includes a fix for a XSS
# vulnerability.https://github.com/spotify/luigi/pull/3230
# PVE-2023-53644
# For more information, please visit https://pyup.io/v/53644/f17

# Ingore vulnerability in markdown-it-py until upgraded in DATA-2729
# -> Vulnerability found in markdown-it-py version 1.1.0
#    Vulnerability ID: 54650
#    Affected spec: >=0,<2.2.0
#    ADVISORY: Denial of service could be caused to markdown-it-py, before
#    v2.2.0, if an attacker was allowed to force null assertions with specially
#    crafted input.
#    CVE-2023-26303
#    For more information, please visit https://pyup.io/v/54650/f17

# Ingore vulnerability in markdown-it-py until upgraded in DATA-2729
# -> Vulnerability found in markdown-it-py version 1.1.0
#    Vulnerability ID: 54651
#    Affected spec: >=0,<2.2.0
#    ADVISORY: Denial of service could be caused to the command line
#    interface of markdown-it-py, before v2.2.0, if an attacker was allowed to use
#    invalid UTF-8 characters as input.
#    CVE-2023-26302
#    For more information, please visit https://pyup.io/v/54651/f17

# Ignore vulnerability in werkzeug until upgraded in DATA-1463
# -> Vulnerability found in werkzeug version 2.0.3
#    Vulnerability ID: 54456
#    Affected spec: >=0,<2.1.1
#    ADVISORY: ** DISPUTED ** Improper parsing of HTTP requests in Pallets
#    Werkzeug v2.1.0 and below allows attackers to perform HTTP Request Smuggling
#    using a crafted HTTP request with multiple requests included inside the body.
#    NOTE: the vendor's position is that this behavior can only occur in
#    unsupported configurations involving development mode and an HTTP server from
#    outside the Werkzeug project.
#    CVE-2022-29361
#    For more information, please visit https://pyup.io/v/54456/f17

# Ignore the following two vulnerabilites in Wagtail until fixed in DATA-2737
# -> Vulnerability found in wagtail version 2.15.2
#    Vulnerability ID: 54840
#    Affected spec: >=1.5rc1,<4.1.4
#    ADVISORY: Wagtail 4.1.4 and 4.2.2 include a fix for CVE-2023-28836:
#    Starting in version 1.5 and prior to versions 4.1.4 and 4.2.2, a stored
#    cross-site scripting (XSS) vulnerability exists on ModelAdmin views within
#    the Wagtail admin interface. A user with a limited-permission editor account
#    for the Wagtail admin could potentially craft pages and documents that, when
#    viewed by a user with higher privileges, could perform actions with that
#    user's credentials. The vulnerability is not exploitable by an ordinary site
#    visitor without access to the Wagtail admin, and only affects sites with
#    ModelAdmin enabled. For page, the vulnerability is in the "Choose a parent
#    page" ModelAdmin view ('ChooseParentView'), available when managing pages via
#    ModelAdmin. For documents, the vulnerability is in the ModelAdmin Inspect
#    view ('InspectView') when displaying document fields. Patched versions have
#    been released as Wagtail 4.1.4 and Wagtail 4.2.2. Site owners who are unable
#    to upgrade to the new versions can disable or override the corresponding
#    functionality.
#    CVE-2023-28836
#    For more information, please visit https://pyup.io/v/54840/f17

# -> Vulnerability found in wagtail version 2.15.2
#    Vulnerability ID: 54841
#    Affected spec: <4.1.4
#    ADVISORY: Wagtail 4.1.4 and 4.2.2 include a fix for CVE-2023-28837:
#    Prior to versions 4.1.4 and 4.2.2, a memory exhaustion bug exists in
#    Wagtail's handling of uploaded images and documents. For both images and
#    documents, files are loaded into memory during upload for additional
#    processing. A user with access to upload images or documents through the
#    Wagtail admin interface could upload a file so large that it results in a
#    crash of denial of service. The vulnerability is not exploitable by an
#    ordinary site visitor without access to the Wagtail admin. It can only be
#    exploited by admin users with permission to upload images or documents. Image
#    uploads are restricted to 10MB by default, however this validation only
#    happens on the frontend and on the backend after the vulnerable code. Patched
#    versions have been released as Wagtail 4.1.4 and Wagtail 4.2.2). Site owners
#    who are unable to upgrade to the new versions are encouraged to add extra
#    protections outside of Wagtail to limit the size of uploaded files.
#    CVE-2023-28837
#    For more information, please visit https://pyup.io/v/54841/f17

# Ignore vulnerability in django-allauth until fixed in DATA-2738
# -> Vulnerability found in django-allauth version 0.47.0
#    Vulnerability ID: 54809
#    Affected spec: <0.54.0
#    ADVISORY: Django-allauth 0.54.0 includes a security fix: Even when
#    account enumeration prevention was turned on, it was possible for an attacker
#    to infer whether or not a given account exists based upon the response time
#    of an authentication attempt.
#    PVE-2023-54809
#    For more information, please visit https://pyup.io/v/54809/f17

echo Package Vulnerabilities:
pip freeze | safety check --stdin --full-report -i 42369 -i 42370 -i 39642 -i 40962 -i 44715 -i 48545 -i 48542 -i 51668 -i 51832 -i 53325 -i 53326 -i 53644 -i 54650 -i 54651 -i 54456 -i 54840 -i 54841 -i 54809
SAFETY_RESULT=$?

# Suppress SAFETY_RESULT unless CHECK_SAFETY is set
[ -z "${CHECK_SAFETY}" ] && SAFETY_RESULT=0

# Return the results
exit $(($TEST_RESULT + $SAFETY_RESULT))
