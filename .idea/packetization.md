video2text
├── .dockerignore
├── .env
├── .github
│   └── workflows
│       └── build.yaml
├── .gitignore
├── Dockerfile
├── k8s
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── ingress.yaml
│   ├── secret.yaml
│   └── service.yaml
├── packetization.txt
├── requirements.txt
└── src
    ├── adapters
    │   ├── inbound
    │   │   └── http
    │   │       ├── pipeline_controller.py
    │   │       └── __pycache__
    │   │           └── pipeline_controller.cpython-313.pyc
    │   └── outbound
    │       ├── file_prompt_loader.py
    │       ├── mongodb
    │       │   ├── app_config_repository.py
    │       │   ├── channel_repository.py
    │       │   ├── prompt_repository.py
    │       │   ├── tweet_generation_repository.py
    │       │   ├── tweet_repository.py
    │       │   ├── user_repository.py
    │       │   ├── video_repository.py
    │       │   └── __pycache__
    │       │       ├── app_config_repository.cpython-313.pyc
    │       │       ├── channel_repository.cpython-313.pyc
    │       │       ├── prompt_repository.cpython-313.pyc
    │       │       ├── tweet_generation_repository.cpython-313.pyc
    │       │       ├── tweet_repository.cpython-313.pyc
    │       │       ├── user_repository.cpython-313.pyc
    │       │       └── video_repository.cpython-313.pyc
    │       ├── openai_client.py
    │       ├── transcription_client.py
    │       ├── twitter_client.py
    │       ├── youtube_video_client.py
    │       └── __pycache__
    │           ├── file_prompt_loader.cpython-313.pyc
    │           ├── openai_client.cpython-313.pyc
    │           ├── transcription_client.cpython-313.pyc
    │           ├── twitter_client.cpython-313.pyc
    │           └── youtube_video_client.cpython-313.pyc
    ├── application
    │   └── services
    │       ├── ingestion_pipeline_service.py
    │       ├── POC_pipeline_service.py
    │       ├── prompt_composer_service.py
    │       ├── publishing_pipeline_service.py
    │       └── __pycache__
    │           ├── ingestion_pipeline_service.cpython-313.pyc
    │           ├── pipeline_service.cpython-313.pyc
    │           ├── prompt_composer_service.cpython-313.pyc
    │           └── publishing_pipeline_service.cpython-313.pyc
    ├── config.py
    ├── domain
    │   ├── entities
    │   │   ├── app_config.py
    │   │   ├── channel.py
    │   │   ├── prompt.py
    │   │   ├── tweet.py
    │   │   ├── tweet_generation.py
    │   │   ├── user.py
    │   │   ├── video.py
    │   │   └── __pycache__
    │   │       ├── app_config.cpython-313.pyc
    │   │       ├── channel.cpython-313.pyc
    │   │       ├── prompt.cpython-313.pyc
    │   │       ├── tweet.cpython-313.pyc
    │   │       ├── tweet_generation.cpython-313.pyc
    │   │       ├── user.cpython-313.pyc
    │   │       └── video.cpython-313.pyc
    │   ├── ports
    │   │   ├── inbound
    │   │   │   ├── ingestion_pipeline_port.py
    │   │   │   ├── publishing_pipeline_port.py
    │   │   │   └── __pycache__
    │   │   │       ├── ingestion_pipeline_port.cpython-313.pyc
    │   │   │       └── publishing_pipeline_port.cpython-313.pyc
    │   │   ├── outbound
    │   │   │   ├── mongodb
    │   │   │   │   ├── app_config_repository_port.py
    │   │   │   │   ├── channel_repository_port.py
    │   │   │   │   ├── prompt_repository_port.py
    │   │   │   │   ├── tweet_generation_repository_port.py
    │   │   │   │   ├── tweet_repository_port.py
    │   │   │   │   ├── user_repository_port.py
    │   │   │   │   ├── video_repository_port.py
    │   │   │   │   └── __pycache__
    │   │   │   │       ├── app_config_repository_port.cpython-313.pyc
    │   │   │   │       ├── channel_repository_port.cpython-313.pyc
    │   │   │   │       ├── prompt_repository_port.cpython-313.pyc
    │   │   │   │       ├── tweet_generation_repository_port.cpython-313.pyc
    │   │   │   │       ├── tweet_repository_port.cpython-313.pyc
    │   │   │   │       ├── user_repository_port.cpython-313.pyc
    │   │   │   │       └── video_repository_port.cpython-313.pyc
    │   │   │   ├── openai_port.py
    │   │   │   ├── prompt_loader_port.py
    │   │   │   ├── transcription_port.py
    │   │   │   ├── twitter_port.py
    │   │   │   ├── video_source_port.py
    │   │   │   └── __pycache__
    │   │   │       ├── openai_port.cpython-313.pyc
    │   │   │       ├── prompt_loader_port.cpython-313.pyc
    │   │   │       ├── transcription_port.cpython-313.pyc
    │   │   │       ├── twitter_port.cpython-313.pyc
    │   │   │       └── video_source_port.cpython-313.pyc
    │   │   └── __pycache__
    │   │       ├── openai_port.cpython-313.pyc
    │   │       ├── prompt_loader_port.cpython-313.pyc
    │   │       ├── transcription_port.cpython-313.pyc
    │   │       ├── twitter_port.cpython-313.pyc
    │   │       └── video_source_port.cpython-313.pyc
    │   └── value_objects
    │       ├── scheduler_config.py
    │       └── __pycache__
    │           └── scheduler_config.cpython-313.pyc
    ├── infrastructure
    │   ├── mongodb.py
    │   ├── mongodb_test.py
    │   ├── security
    │   │   ├── encription.py
    │   │   ├── generate_key_snippet.py
    │   │   └── __pycache__
    │   │       └── encription.cpython-313.pyc
    │   └── __pycache__
    │       └── mongodb.cpython-313.pyc
    ├── main.py
    ├── POC_video2text_app.py
    └── __pycache__
        ├── config.cpython-313.pyc
        └── main.cpython-313.pyc
