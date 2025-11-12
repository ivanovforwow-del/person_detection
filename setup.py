from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line and not line.startswith("#")]

setup(
    name="person_detection_microservice",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Микросервис для детекции людей в RTSP/HTTP потоках",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/person_detection_microservice",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "person-detection-service=main:run_service",
        ],
    },
)