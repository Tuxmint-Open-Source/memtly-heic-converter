# syntax=docker/dockerfile:1.7

ARG SOURCE_IMAGE=alpine/git:2.49.1@sha256:c0280cf9572316299b08544065d3bf35db65043d5e3963982ec50647d2746e26
ARG NODE_IMAGE=node:22.23.2-bookworm-slim@sha256:d649c27dae7ba0137b3cef5dd75baa422c08dc3d9e3fc0c23dfb172dc3cc6436
ARG SDK_IMAGE=mcr.microsoft.com/dotnet/sdk:10.0@sha256:e1ffd2a92ae84c1291bc1b6887501f8af98e6331e7af6d4c8d37168c5e87a64c
ARG RUNTIME_IMAGE=mcr.microsoft.com/dotnet/aspnet:10.0@sha256:a4556ed033fa96f984bb7a8d348851cb2d36b1281dd2420070045f664fbb5f94

FROM ${SOURCE_IMAGE} AS source
ARG MEMTLY_COMMUNITY_TAG=1.0.6
ARG MEMTLY_COMMUNITY_COMMIT=d9b7298866c8cafbd515a6bf5e260e1d0423f262
ARG MEMTLY_CORE_COMMIT=cc8c88d625136f04ae1f1063fc635f74e739bd72
COPY patches /overlay/patches
RUN set -eux; \
    git clone --filter=blob:none --no-checkout https://github.com/Memtly/Memtly.Community.git /src; \
    cd /src; \
    git fetch --depth 1 origin "refs/tags/${MEMTLY_COMMUNITY_TAG}:refs/tags/${MEMTLY_COMMUNITY_TAG}"; \
    test "$(git cat-file -t "refs/tags/${MEMTLY_COMMUNITY_TAG}")" = tag; \
    test "$(git rev-parse "refs/tags/${MEMTLY_COMMUNITY_TAG}^{commit}")" = "${MEMTLY_COMMUNITY_COMMIT}"; \
    git checkout --detach "${MEMTLY_COMMUNITY_COMMIT}"; \
    test "$(git rev-parse HEAD)" = "${MEMTLY_COMMUNITY_COMMIT}"; \
    test "$(git ls-tree HEAD Memtly.Core | awk '{print $3}')" = "${MEMTLY_CORE_COMMIT}"; \
    git submodule update --init --depth 1 Memtly.Core; \
    test "$(git -C Memtly.Core rev-parse HEAD)" = "${MEMTLY_CORE_COMMIT}"; \
    while IFS= read -r patch; do \
      case "${patch}" in ''|'#'*) continue ;; esac; \
      git apply --check "/overlay/patches/${patch}"; \
      git apply "/overlay/patches/${patch}"; \
    done < /overlay/patches/series; \
    rm -rf .git Memtly.Core/.git

FROM ${NODE_IMAGE} AS node

FROM ${SDK_IMAGE} AS build
ARG TARGETARCH=amd64
ARG BUILD_CONFIGURATION=Release
COPY --from=node /usr/local /usr/local
WORKDIR /src
COPY --from=source /src .
RUN test "$(node --version)" = "v22.23.2" && test "$(npm --version | cut -d. -f1)" -ge 10
RUN dotnet restore -a "${TARGETARCH}" ./Memtly.Community/Memtly.Community.csproj
WORKDIR /src/Memtly.Community
RUN dotnet build ./Memtly.Community.csproj \
      -a "${TARGETARCH}" \
      -c "${BUILD_CONFIGURATION}" \
      -o /app/build
RUN dotnet publish ./Memtly.Community.csproj \
      -a "${TARGETARCH}" \
      -c "${BUILD_CONFIGURATION}" \
      -o /app/publish \
      /p:UseAppHost=false
RUN test -s /app/publish/wwwroot/_content/Memtly.Core/dist/manifest.json && \
    node -e "const fs=require('fs'); const dll=fs.readFileSync('/app/publish/Memtly.Core.dll'); if (!dll.includes(Buffer.from('Memtly.Core.wwwroot.dist.manifest.json'))) process.exit(1)"

FROM ${RUNTIME_IMAGE} AS final
ARG MEMTLY_COMMUNITY_COMMIT=d9b7298866c8cafbd515a6bf5e260e1d0423f262
ARG MEMTLY_CORE_COMMIT=cc8c88d625136f04ae1f1063fc635f74e739bd72
LABEL org.opencontainers.image.title="Memtly HEIC Converter" \
      org.opencontainers.image.description="Independent build overlay for Memtly Community" \
      org.opencontainers.image.source="https://github.com/Tuxmint-Open-Source/memtly-heic-converter" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.version="1.0.6-foundation" \
      org.opencontainers.image.revision="${MEMTLY_COMMUNITY_COMMIT}" \
      io.tuxmint.memtly.core.revision="${MEMTLY_CORE_COMMIT}" \
      io.tuxmint.memtly.heic.enabled="false"
ENV CODE_BUILT_BY="Tuxmint-Open-Source/memtly-heic-converter"
WORKDIR /app
EXPOSE 5000
COPY --from=build /app/publish .
RUN mkdir -p /app/config
ENTRYPOINT ["dotnet", "Memtly.Community.dll"]
