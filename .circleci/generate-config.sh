cd .circleci
python -m ensurepip 
pip install envtpl
envtpl ci-template.yml -o generated_config.yml --keep-template