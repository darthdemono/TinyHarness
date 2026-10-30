"""Problem 5 in twenty lines: describe an image for a blind or low-vision reader.

    python examples/alt_text.py photo.jpg
"""
import sys

from tinyharness.client import Client, image_b64

SYSTEM = "You write alt text. One sentence for the gist, then one short paragraph of detail. No guessing names."


def describe(path, client=None):
    return (client or Client()).ask("Describe this image.", images=[image_b64(path)], system=SYSTEM)


if __name__ == "__main__":
    print(describe(sys.argv[1]))
