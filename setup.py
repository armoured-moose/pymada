import setuptools

setuptools.setup(
    name="pymada",
    version="0.0.1",
    packages=setuptools.find_packages(where="pymada"),
    package_dir={"": "pymada",},
    url="https://github.com/armoured-moose/pymada",
    author="Samuel Ward",
    author_email="samuelhward@gmail.com",
    description="pymada"
    # long_description=open('README.md').read(),
    # install_requires=['']
)
