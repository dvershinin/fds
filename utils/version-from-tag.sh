#!/bin/bash
# TODO integrate to rpmbuilder docker? if there's a tag, build based on that...
# Print what is being run:
set -x

TAG=$(git describe --exact-match --tags $(git log -n1 --pretty='%h') 2>/dev/null ||:)
PKG=$(basename *.spec .spec)

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
    echo "Not a tag checkout. Create github-like archive from current checkout, for rpmbuild to pick that instead of v0.0.1 tag in spec"
    # by our convention, the spec file in git has Version: 0, so it will extract to <name>-0
    BUILD_NAME="${PKG}-0"
    mkdir "/tmp/${BUILD_NAME}"
    cp -aRp ./* "/tmp/${BUILD_NAME}/"
    echo "ref-names: HEAD -> master, tag: ${TAG}" > "/tmp/${BUILD_NAME}/.git_archival.txt"
    pushd /tmp || exit
    tar -czvf ./v0.tar.gz "./${BUILD_NAME}"
    popd || exit
    mv /tmp/v0.tar.gz ./
fi