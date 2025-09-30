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
├── packetization.md
├── requirements.txt
└── src
    ├── adapters
    │   ├── inbound
    │   │   └── http
    │   │       └── pipeline_controller.py
    │   └── outbound
    │       ├── file_prompt_loader.py
    │       ├── mongodb
    │       │   ├── app_config_repository.py
    │       │   ├── channel_repository.py
    │       │   ├── prompt_repository.py
    │       │   ├── tweet_generation_repository.py
    │       │   ├── tweet_repository.py
    │       │   ├── user_repository.py
    │       │   └── video_repository.py
    │       ├── openai_client.py
    │       ├── transcription_client.py
    │       ├── twitter_client.py
    │       └── youtube_video_client.py
    ├── application
    │   └── services
    │       ├── ingestion_pipeline_service.py
    │       ├── POC_pipeline_service.py
    │       ├── prompt_composer_service.py
    │       └── publishing_pipeline_service.py
    ├── config.py                                       # carga .env y Settings                            
    ├── domain
    │   ├── entities
    │   │   ├── app_config.py
    │   │   ├── channel.py
    │   │   ├── prompt.py
    │   │   ├── tweet.py
    │   │   ├── tweet_generation.py
    │   │   ├── user.py
    │   │   └── video.py
    │   ├── ports
    │   │   ├── inbound
    │   │   │   ├── ingestion_pipeline_port.py
    │   │   │   └── publishing_pipeline_port.py
    │   │   └── outbound
    │   │       ├── mongodb
    │   │       │   ├── app_config_repository_port.py
    │   │       │   ├── channel_repository_port.py
    │   │       │   ├── prompt_repository_port.py
    │   │       │   ├── tweet_generation_repository_port.py
    │   │       │   ├── tweet_repository_port.py
    │   │       │   ├── user_repository_port.py
    │   │       │   └── video_repository_port.py
    │   │       ├── openai_port.py
    │   │       ├── prompt_loader_port.py
    │   │       ├── transcription_port.py
    │   │       ├── twitter_port.py
    │   │       └── video_source_port.py
    │   └── value_objects
    │       └── scheduler_config.py
    ├── infrastructure
    │   ├── mongodb.py                          # inicializa AsyncIOMotorClient y exporta `db`
    │   ├── mongodb_test.py
    │   └── security
    │      ├── encription.py
    │      └── generate_key_snippet.py
    └── main.py                                 # arranca FastAPI, registra routers de adapters/inbound/http/