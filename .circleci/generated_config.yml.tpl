version: 2
jobs:
  build:  # required for runs that don't use workflows
    working_directory: ~/backend/api
    docker:
      - image: cimg/python:3.10.1  # primary container for the build job
        auth:
          username: mydockerhub-user
          password: $DOCKERHUB_PASSWORD  # context / project UI env-var reference
    steps:
      - checkout  # checkout source code to working directory
      - run:
          command: |  # use pipenv to install dependencies
            sudo pip install pipenv
            pipenv install