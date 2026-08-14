# References

Place source images for reconstruction here.

Default project configuration expects:

```text
data/references/hotrod_reference.png
```

Reference images are inputs, never authoritative geometry. The analyzer may infer proportions and part relationships, but uncertain dimensions must remain explicit parameters rather than fabricated facts.

## Readiness gate

Before a Blender learning run, validate the configured reference:

```bash
rodforge reference-check --config configs/project.yaml
```

The command fails closed when the image is missing, unreadable, or too small. A valid report includes format, pixel dimensions, color mode, alpha presence, aspect ratio, and a SHA-256 fingerprint so later learning episodes can be tied to the exact visual input that produced them.

The fingerprint identifies the input bytes; it is not a claim that the image contains complete or metrically accurate geometry.
