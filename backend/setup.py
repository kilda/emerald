from setuptools import find_packages, setup

setup(
    name='emerald',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'fastapi',
        'uvicorn'
    ],
    extras_require={
        'test': [

        ],
    },
)