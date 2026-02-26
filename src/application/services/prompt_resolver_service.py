# src/application/services/prompt_resolver_service.py

#  Es un application service (y no un domain service) porque:
#   - Necesita acceder a repositorios (para cargar MasterPrompt).
#   - Orquesta entidades y value objects.
#   - Produce un resultado listo para usar por pipelines.