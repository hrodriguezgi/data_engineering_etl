FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    CONDA_DIR=/opt/conda \
    CONDA_ENV=app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        bzip2 \
        ca-certificates \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Install Miniforge (conda-forge based) and create a Python 3.10 environment.
RUN set -eux; \
    arch="$(uname -m)"; \
    case "$arch" in \
      x86_64) mf_arch="x86_64" ;; \
      aarch64|arm64) mf_arch="aarch64" ;; \
      *) echo "Unsupported architecture: $arch"; exit 1 ;; \
    esac; \
    curl -fsSL -o /tmp/miniforge.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-${mf_arch}.sh"; \
    bash /tmp/miniforge.sh -b -p "${CONDA_DIR}"; \
    rm -f /tmp/miniforge.sh; \
    "${CONDA_DIR}/bin/conda" create -y -n "${CONDA_ENV}" python=3.10; \
    "${CONDA_DIR}/bin/conda" clean -afy

ENV PATH=${CONDA_DIR}/envs/${CONDA_ENV}/bin:${CONDA_DIR}/bin:${PATH}

# Install uv in the Python 3.10 conda environment.
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy dependency manifests first for better Docker layer caching.
COPY requirements.txt pyproject.toml ./

# Install dependencies from requirements.txt via uv.
RUN uv pip install --system --no-cache -r requirements.txt

# Optional: copy files present in the build context.
COPY . .

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash"]
