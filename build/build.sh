#!/usr/bin/env bash
#
# Build AWX container image from AAP 2.6.5 open-source sources.
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
AWX_COMMIT="03140796f620966cdc4ff5052978c80a51c94ca7"
AWX_LOGOS_REPO="https://github.com/ansible/awx-logos.git"
AWX_LOGOS_COMMIT="bae4e6cfd16f5e7b814ed873a2fef68b6d90a354"
AWX_LOGOS_DIR="${AWX_LOGOS_DIR:-${SCRIPT_DIR}/awx-logos}"
AAP_UI_SRPM_URL="https://ftp.redhat.com/redhat/linux/enterprise/9Base/en/AnsibleAutomationPlatform/SRPMS/automation-platform-ui-2.6.5-1.el9ap.src.rpm"
AAP_UI_SRPM_DIR="${AAP_UI_SRPM_DIR:-${SCRIPT_DIR}/aap-ui-srpm}"
AAP_UI_TARBALL_GLOB="aap-ui-*.tar.gz"
AAP_UI_DIR="${AAP_UI_DIR:-${SCRIPT_DIR}/aap-ui}"
# Python package version — must be PEP 440 compliant (no hyphens).
# .post330 = 330 commits past the last public release 24.6.1
VERSION="${VERSION:-24.6.1.post330}"
IMAGE_NAME="${IMAGE_NAME:-quay.io/tadas/awx}"
# Docker image tag — can use any format
IMAGE_TAG="${IMAGE_TAG:-$VERSION}"
BUILD_DIR="${BUILD_DIR:-${SCRIPT_DIR}/awx-src}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
BUILDER_NAME="awx-multiarch"

# Pre-flight: check required tools
for cmd in git curl docker rpm2cpio cpio; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' is required but not found in PATH."
        echo "  On macOS: brew install rpm2cpio"
        echo "  On Debian/Ubuntu: apt install rpm2cpio cpio"
        echo "  On RHEL/Fedora: dnf install rpm cpio"
        exit 1
    fi
done

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

echo "=== AWX Rebuild from AAP 2.6.5 sources ==="
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
# 1. Clone AWX at the AAP 2.6.5 commit
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
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 2. Fetch official AWX branding assets (logos, favicons)
#    The repo ships "angry potato" dev logos. Official AWX releases use
#    assets from ansible/awx-logos.
# -------------------------------------------------------------------
echo "=> Fetching official AWX logos from ${AWX_LOGOS_REPO} @ ${AWX_LOGOS_COMMIT}..."
if [ ! -d "${AWX_LOGOS_DIR}" ]; then
    git clone "${AWX_LOGOS_REPO}" "${AWX_LOGOS_DIR}"
fi
cd "${AWX_LOGOS_DIR}" && git fetch origin && git checkout "${AWX_LOGOS_COMMIT}" && cd "${BUILD_DIR}"
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 3. Fix requirements_git.txt (replace private SSH URLs with public HTTPS)
# -------------------------------------------------------------------
echo "=> Patching requirements_git.txt..."
cat > requirements/requirements_git.txt << 'REQUIREMENTS_GIT'
certifi @ git+https://github.com/ansible/system-certifi.git@5aa52ab91f9d579bfe52b5acf30ca799f1a563d9
python3-saml @ git+https://github.com/ansible/python3-saml.git@f90824c4910e36c5a89dd295271be26691204ba3
django-ansible-base[feature-flags,jwt-consumer,rbac,resource-registry,rest-filters] @ git+https://github.com/ansible/django-ansible-base.git@f60bf1e40832edee49832f1ce6f836e65c130b1d
kubernetes @ git+https://github.com/kubernetes-client/python.git@df31d90d6c910d6b5c883b98011c93421cac067d
REQUIREMENTS_GIT
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 4. Patch CVEs — bump safe dependencies (patch/minor within same major)
#    Only packages where the upgrade is backward-compatible.
#    DO NOT bump: cryptography (42→46 breaking), protobuf (4→5 breaking)
# -------------------------------------------------------------------
echo "=> Patching requirements.txt for CVE fixes..."
REQFILE="requirements/requirements.txt"

# Cross-platform sed in-place (macOS needs -i '', GNU/Linux needs -i)
sedi() { if sed --version >/dev/null 2>&1; then sed -i "$@"; else sed -i '' "$@"; fi; }

# Critical + High: Django 4.2.27 → 4.2.29 (LTS patch, SQLi/DoS fixes)
sedi 's/^django==4.2.27$/django==4.2.29/' "$REQFILE"

