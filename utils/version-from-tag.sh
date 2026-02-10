#!/bin/bash
# TODO integrate to rpmbuilder docker? if there's a tag, build based on that...
# Print what is being run:
set -x

PKG=$(basename *.spec .spec)

if TAG=$(git describe --exact-match --tags "$(git log -n1 --pretty='%h')" 2>/dev/null); then
  VER=$(echo "${TAG}" | grep --perl-regexp --only-matching '\d+\.\d+\.\d+')
  sed -i "s@Version:.*@Version:        ${VER}@" "${PKG}.spec"
else
  # For non-tagged builds, use the version from spec file (don't reset to 0)
  VER=$(awk '/^Version:/ {print $2}' "${PKG}.spec")
  TAG="v${VER}"
fi

echo "Creating github-like archive from current checkout, for rpmbuild"
# The spec file in git has a version number, tagged builds update it from the tag
# first create subst like ref-names: HEAD -> master, tag: v0.0.9 in .git_archival.txt
# because we are creating archive ourselves
# Build name is extracted dir name (without v!)
BUILD_NAME="${PKG}-${VER}"
mkdir "/tmp/${BUILD_NAME}"
cp -aRp ./* "/tmp/${BUILD_NAME}/"
# Create .git_archival.txt with format expected by setuptools_scm 6.0+
NODE=$(git rev-parse HEAD)
NODE_DATE=$(git log -1 --format=%cI)
cat > "/tmp/${BUILD_NAME}/.git_archival.txt" << EOF
node: ${NODE}
node-date: ${NODE_DATE}
describe-name: ${TAG}
ref-names: HEAD -> master, tag: ${TAG}
EOF
pushd /tmp || exit
tar -czvf ./${TAG}.tar.gz "./${BUILD_NAME}"
popd || exit
mv /tmp/${TAG}.tar.gz ./
