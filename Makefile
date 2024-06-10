deploy:
	appwrite functions createDeployment \
    --functionId=66660add0027fb71e927 \
    --entrypoint='main.py' \
        --commands='pip install -r requirements.txt' \
    --code="./" \
    --activate=true