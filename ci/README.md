# Continuous Integration Pipeline (CI)

## Building new images

To build a new version of the CI Docker image
run the following command.
Replacing <version> with the desired semantic versioning numer (e.g. v0.4.1):

```bash
./build.sh
```

## Running Tests locally

You can run all tests in the same environment as the CI/CD Pipeline using
the following command (this assumes you have already built the corresponding docker image above):

```bash
./run_tests.sh
```
**Caution**: This script will expose you ssh private key to the
running docker container to fetch packages from [gitlab.ltz.de](https://gitlab.lrz.de). Use carefully.

## Running the docker image locally

If you want to use the docker image for testing during development
you can run the following script:

```bash
./run_docker.sh
```

This command will allow you to run GUI applications  (i.e. `sumo-gui`)
within the container

**Caution**: Just like above, this script will expose you ssh private key to
the running docker container to fetch packages from [gitlab.ltz.de](https://gitlab.lrz.de). Use carefully.