# High: wheel 0.42.0 → 0.46.2 (path traversal)
sedi 's/^wheel==0.42.0$/wheel==0.46.2/' "$REQFILE"

# Medium: python-ldap 3.4.4 → 3.4.5 (filter escape bypass)
sedi 's/^python-ldap==3.4.4$/python-ldap==3.4.5/' "$REQFILE"

# Medium: sqlparse 0.5.3 → 0.5.5 (Django dependency)
sedi 's/^sqlparse==0.5.3$/sqlparse==0.5.5/' "$REQFILE"

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

# Medium: msal 1.26.0 → 1.28.0 (privilege escalation CVE-2024-35255)
sedi 's/^msal==1.26.0$/msal==1.28.0/' "$REQFILE"

# High: azure-core 1.30.0 → 1.38.0 (GHSA-jm66-cg57-jjv5)
# All azure-* packages require azure-core>=1.23.0,<2.0.0 — compatible.
sedi 's/^azure-core==1.30.0$/azure-core==1.38.0/' "$REQFILE"

echo "   Patched $(grep -c '==' "$REQFILE") packages in requirements.txt"
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 5. Patch AWX metadata to expose content_type choices for role_definitions
#    The new UI (aap-ui) fetches OPTIONS /api/v2/role_definitions/ and reads
#    actions.GET.content_type.choices to populate the "Resource type" dropdown.
#    AWX's Metadata class skips choices for RelatedField subclasses (by design),
#    but DAB's RoleDefinitionSerializer uses SlugRelatedField for content_type.
#    We patch get_field_info() to add choices for SlugRelatedField fields whose
#    queryset is DABContentType.
# -------------------------------------------------------------------
echo "=> Patching metadata.py to expose content_type choices..."
python3 -c "
f = 'awx/api/metadata.py'
content = open(f).read()

# Add import for DABContentType at the top of the file (after existing imports)
import_line = 'from ansible_base.rbac.models import DABContentType'
if import_line not in content:
    # Insert after the last 'from ansible_base' import or before 'from awx'
    import_anchor = 'from awx.'
    idx = content.index(import_anchor)
    content = content[:idx] + import_line + '\n' + content[idx:]

# Patch get_field_info to add choices for SlugRelatedField with DABContentType queryset
old = '''        if not isinstance(field, (RelatedField, ManyRelatedField)) and hasattr(field, 'choices'):'''
new = '''        # Expose content_type choices for DAB RBAC SlugRelatedField (needed by ui_next)
        if isinstance(field, RelatedField) and hasattr(field, 'get_queryset'):
            qs = field.get_queryset()
            if qs is not None and qs.model is DABContentType:
                field_info['choices'] = [
                    (ct.api_slug, ct.model_class()._meta.verbose_name.title())
                    for ct in qs if ct.model_class() is not None
                ]

        if not isinstance(field, (RelatedField, ManyRelatedField)) and hasattr(field, 'choices'):'''

content = content.replace(old, new, 1)
open(f, 'w').write(content)
"
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 6. Prepare AAP UI source for Vite build (Apache-2.0 licensed)
#    Downloads the AAP Platform UI SRPM, extracts the aap-ui tarball,
#    and unpacks it for the Vite build. Replaces old CRA/webpack UI.
# -------------------------------------------------------------------
echo "=> Preparing AAP UI source for Vite build..."
if [ ! -d "${AAP_UI_DIR}" ]; then
    # Download SRPM if not cached
    mkdir -p "${AAP_UI_SRPM_DIR}"
    SRPM_FILE="${AAP_UI_SRPM_DIR}/$(basename "${AAP_UI_SRPM_URL}")"
    if [ ! -f "${SRPM_FILE}" ]; then
        echo "   Downloading AAP UI SRPM..."
        curl -fSL -o "${SRPM_FILE}" "${AAP_UI_SRPM_URL}"
    fi
    # Extract SRPM contents (uses rpm2cpio + cpio)
    echo "   Extracting SRPM..."
    cd "${AAP_UI_SRPM_DIR}" && rpm2cpio "${SRPM_FILE}" | cpio -idm --quiet 2>/dev/null
    # Find the aap-ui source tarball inside the extracted SRPM
    AAP_UI_TARBALL=$(ls ${AAP_UI_SRPM_DIR}/${AAP_UI_TARBALL_GLOB} 2>/dev/null | head -1)
    if [ -z "${AAP_UI_TARBALL}" ]; then
        echo "   ERROR: Could not find ${AAP_UI_TARBALL_GLOB} in SRPM contents"
        exit 1
    fi
    echo "   Found: $(basename "${AAP_UI_TARBALL}")"
    # Unpack the aap-ui source
    mkdir -p "${AAP_UI_DIR}"
    tar xzf "${AAP_UI_TARBALL}" -C "${AAP_UI_DIR}" --strip-components=1
    cd "${BUILD_DIR}"
