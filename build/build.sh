#!/usr/bin/env bash
#
# Build AWX container image from AAP 2.6.1 open-source sources.
#
# Usage:
#   ./build.sh                                     # Build for local platform
#   ./build.sh --platform linux/arm64              # Build specific arch locally
#   ./build.sh --push                              # Build multiarch (amd64+arm64) and push
#   ./build.sh --no-cache                          # Force full rebuild (no Docker cache)
#   PLATFORMS=linux/amd64 ./build.sh --push        # Push single arch to registry
#   VERSION=24.7.0 ./build.sh                      # Custom version
#   IMAGE_NAME=my-registry/awx ./build.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

AWX_REPO="https://github.com/ansible/awx.git"
AWX_COMMIT="05626248ce26fda2d64f311e494cfd146e7e4f2e"
# Python package version — must be PEP 440 compliant (no hyphens).
# .post281 = 281 commits past the last public release 24.6.1
VERSION="${VERSION:-24.6.1.post281}"
IMAGE_NAME="${IMAGE_NAME:-quay.io/tadas/awx}"
# Docker image tag — can use any format
IMAGE_TAG="${IMAGE_TAG:-$VERSION}"
BUILD_DIR="${BUILD_DIR:-${SCRIPT_DIR}/awx-src}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
BUILDER_NAME="awx-multiarch"

PUSH=false
LOCAL_PLATFORM=""
NO_CACHE=false
while [ $# -gt 0 ]; do
    case "$1" in
        --push) PUSH=true ;;
        --platform) LOCAL_PLATFORM="$2"; shift ;;
        --no-cache) NO_CACHE=true ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
    shift
done

echo "=== AWX Rebuild from AAP 2.6.1 sources ==="
echo "  Commit:    ${AWX_COMMIT}"
echo "  Version:   ${VERSION}"
echo "  Image:     ${IMAGE_NAME}:${IMAGE_TAG}"
if [ "${PUSH}" = true ]; then
    echo "  Platforms: ${PLATFORMS}"
elif [ -n "${LOCAL_PLATFORM}" ]; then
    echo "  Platform:  ${LOCAL_PLATFORM}"
else
    echo "  Platform:  (native)"
fi
echo "  Push:      ${PUSH}"
echo "  No cache:  ${NO_CACHE}"
echo ""

# -------------------------------------------------------------------
# 1. Clone AWX at the AAP 2.6.1 commit
# -------------------------------------------------------------------
if [ -d "${BUILD_DIR}" ]; then
    echo "=> Build directory already exists: ${BUILD_DIR}"
    echo "   Remove it to force a fresh clone, or reusing existing checkout."
    cd "${BUILD_DIR}"
    CURRENT_COMMIT="$(git rev-parse HEAD)"
    if [ "${CURRENT_COMMIT}" != "${AWX_COMMIT}" ]; then
        echo "   WARNING: Current commit ${CURRENT_COMMIT} differs from target ${AWX_COMMIT}"
        echo "   Fetching and checking out target commit..."
        git fetch origin "${AWX_COMMIT}"
        git checkout FETCH_HEAD
    fi
else
    echo "=> Cloning AWX repository..."
    git clone "${AWX_REPO}" "${BUILD_DIR}"
    cd "${BUILD_DIR}"
    # The target commit is not on any default branch, so fetch it explicitly
    echo "=> Fetching target commit..."
    git fetch origin "${AWX_COMMIT}"
    git checkout FETCH_HEAD
fi
echo ""

