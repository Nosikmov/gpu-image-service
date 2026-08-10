# ComfyUI runtime image (GPU). Models are mounted from host volume.
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      python3-venv \
      git \
      curl \
      libgl1 \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ComfyUI

ARG COMFYUI_REF=master
RUN git clone --depth 1 --branch "${COMFYUI_REF}" https://github.com/comfyanonymous/ComfyUI.git . \
    && pip3 install --upgrade pip \
    && pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 \
    && pip3 install -r requirements.txt

EXPOSE 8188

# Models / output mounted at runtime
CMD ["python3", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
