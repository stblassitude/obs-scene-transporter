import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="obs-scene-transporter", # Replace with your own username
    version="0.0.1",
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
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    python_requires=">=3.6",
)