# -------------------------------------------------------------------
# 2. Fix requirements_git.txt (replace private SSH URLs with public HTTPS)
# -------------------------------------------------------------------
echo "=> Patching requirements_git.txt..."
cat > requirements/requirements_git.txt << 'REQUIREMENTS_GIT'
certifi @ git+https://github.com/ansible/system-certifi.git@devel
python3-saml @ git+https://github.com/ansible/python3-saml.git@f90824c4910e36c5a89dd295271be26691204ba3
django-ansible-base[feature-flags,jwt-consumer,rbac,resource-registry,rest-filters] @ git+https://github.com/ansible/django-ansible-base.git@b8fe0b5c855686138f8ec27b1e69a944e4db4d44
REQUIREMENTS_GIT
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 3. Patch CVEs — bump safe dependencies (patch/minor within same major)
#    Only packages where the upgrade is backward-compatible.
#    DO NOT bump: urllib3 (v1→v2 breaking), cryptography (42→46 breaking),
#                 protobuf (4→5 breaking), pip/wheel (build-time only)
# -------------------------------------------------------------------
echo "=> Patching requirements.txt for CVE fixes..."
REQFILE="requirements/requirements.txt"

# Cross-platform sed in-place (macOS needs -i '', GNU/Linux needs -i)
sedi() { if sed --version >/dev/null 2>&1; then sed -i "$@"; else sed -i '' "$@"; fi; }

# Critical + High: Django 4.2.24 → 4.2.28 (LTS patch, 1 critical + 4 high SQLi/DoS)
sedi 's/^django==4.2.24$/django==4.2.28/' "$REQFILE"

# High: brotli 1.1.0 → 1.2.0 (DoS in decompression)
sedi 's/^brotli==1.1.0$/brotli==1.2.0/' "$REQFILE"

# High: wheel 0.42.0 → 0.46.2 (path traversal)
sedi 's/^wheel==0.42.0$/wheel==0.46.2/' "$REQFILE"

# Medium: python-ldap 3.4.4 → 3.4.5 (filter escape bypass)
sedi 's/^python-ldap==3.4.4$/python-ldap==3.4.5/' "$REQFILE"

# Medium: sqlparse 0.5.3 → 0.5.4 (Django dependency)
sedi 's/^sqlparse==0.5.3$/sqlparse==0.5.4/' "$REQFILE"

# Medium: requests 2.32.3 → 2.32.4
sedi 's/^requests==2.32.3$/requests==2.32.4/' "$REQFILE"

# Medium: jwcrypto 1.5.4 → 1.5.6
sedi 's/^jwcrypto==1.5.4$/jwcrypto==1.5.6/' "$REQFILE"

# Medium: zipp 3.17.0 → 3.19.1 (DoS)
sedi 's/^zipp==3.17.0$/zipp==3.19.1/' "$REQFILE"

# Medium: filelock 3.13.1 → 3.20.3 (TOCTOU symlink)
sedi 's/^filelock==3.13.1$/filelock==3.20.3/' "$REQFILE"

# Medium: azure-identity 1.15.0 → 1.16.1 (privilege escalation)
sedi 's/^azure-identity==1.15.0$/azure-identity==1.16.1/' "$REQFILE"

# Medium: pycares 4.5.0 → 4.9.0 (use-after-free)
sedi 's/^pycares==4.5.0$/pycares==4.9.0/' "$REQFILE"

# Medium: msal 1.26.0 → 1.28.0 (privilege escalation CVE-2024-35255)
sedi 's/^msal==1.26.0$/msal==1.28.0/' "$REQFILE"

echo "   Patched $(grep -c '==' "$REQFILE") packages in requirements.txt"
echo ""

# -------------------------------------------------------------------
# 4. Fix UI settings mismatch (SUBSCRIPTIONS_USERNAME/PASSWORD → CLIENT_ID/SECRET)
#    Backend registers SUBSCRIPTIONS_CLIENT_ID/CLIENT_SECRET but UI references
#    SUBSCRIPTIONS_USERNAME/PASSWORD, causing TypeError on Settings > Misc System.
# -------------------------------------------------------------------
echo "=> Fixing UI settings field names..."
UI_DETAIL="awx/ui/src/screens/Setting/MiscSystem/MiscSystemDetail/MiscSystemDetail.js"
UI_EDIT="awx/ui/src/screens/Setting/MiscSystem/MiscSystemEdit/MiscSystemEdit.js"
for f in "$UI_DETAIL" "$UI_EDIT"; do
    sedi 's/SUBSCRIPTIONS_USERNAME/SUBSCRIPTIONS_CLIENT_ID/g' "$f"
    sedi 's/SUBSCRIPTIONS_PASSWORD/SUBSCRIPTIONS_CLIENT_SECRET/g' "$f"
