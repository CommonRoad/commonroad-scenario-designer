# Continuous Integration Pipeline (CI)

## Building new images

To build a new version of the CI Docker image
run the following command.
Replacing <version> with the desired semantic versioning numer (e.g. v0.4.1):

```bash
./build.sh
```

## Running the docker image locally

If you want to use the docker image for testing during development
you can run the following script:

```bash
./run_docker.sh
```

This command will allow you to run GUI applications  (e.g. `sumo-gui`)
within the container, but also expose you ssh private key to it.
Use carefully.
