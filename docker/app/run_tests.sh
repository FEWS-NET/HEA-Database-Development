#!/bin/bash

echo Compiling translations
python manage.py compilemessages

# Need to create and set permissions on the logs so that we can run as the django user and
# still have permission to write to the logs directory using docker-compose.override.yml
echo Setting up logs
touch log/django.log
chown -R django:django log/*

echo -e "\nChecks:"
gosu django python manage.py check --settings=hea.settings.production --deploy || exit $?
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

# Ignore vulnerability found in gdal version 3.6.2
# @TODO Remove these once the base image includes GDAL>=3.8.0
#   Vulnerability ID: 62283
#     Affected spec: <3.8.0
#     ADVISORY: Gdal 3.8.0 backports a security fix for CVE-2023-45853: MiniZip
#     in zlib through 1.3 has an integer overflow.
#  Vulnerability ID: 74054
#     Affected spec: <3.9.3
#     ADVISORY: Affected versions of GDAL's GMLAS driver are vulnerable
#     to XML Entity Expansion attacks (Billion Laughs attack). This
#     vulnerability can lead to a Denial of Service (DoS) by causing excessive
#     resource consumption when parsing specially crafted XML files with
#     recursive entity definitions. The attack vector involves feeding malicious
#     XML content to the GMLAS driver, exploiting the unlimited entity expansion
#     during parsing. The vulnerability exists in the GMLASReader class's XML
#     parsing functions that lack restrictions on entity expansion. An attacker
#     can exploit this by providing a crafted XML input to any application using
#     the vulnerable GMLAS driver, potentially rendering the application
#     unresponsive. The issue is mitigated by introducing a limit on entity
#     expansions and aborting parsing when the limit is exceeded.
#  Vulnerability ID: 82915
#    Affected spec: <3.12.1
#    ADVISORY: Affected versions of the gdal package are vulnerable to
#    path traversal due to insufficient path sanitization in multiple drivers.

# Ignore vulnerability found in jinja2 version 3.1.4
# We do not allow any untrusted templates, and so are not affected.
#   Vulnerability ID: 70612
#   Affected spec: >=0
#   ADVISORY: In Jinja2, the from_string function is prone to Server
#   Side Template Injection (SSTI) where it takes the "source" parameter as a
#   template object, renders it, and then returns it. The attacker can exploit
#   it with {{INJECTION COMMANDS}} in a URI. NOTE: The maintainer and multiple
#   third parties believe that this vulnerability isn't valid because users
#   shouldn't use untrusted templates without sandboxing.
#   CVE-2019-8341

# Vulnerability found in nbconvert version 7.16.6
#    Vulnerability ID: 83150
#    Affected spec: <=7.16.6
#    ADVISORY: Affected versions of the nbconvert package are
#    vulnerable to Uncontrolled Search Path Element due to resolving the
#    inkscape executable on Windows using a search order that includes the
#    current working directory. In nbconvert/preprocessors/svg2pdf.py, the PDF
#    conversion flow for notebooks with SVG outputs locates and executes
#    inkscape without a fully qualified path, allowing a local inkscape.bat to
#    be selected and run.
# NOTE: jupyterlab==4.4.8 uses nbconvert==7.16.6 and there is currently no patched version 
#  of nbconvert for CVE-2025-53000. 
#  The vulnerability was only published on December 17-18, 2025, and version 7.16.6 remains 
#  the latest release.
#  Will ignore this and update once we got a fix

echo Package Vulnerabilities:
pip freeze | safety check --stdin --full-report -i 62283 -i 70612 -i 74054 -i 82915 -i 83150
SAFETY_RESULT=$?

# Suppress SAFETY_RESULT unless CHECK_SAFETY is set
[ -z "${CHECK_SAFETY}" ] && SAFETY_RESULT=0

# Return the results
exit $(($TEST_RESULT + $SAFETY_RESULT))