done
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 5. Replace dev logos with official AWX branding
#    The repo ships "angry potato" dev logos. Official AWX releases use
#    assets from ansible/awx-logos.
# -------------------------------------------------------------------
echo "=> Fetching official AWX logos from ansible/awx-logos..."
AWX_LOGOS_DIR="${SCRIPT_DIR}/.awx-logos"
if [ ! -d "${AWX_LOGOS_DIR}" ]; then
    git clone --depth 1 https://github.com/ansible/awx-logos.git "${AWX_LOGOS_DIR}"
fi
cp "${AWX_LOGOS_DIR}/awx/ui/client/assets/"* awx/ui/public/static/media/
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 6. Ensure credentials file is clean (no actual credentials)
# -------------------------------------------------------------------
echo "=> Cleaning requirements_git.credentials.txt..."
cat > requirements/requirements_git.credentials.txt << 'CREDENTIALS'
CREDENTIALS
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 7. Create _build/ directory with rendered configs
# -------------------------------------------------------------------
echo "=> Installing rendered configs into _build/..."
mkdir -p _build
cp "${SCRIPT_DIR}/supervisor_web.conf" _build/supervisor_web.conf
cp "${SCRIPT_DIR}/supervisor_task.conf" _build/supervisor_task.conf
cp "${SCRIPT_DIR}/supervisor_rsyslog.conf" _build/supervisor_rsyslog.conf
cp "${SCRIPT_DIR}/nginx.conf" _build/nginx.conf
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 8. Build the container image
# -------------------------------------------------------------------
BUILDX_ARGS=(
    -f "${SCRIPT_DIR}/Dockerfile"
    --build-arg VERSION="${VERSION}"
    --build-arg SETUPTOOLS_SCM_PRETEND_VERSION="${VERSION}"
    -t "${IMAGE_NAME}:${IMAGE_TAG}"
)

if [ "${NO_CACHE}" = true ]; then
    BUILDX_ARGS+=(--no-cache)
fi

if [ "${PUSH}" = true ]; then
    # Multiarch build + push requires a buildx builder with multi-platform support
    echo "=> Ensuring buildx builder '${BUILDER_NAME}' exists..."
    if ! docker buildx inspect "${BUILDER_NAME}" &>/dev/null; then
        docker buildx create --name "${BUILDER_NAME}" --driver docker-container --use
    else
        docker buildx use "${BUILDER_NAME}"
    fi

    echo "=> Building multiarch image and pushing to registry..."
    docker buildx build "${BUILDX_ARGS[@]}" \
        --platform "${PLATFORMS}" \
        --push \
        .
elif [ -n "${LOCAL_PLATFORM}" ]; then
    # Local build for a specific platform (e.g. linux/arm64 on amd64 host)
    echo "=> Building image for ${LOCAL_PLATFORM} (local)..."
    DOCKER_BUILDKIT=1 docker buildx build "${BUILDX_ARGS[@]}" \
        --platform "${LOCAL_PLATFORM}" \
        --load \
        .
else
    # Local build for native platform
    echo "=> Building container image for local use..."
    DOCKER_BUILDKIT=1 docker build "${BUILDX_ARGS[@]}" .
fi

echo ""
echo "=== Build complete ==="
echo "  Image: ${IMAGE_NAME}:${IMAGE_TAG}"
if [ "${PUSH}" = true ]; then
    echo "  Platforms: ${PLATFORMS}"
    echo "  Pushed to registry."
else
    echo ""
    echo "  Quick test:"
    echo "    docker run --rm -e AWX_MODE=defaults -e SKIP_SECRET_KEY_CHECK=yes -e SKIP_PG_VERSION_CHECK=yes ${IMAGE_NAME}:${IMAGE_TAG} awx-manage version"
    echo ""
    echo "  To build multiarch and push:"
    echo "    ./build.sh --push"
fi
