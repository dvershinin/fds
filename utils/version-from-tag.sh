#!/bin/bash
# TODO integrate to rpmbuilder docker? if there's a tag, build based on that...
# Print what is being run:
set -x

TAG=$(git describe --exact-match --tags $(git log -n1 --pretty='%h') 2>/dev/null ||:)

# If tag looks like a semantic version, then replace version in the spec file
if $(echo ${TAG} | grep --silent --perl-regexp '^v?\d+\.\d+\.\d+$'); then
    VER=$(echo ${TAG} | grep --perl-regexp --only-matching '\d+\.\d+\.\d+')
    if [[ $# -eq 0 ]]; then
        echo "No arguments supplied, replacing in *.spec"
        sed -i "s@Version:.*@Version:        ${VER}@" *.spec
    else
        sed -i "s@Version:.*@Version:        ${VER}@" $1
    fi
else
    echo "Not a tag checkout"
fi

# compile :)
yum -y install shc
# generate executable that will refuse to launch in 3 months from now
shc -v -r -e $(date --date='+6 month' +%d/%m/%Y) -m "Please upgrade clearmage2 package from the GetPageSpeed.com/redhat repository" -f clearmage2.sh
# replace the script with compiled one
mv -f clearmage2.sh.x clearmage2.sh