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
#     Affected spec: <3.12.1
#     ADVISORY: Affected versions of the gdal package are vulnerable to
#     path traversal due to insufficient path sanitization in multiple drivers.
#  Vulnerability ID: SFTY-20260510-89962
#     Affected spec: <3.13.0RC1
#     ADVISORY: A flaw has been found in OSGeo gdal up to 3.13.0dev-4.
#     Affected by this vulnerability is the function SWSDfldsrch of the file
#     frmts/hdf4/hdf-eos/SWapi.c. Executing a manipulation can lead to heap-
#     based buffer overflow. The attack requires local access. The exploit has
#     been published and may be used.
#   Vulnerability ID: 98069
#     Affected spec: <3.13.0
#     ADVISORY: Affected versions of the GDAL package are vulnerable to
#     a Heap-based Buffer Overflow due to insufficient bounds checking in the
#     GDnentries function within frmts/hdf4/hdf-eos/GDapi.c. Manipulating the
#     DataFieldName argument supplied to this function can cause a write
#     operation to exceed the allocated heap buffer boundaries. A local attacker
#     with low-level privileges who can supply a malicious HDF-EOS file to a
#     process using GDAL can trigger this overflow, potentially resulting in
#     memory corruption, disclosure of sensitive data, or code execution.
#   Vulnerability ID: 98070
#     Affected spec: <3.13.0
#     ADVISORY: Affected versions of the GDAL package are vulnerable to
#     an Out-of-bounds Read due to insufficient validation in the GDfieldinfo
#     function within frmts/hdf4/hdf-eos/GDapi.c. A manipulated input to this
#     function can cause a read operation to access memory outside the intended
#     buffer boundaries. A local attacker can supply a crafted HDF-EOS dataset
#     to trigger this out-of-bounds read, resulting in a partial Denial of
#     Service through abnormal process termination.
#   Vulnerability ID: SFTY-20260527-29918
#     Affected spec: >=3.1.0,<3.13.1
#     ADVISORY: In GDAL 3.1.0 through 3.13.0, scanForGeometryContainers
#     in the netCDF driver allows code execution via a stack-based buffer
#     overflow. It reads a geometry attribute into a fixed-size stack buffer
#     without validating the attribute length. The attacker embeds the exploit
#     as an oversized geometry attribute in a crafted NetCDF file. This achieves
#     arbitrary code execution on the server running GDAL. This is in
#     frmts/netcdf/netcdfsg.cpp.
#     CVE-2026-49014

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

# Vulnerability found in nltk version 3.10.3
#  Vulnerability ID: SFTY-20260902-58666
#  Affected spec: <=3.10.3
#  ADVISORY: Affected versions of the NLTK package are vulnerable to
#  Path Traversal due to the use of built-in `open()` on caller-controlled
#  paths instead of pathsec-aware helpers. The `TransitionParser.train`,
#  `TransitionParser.parse`, `AveragedPerceptron.save`,
#  `AveragedPerceptron.load`, `PerceptronTagger.save_to_json`, and
#  `save_maxent_params` methods bypass path security checks, allowing file
#  operations on paths outside the allowed roots. An attacker can exploit
#  this vulnerability by providing paths that escape the designated sandbox,
#  potentially leading to unauthorized file reads or writes on the host
#  system.
# NOTE: nltk is a dependency of Safety only - it isn't part of the main image.

# Vulnerabilities found in filelock version 3.32.7
#   Vulnerability IDs: SFTY-20261023-16869, SFTY-20261023-24590
#   CVE-2026-112940, CVE-2026-112913: ReadWriteLock path races; Safety and Dagster only use plain FileLock.
#   Vulnerability ID: SFTY-20261023-10299
#   CVE-2026-112907: Windows soft-lock oplock hang; our containers run Linux.
#   Vulnerability IDs: SFTY-20261017-72390, SFTY-20261017-54654, SFTY-20261017-57659
#   Affected spec: <=4.2.0
#   CVE-2026-112910: FileLock ignores `mode` on Windows - our containers run Linux.
#   CVE-2026-112908, CVE-2026-112938: StrictSoftFileLock claim directory permissions and
#   symlink race - dagster only uses plain FileLock.
#   Vulnerability IDs: SFTY-20261020-34461, SFTY-20261020-18367, SFTY-20261020-13394,
#   SFTY-20261020-91319, SFTY-20261020-25530, SFTY-20261020-11422
#   CVE-2026-112912, CVE-2026-112915, CVE-2026-112935, CVE-2026-112939, CVE-2026-112911,
#   CVE-2026-112936: SoftFileLock, MarkerSoftFileLock, SoftFileLease, StrictSoftFileLock and
#   (Async)ReadWriteLock - dagster and Safety only use plain FileLock.
#   Vulnerability ID: SFTY-20261020-81101
#   CVE-2026-112909: UnixFileLock, the backend of FileLock, truncates a file renamed or
#   hard-linked onto the lock path - needs another local user in the container, which runs
#   only our own processes.
# NOTE: filelock 3.x is forced by Safety itself (safety<=3.8.1 requires filelock<4.0), so no
#  patched version can be installed alongside it. The prod image doesn't install Safety and
#  gets the latest filelock through dagster. Remove these ignores once a Safety release
#  allows filelock>=4.2.1.

echo Package Vulnerabilities:
pip freeze | safety check --stdin --full-report -i 62283 -i 70612 -i 74054 -i 82915 -i 83150 -i SFTY-20260510-89962 -i 98069 -i 98070 -i SFTY-20260527-29918 -i SFTY-20260902-58666 -i SFTY-20261017-72390 -i SFTY-20261017-54654 -i SFTY-20261017-57659 -i SFTY-20261020-34461 -i SFTY-20261020-18367 -i SFTY-20261020-13394 -i SFTY-20261020-91319 -i SFTY-20261020-81101 -i SFTY-20261020-25530 -i SFTY-20261020-11422 -i SFTY-20261023-16869 -i SFTY-20261023-24590 -i SFTY-20261023-10299
SAFETY_RESULT=$?

# Suppress SAFETY_RESULT unless CHECK_SAFETY is set
[ -z "${CHECK_SAFETY}" ] && SAFETY_RESULT=0

# Return the results
exit $(($TEST_RESULT + $SAFETY_RESULT))
