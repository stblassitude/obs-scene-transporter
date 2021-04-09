import os
import setuptools
import subprocess

with open("README.md", "r") as fh:
    long_description = fh.read()

version = None
try:
    version = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"]).decode("UTF-8").strip()
except Exception as e:
    version = "0.9.0"
if "GITHUB_REF" in os.environ and os.environ["GITHUB_REF"].startswith("refs/tags/"):
    version = os.environ["GITHUB_REF"][len("refs/tags/"):]

setuptools.setup(
    name="obs-scene-transporter",
    version=version,
    author="Stefan Bethke",
    author_email="stb@lassitu.de",
    description="Import and export OBS Studio scenes including all assets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stblassitude/obs-scene-transporter",
    project_urls={
        "Bug Tracker": "https://github.com/stblassitude/obs-scene-transporter/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': ['obs-scene-transporter=obsscenetransporter:main']
    },
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.6",
)