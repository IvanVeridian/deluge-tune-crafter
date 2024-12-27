from setuptools import setup, find_packages

setup(
    name="deluge_midi_converter",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pretty_midi",
        "basic-pitch[tf]",
        "tqdm",
    ],
    python_requires=">=3.6",
) 