# Upscaling Options (Practical vs Research)

## Purpose

Use this note to choose the right workflow for image enlargement requests.

## Decision Guide

- The user says "upscale this image/photo/screenshot/logo to 2x/4x" -> Use interpolation first (`scripts/upscale_image.py`).
- The user says "recover detail / sharpen blurry image / denoise JPEG artifacts" -> Prefer AI super-resolution (for example Real-ESRGAN) if install/setup is acceptable.
- The user says "generate a huge 4K/8K image from a prompt" or is exploring diffusion research methods -> DyPE is relevant.

## DyPE (research fit)

- DyPE is not a simple drop-in photo upscaler.
- It is a diffusion-oriented high-resolution generation method that improves efficiency/quality for large images by dynamic patching.
- Treat it as a generative image pipeline option, especially for prompt-driven outputs or advanced diffusion workflows.
- Expect more setup complexity (GPU, model/runtime dependencies, repo-specific workflow) than routine upscaling tools.

## Practical Local Upscaling Defaults

### 1. Interpolation (bundled script)

- Pillow Lanczos: fastest path with minimal dependencies, deterministic, works well for many enlargement tasks.
- ffmpeg Lanczos: useful when the user already uses ffmpeg pipelines or wants consistent image/video scaling behavior.
- Limitation: interpolation enlarges pixels; it cannot truly recover lost detail.

### 2. AI Super-Resolution (recommended next step)

- Real-ESRGAN is the practical starting point for local AI upscaling of existing images.
- Use it when the user explicitly wants detail enhancement beyond interpolation.
- Clarify tradeoffs: slower runtime, larger dependencies, possible hallucinated textures, and model/style selection (photo vs anime/illustration).

## Scope and Safety

- Do not frame upscaling as guaranteed restoration of missing information.
- Ask for the original highest-resolution file when available.
- If the user requests watermark/logo removal, treat that as a separate task and follow policy constraints.

## Source URLs

- DyPE project page: https://noamissachar.github.io/DyPE/
- DyPE repository: https://github.com/guyyariv/DyPE
- Real-ESRGAN repository: https://github.com/xinntao/Real-ESRGAN