fi
# Copy AWX logo assets into the frontend build source
cp "${AWX_LOGOS_DIR}/awx/ui/client/assets/logo-login.svg" "${AAP_UI_DIR}/frontend/assets/awx-logo.svg" 2>/dev/null || true
cp "${AWX_LOGOS_DIR}/awx/ui/client/assets/favicon.ico" "${AAP_UI_DIR}/frontend/awx/favicon.ico" 2>/dev/null || true
cp "${AWX_LOGOS_DIR}/awx/ui/client/assets/favicon.svg" "${AAP_UI_DIR}/frontend/assets/awx-icon.svg" 2>/dev/null || true
# Replace the angry potato icon in Vite's public/ dir — Vite copies public/ files
# directly to dist/, so this is what browsers load via <link rel="icon" href="/awx-icon.svg">
cp "${AWX_LOGOS_DIR}/awx/ui/client/assets/favicon.svg" "${AAP_UI_DIR}/frontend/awx/public/awx-icon.svg" 2>/dev/null || true
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 7. Make the new UI the default (replace old CRA/webpack UI)
#    Note: working directory must be BUILD_DIR for relative paths below.
#    - Patch the old UI's IndexView to serve index_awx.html (Vite build)
#    - Re-add ui_next to STATICFILES_DIRS so collectstatic picks it up
#    - Copy AWX logos into the static media dir for fallback
#    Note: This commit already has ui_next in TEMPLATES['DIRS'] and UI_NEXT=True
#    in defaults.py, but STATICFILES_DIRS still needs the entry.
# -------------------------------------------------------------------
echo "=> Patching AWX to serve new UI as default..."
cd "${BUILD_DIR}"

# 7a. Make the root IndexView serve the Vite-built index_awx.html
sedi "s/template_name = 'index.html'/template_name = 'index_awx.html'/" awx/ui/urls.py

# 7b. Fix STATICFILES_DIRS:
#     - Ensure ui_next entry exists (for collectstatic to pick up Vite assets)
#     - Remove old UI 'ui/build/static' entry (we don't build the old CRA UI,
#       so this path doesn't exist at runtime → Django W004 warning)
python3 -c "
f = 'awx/settings/defaults.py'
content = open(f).read()
marker = \"('awx', os.path.join(BASE_DIR, 'ui_next', 'build', 'awx'))\"
if marker not in content:
    old = 'STATICFILES_DIRS = ['
    new = \"\"\"STATICFILES_DIRS = [
    ('awx', os.path.join(BASE_DIR, 'ui_next', 'build', 'awx')),\"\"\"
    content = content.replace(old, new, 1)
# Remove old CRA/webpack UI static dir (no longer built)
content = content.replace(\"    os.path.join(BASE_DIR, 'ui', 'build', 'static'),\n\", '')
open(f, 'w').write(content)
"

# 7c. Copy official AWX logos into static media (for old UI fallback paths)
cp "${AWX_LOGOS_DIR}/awx/ui/client/assets/"* awx/ui/public/static/media/

echo "   Done."
echo ""

# -------------------------------------------------------------------
# 8. Ensure credentials file is clean (no actual credentials)
# -------------------------------------------------------------------
echo "=> Cleaning requirements_git.credentials.txt..."
cat > requirements/requirements_git.credentials.txt << 'CREDENTIALS'
CREDENTIALS
echo "   Done."
echo ""

# -------------------------------------------------------------------
# 9. Create _build/ directory with rendered configs
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
# 10. Ensure aap-ui is inside the Docker build context
#     AAP_UI_DIR may live outside BUILD_DIR for caching; Docker COPY
#     requires it inside the context.
# -------------------------------------------------------------------
if [ "$(cd "${AAP_UI_DIR}" && pwd)" != "$(cd "${BUILD_DIR}/aap-ui" 2>/dev/null && pwd)" ]; then
    echo "=> Copying aap-ui into Docker build context..."
    rm -rf "${BUILD_DIR}/aap-ui"
    cp -a "${AAP_UI_DIR}" "${BUILD_DIR}/aap-ui"
    echo "   Done."
    echo ""
fi

# -------------------------------------------------------------------
# 11. Build the container image
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
