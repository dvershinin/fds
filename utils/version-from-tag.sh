#!/bin/bash
# TODO integrate to rpmbuilder docker? if there's a tag, build based on that...
# Print what is being run:
set -x

if TAG=$(git describe --exact-match --tags "$(git log -n1 --pretty='%h')" 2>/dev/null); then
  VER=$(echo "${TAG}" | grep --perl-regexp --only-matching '\d+\.\d+\.\d+')
else
  TAG="v0"
  VER=0
fi

PKG=$(basename *.spec .spec)

sed -i "s@Version:.*@Version:        ${VER}@" "${PKG}.spec"

echo "Creating github-like archive from current checkout, for rpmbuild"
# by our convention, the spec file in git has Version: 0, so it will extract to <name>-0
# first create subst like ref-names: HEAD -> master, tag: v0.0.9 in .git_archival.txt
# because we are creating archive ourselves
# Build name is extracted dir name (without v!)
BUILD_NAME="${PKG}-${VER}"
mkdir "/tmp/${BUILD_NAME}"
cp -aRp ./* "/tmp/${BUILD_NAME}/"
echo "ref-names: HEAD -> master, tag: ${TAG}" > "/tmp/${BUILD_NAME}/.git_archival.txt"
pushd /tmp || exit
tar -czvf ./${TAG}.tar.gz "./${BUILD_NAME}"
popd || exit
mv /tmp/${TAG}.tar.gz ./
