from setuptools import find_packages, setup

print(find_packages(include=["velo", "velo.*"]))
setup(
    name="velo",
    version="1.0.0",
    packages=find_packages(include=["velo", "velo.*"]),
    license="Proprietary",
    long_description="Distributed model execution proof of concept project",
)
