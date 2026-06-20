import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="osuirc",
    version="0.1.1",
    author="codefz840",
    author_email="code840@outlook.com",
    description="IRC client for osu!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/codefz840/osuirc",
    license="MIT",
    packages=["osuirc", "osuirc.utils", "osuirc.objects"],
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
