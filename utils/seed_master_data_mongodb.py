# utils/seed_master_data_mongodb.py

# ---- HOW TO USE THIS SCRIPT ----- 
# cd /d/software_projects/video2text
# PYTHONPATH="$PWD/src" SEED_CLEAN_USERS=true SEED_CLEAN_CHANNELS=true SEED_CLEAN_PROMPTS=true SEED_CLEAN_MASTER_PROMPTS=true SEED_CLEAN_APP_CONFIG=true SEED_CLEAN_TWEET_GENERATIONS=true SEED_CLEAN_TWEETS=true SEED_CLEAN_VIDEOS=true SEED_CLEAN_USER_SCHEDULER_STATUS_RUNTIME=true python utils/seed_master_data_mongodb.py
# (WARNING!! ----> check deletion flags SEED_CLEAN_!! when true the entire collection will be erased before seeding the master data):


import asyncio
import os
import sys
import threading
import inspect
import logging
import datetime as _dt
from datetime import timezone
from bson import ObjectId
from typing import Optional
from datetime import datetime
from pathlib import Path 
import yaml

# reuse existing async db instance
from infrastructure.mongodb import db  # AsyncIOMotorDatabase

# IMPORTAR repos/adapters solo para app_config fallback
from adapters.outbound.mongodb.app_config_repository import MongoAppConfigRepository

# Specific logger for this module (follow existing project logging style)
logger = logging.getLogger(__name__)

# WARNING - IMPORTANT !!!
# Flags to delete all documents (set CLEAN_XXX to "true" to enable deletion of the complete collection, all documents will be deleted !!!)
CLEAN_USERS = os.getenv("SEED_CLEAN_USERS", "false").lower() in ("1", "true", "yes")
CLEAN_CHANNELS = os.getenv("SEED_CLEAN_CHANNELS", "false").lower() in ("1", "true", "yes")
CLEAN_PROMPTS = os.getenv("SEED_CLEAN_PROMPTS", "false").lower() in ("1", "true", "yes")
CLEAN_MASTER_PROMPTS = os.getenv("SEED_CLEAN_MASTER_PROMPTS", "false").lower() in ("1", "true", "yes")
CLEAN_APP_CONFIG = os.getenv("SEED_CLEAN_APP_CONFIG", "false").lower() in ("1", "true", "yes")
CLEAN_TWEET_GENERATIONS = os.getenv("SEED_CLEAN_TWEET_GENERATIONS", "false").lower() in ("1", "true", "yes")
CLEAN_TWEETS = os.getenv("SEED_CLEAN_TWEETS", "false").lower() in ("1", "true", "yes")
CLEAN_VIDEOS = os.getenv("SEED_CLEAN_VIDEOS", "false").lower() in ("1", "true", "yes")
CLEAN_USER_SCHEDULER_STATUS_RUNTIME = os.getenv("SEED_CLEAN_USER_SCHEDULER_STATUS_RUNTIME", "false").lower() in ("1", "true", "yes")

# Import domain entities for AppConfig usage
from domain.entities.app_config import AppConfig, SchedulerConfig

# -----------------------
# HELPER METHODS 
# -----------------------

def ms_to_dt(ms: int) -> _dt.datetime:
    return _dt.datetime.fromtimestamp(ms / 1000.0)

def _read_input(result_container: list) -> None:
    try:
        result_container.append(sys.stdin.readline())
    except Exception:
        result_container.append("")

def prompt_confirm(message: str, timeout: int = 60, default: bool = True) -> bool:
    """
    Muestra `message` y espera input del usuario.
    - Enter o 'Y'/'y' => True (proceed)
    - 'N'/'n' => False (abort)
    - Si no hay input en `timeout` segundos => devuelve `default` (por defecto True)
    Nota: usa un hilo para leer stdin; si no hay input en el timeout el hilo queda bloqueado pero el programa continúa.
    """
    prompt_text = (
        f"{message}\n"
        f"[Press Enter or Y to proceed, N to abort] (auto-continue in {timeout}s): "
    )
    print(prompt_text, end="", flush=True)

    result: list = []
    t = threading.Thread(target=_read_input, args=(result,), daemon=True)
    t.start()
    t.join(timeout)

    if not result:
        # timeout: continuar como si se hubiera pulsado Enter/Y
        print()  # newline after prompt
        return default

    user_input = result[0].strip().lower()
    print()  # newline after prompt
    if user_input == "" or user_input == "y":
        return True
    if user_input == "n":
        return False
    # cualquier otra entrada: tratar como default (proceed)
    return default

# -----------------------
# SEED DB WITH DATA 
# -----------------------
async def seed():
    logger.info("Script - Seeding data to MongoDB starting", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

    # ---------------------------
    # REQUEST USER PERMISSION PRIOR TO ERASE COLLECTIONS
    # ---------------------------

    # Construir lista de collections marcadas como true en las env vars SEED_CLEAN_*
    _env_map = {
        "users": "SEED_CLEAN_USERS",
        "channels": "SEED_CLEAN_CHANNELS",
        "prompts": "SEED_CLEAN_PROMPTS",
        "master_prompts": "SEED_CLEAN_MASTER_PROMPTS",
        "app_config": "SEED_CLEAN_APP_CONFIG",
        "tweet_generations": "SEED_CLEAN_TWEET_GENERATIONS",
        "tweets": "SEED_CLEAN_TWEETS",
        "videos": "SEED_CLEAN_VIDEOS",
        "user_scheduler_runtime_status": "SEED_CLEAN_USER_SCHEDULER_STATUS_RUNTIME",
    }

    _collections_to_erase = [
        name for name, env_key in _env_map.items()
        if os.environ.get(env_key, "").strip().lower() in ("1", "true", "yes")
    ]

    if _collections_to_erase:
        # Obtain DB name for the confirmation message (Motor AsyncIOMotorDatabase exposes .name)
        try:
            db_name = getattr(db, "name", None) or getattr(db, "database_name", None) or "unknown"
        except Exception:
            db_name = "unknown"

        _list_text = "\n".join(f"- {c}" for c in _collections_to_erase)
        _msg = f"\nThe following MongoDB collections in database '{db_name}' will be fully erased of documents. Do you want to proceed?\n" + _list_text
        if not prompt_confirm(_msg, timeout=60, default=True):
            print(f"Aborted by user before cleaning collections in database '{db_name}'.")
            sys.exit(0)
    else:
        # Si no hay collections marcadas, no preguntar y continuar
        pass

    # Optional cleaning using direct collection clears (we operate directly here, not using application repo adapters)
    if CLEAN_USERS:
        await db.get_collection("users").delete_many({})
        logger.info("[ok] erased users", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_CHANNELS:
        await db.get_collection("channels").delete_many({})
        logger.info("[ok] erased channels", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_PROMPTS:
        await db.get_collection("prompts").delete_many({})
        logger.info("[ok] erased prompts", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_MASTER_PROMPTS:
        await db.get_collection("master_prompts").delete_many({})
        logger.info("[ok] erased master_prompts", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_APP_CONFIG:
        await db.get_collection("app_config").delete_many({})
        logger.info("[ok] erased app_config", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_TWEET_GENERATIONS:
        await db.get_collection("tweet_generations").delete_many({})
        logger.info("[ok] erased tweet_generations", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_TWEETS:
        await db.get_collection("tweets").delete_many({})
        logger.info("[ok] erased tweets", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_VIDEOS:
        await db.get_collection("videos").delete_many({})
        logger.info("[ok] erased videos", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    if CLEAN_USER_SCHEDULER_STATUS_RUNTIME:
        await db.get_collection("user_scheduler_runtime_status").delete_many({})
        logger.info("[ok] erased user_scheduler_runtime_status", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

    # Ensure collections exist (create empty collections if missing)
    existing_collections = await db.list_collection_names()
    collections_to_ensure = [
        "users",
        "channels",
        "prompts",
        "master_prompts",
        "app_config",
        "tweet_generations",
        "tweets",
        "videos",
        "user_scheduler_runtime_status",
    ]
    for coll_name in collections_to_ensure:
        if coll_name not in existing_collections:
            try:
                await db.create_collection(coll_name)
                logger.info(f"[ok] created collection {coll_name}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
            except Exception:
                logger.warning(f"[warn] could not create collection {coll_name} (it may already exist)", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

    # ---------------------------
    # REQUEST USER PERMISSION PRIOR TO WRITE SEEED DATA
    # ---------------------------
    _msg2 = "\nMongoDB collections have been erased, and seed data will be written now, Do you want to proceed?"
    if not prompt_confirm(_msg2, timeout=60, default=True):
        print("Aborted by user after cleaning collections (seed writing cancelled).")
        sys.exit(0)


    # Si el PC llega aquí, continuar con la escritura de seed data:

    # -----------------------
    # 1) USER
    # -----------------------
    MASTER_USER_ID = ObjectId("000000000000000000000001")  # 24-hex constant

    # --- user_doc uses ObjectId type for _id ---
    user_doc = {
        "_id": MASTER_USER_ID,
        "username": "nico_seed@me.com",
        # "openaiApiKey": "",
        "userTwitterCredentials": {
            "oauth1AccessToken": "",
            "oauth1AccessTokenSecret": "",
            "oauth2AccessToken": "",
            "oauth2AccessTokenExpiresAt": "",
            "oauth2RefreshToken": "",
            "oauth2RefreshTokenExpiresAt": "",
            "screenName": "nicolai"
        },
        "schedulerConfig": {
            "ingestionPipelineFrequencyMinutes": 1440,
            "publishingPipelineFrequencyMinutes": 1440,
            "isIngestionPipelineEnabled": True,
            "isPublishingPipelineEnabled": False
        },
        "maxTweetsToFetchFromDB": 4,
        "maxTweetsToPublish": 1,
        "tweetFetchSortOrder": "random",
        "createdAt": ms_to_dt(1756412100000),
        "updatedAt": ms_to_dt(1763205251652)
    }

    # --- Persist user: prefer repo.update (exposed) then verify and enforce via replace_one if missing
    try:
        from adapters.outbound.mongodb.user_repository import MongoUserRepository  # type: ignore
        from domain.entities.user import User, UserTwitterCredentials  # type: ignore
        from domain.value_objects.scheduler_config import SchedulerConfig  # type: ignore

        user_repo = MongoUserRepository(db)
        try:
            creds = UserTwitterCredentials(
                oauth1_access_token="",
                oauth1_access_token_secret="",
                oauth2_access_token="",
                oauth2_access_token_expires_at=None,
                oauth2_refresh_token=None,
                oauth2_refresh_token_expires_at=None,
                screen_name=None
            )

            # build SchedulerConfig from the user_doc (use defaults if keys missing)
            sc_doc = user_doc.get("schedulerConfig", {})
            scheduler_config = SchedulerConfig(
                ingestion_pipeline_frequency_minutes=int(sc_doc.get("ingestionPipelineFrequencyMinutes", 1440)),
                publishing_pipeline_frequency_minutes=int(sc_doc.get("publishingPipelineFrequencyMinutes", 1440)),
                is_ingestion_pipeline_enabled=bool(sc_doc.get("isIngestionPipelineEnabled", True)),
                is_publishing_pipeline_enabled=bool(sc_doc.get("isPublishingPipelineEnabled", True)),
            )

            user_entity = User(
                id=str(MASTER_USER_ID),
                username=user_doc.get("username", ""),
                # openai_api_key=user_doc.get("openaiApiKey", None),
                twitter_credentials=creds,
                scheduler_config=scheduler_config,
                max_tweets_to_fetch_from_db=user_doc.get("maxTweetsToFetchFromDB", 10),
                max_tweets_to_publish=user_doc.get("maxTweetsToPublish", 5),
                tweet_fetch_sort_order=None,
                created_at=user_doc.get("createdAt"),
                updated_at=user_doc.get("updatedAt")
            )

            # Use update (repo exposes it) to respect provided id
            await user_repo.update(user_entity)  # type: ignore

            # Verify document exists; if not, enforce with replace_one(upsert=True)
            found = await db.get_collection("users").find_one({"_id": MASTER_USER_ID})
            if not found:
                await db.get_collection("users").replace_one({"_id": MASTER_USER_ID}, user_doc, upsert=True)
                logger.info(f"[ok] user not found after update; enforced stable _id via direct DB replace = {MASTER_USER_ID}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
            else:
                logger.info(f"[ok] user updated via repo, id={user_entity.id}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
        except Exception:
            # If something fails in the repo, force the _id with replace_one
            await db.get_collection("users").replace_one({"_id": MASTER_USER_ID}, user_doc, upsert=True)
            logger.info("[ok] user upserted with stable _id via direct DB fallback = %s", str(MASTER_USER_ID), extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    except Exception:
        # If adapter import fails, fallback direct (ensures stable _id)
        await db.get_collection("users").replace_one({"_id": MASTER_USER_ID}, user_doc, upsert=True)
        logger.info("[ok] user upserted with stable _id via direct DB (adapter missing) = %s", str(MASTER_USER_ID), extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})


    # -----------------------
    # 2) CHANNEL
    # -----------------------
    # channels_input: list of dicts with keys 'youtubeChannelId' and 'title'
    
    channels_input = [
            {"youtubeChannelId": "UCvSXMi2LebwJEM1s4bz5IBA", "title": "@NewMoneyYouTube"}, 
            {"youtubeChannelId": "UC9vUu4vlIlMC0dHQCTvQPbg", "title": "@MoneyGuyShow"},
            {"youtubeChannelId": "UCAeAB8ABXGoGMbXuYPmiu2A", "title": "@TheSwedishInvestor"},
            {"youtubeChannelId": "UCV6KDgJskWaEckne5aPA0aQ", "title": "@GrahamStephan"},
            {"youtubeChannelId": "UCT3EznhW_CNFcfOlyDNTLLw", "title": "@MinorityMindset"},
            {"youtubeChannelId": "UCFBpVaKCC0ajGps1vf0AgBg", "title": "@humphrey"},
        ]

    saved_channel_ids = []   # list[str] -> will contain the string IDs returned/created in Mongo

    # Try to import channel repo and entity once
    try:
        from adapters.outbound.mongodb.channel_repository import MongoChannelRepository  # type: ignore
        from domain.entities.channel import Channel  # type: ignore
        channel_repo = MongoChannelRepository(db)
        repo_available = True
    except Exception:
        channel_repo = None
        Channel = None
        repo_available = False

    for ch in channels_input:
        # Build channel document using only input fields + fixed defaults
        channel_doc = {
            # _id will be set from repo result or direct upsert fallback
            "userId": MASTER_USER_ID,  # reference to master user as ObjectId
            "youtubeChannelId": ch["youtubeChannelId"],
            "selectedPromptId": None,
            "title": ch["title"],
            #"pollingInterval": 18,
            "maxVideosToFetchFromChannel": 2,
            "lastPolledAt": None,
            "createdAt": _dt.datetime.now(_dt.timezone.utc),
            "updatedAt": _dt.datetime.now(_dt.timezone.utc),
        }

        saved_channel_id = None
        channel_obj_id = None

        if repo_available:
            try:
                # Build channel entity without forcing id (repo.save will insert and return id)
                temp_channel_entity = Channel(
                    id=None,
                    user_id=str(channel_doc["userId"]),
                    youtube_channel_id=channel_doc.get("youtubeChannelId", ""),
                    selected_prompt_id=None,
                    title=channel_doc.get("title", ""),
                    # polling_interval=channel_doc.get("pollingInterval"),
                    max_videos_to_fetch_from_channel=channel_doc.get("maxVideosToFetchFromChannel"),
                    last_polled_at=channel_doc.get("lastPolledAt"),
                    created_at=channel_doc.get("createdAt"),
                    updated_at=channel_doc.get("updatedAt")
                )
                saved_channel_id = await channel_repo.save(temp_channel_entity)  # type: ignore
                logger.info(f"[ok] channel saved via repo, id={saved_channel_id}",
                            extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

                # Try to convert repo id to ObjectId for DB references; if not valid, keep string
                try:
                    channel_obj_id = ObjectId(saved_channel_id)
                except Exception:
                    channel_obj_id = saved_channel_id

            except Exception:
                # fallback: create a new ObjectId and upsert directly
                channel_obj_id = ObjectId()
                channel_doc["_id"] = channel_obj_id
                await db.get_collection("channels").replace_one({"_id": channel_obj_id}, channel_doc, upsert=True)
                saved_channel_id = str(channel_obj_id)
                logger.info(f"[ok] channel upserted with _id={channel_obj_id} via direct DB fallback",
                            extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
        else:
            # adapter import failed -> direct DB upsert with a generated ObjectId
            channel_obj_id = ObjectId()
            channel_doc["_id"] = channel_obj_id
            await db.get_collection("channels").replace_one({"_id": channel_obj_id}, channel_doc, upsert=True)
            saved_channel_id = str(channel_obj_id)
            logger.info(f"[ok] channel upserted with _id={channel_obj_id} via direct DB (adapter missing)",
                        extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

        # Ensure we have a canonical channel_obj_id (prefer ObjectId form)
        if channel_obj_id is None and saved_channel_id is not None:
            try:
                channel_obj_id = ObjectId(saved_channel_id)
            except Exception:
                channel_obj_id = saved_channel_id

        # Append the canonical string id (prefer hex of ObjectId when available)
        saved_channel_ids.append(str(channel_obj_id))
        logger.debug("channel saved; appended id=%s", saved_channel_ids[-1])


    # ------------------------------
    # 3) MASTER PROMPT
    # ------------------------------
    # saved_channel_ids is expected to be a list of channel IDs (strings) produced by the CHANNEL step

    # Load prompt messages from non-reposited file
    path = Path("prompts/seed_master_data_mongodb_PROMPT.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    SYSTEM_MESSAGE = data["system_message"]
    USER_MESSAGE = data["user_message"]

    # Default tweet length policy for the seeded master prompt
    tweet_length_policy_doc = {
        "mode": "range",               # "fixed" | "range"
        "minLength": 120,
        "maxLength": 220,
        "targetLength": 110,
        "tolerancePercent": 10,
        "unit": "chars"                # "chars" | "tokens"
    }

    # Try to import master prompt repo and domain entity once (optional adapter path)
    try:
        from adapters.outbound.mongodb.master_prompt_repository import MongoMasterPromptRepository  # type: ignore
        from domain.entities.master_prompt import MasterPrompt  # type: ignore
        from domain.entities.prompt import PromptContent, TweetLengthPolicy, TweetLengthMode, TweetLengthUnit  # type: ignore
        master_prompt_repo = MongoMasterPromptRepository(db)
        repo_master_prompt_available = True
    except Exception:
        master_prompt_repo = None
        MasterPrompt = None
        PromptContent = None
        TweetLengthPolicy = None
        TweetLengthMode = None
        TweetLengthUnit = None
        repo_master_prompt_available = False

    # Build master_prompt document
    master_prompt_doc = {
        "_id": ObjectId(),
        "category": "Finance",  # adjust category/subcategory as needed
        "subcategory": "Investing",
        "promptContent": {
            "systemMessage": SYSTEM_MESSAGE,
            "userMessage": USER_MESSAGE,
        },
        "languageOfThePrompt": "English",
        "languageToGenerateTweets": "Spanish (ESPAÑOL)",
        "maxTweetsToGeneratePerVideo": 2,
        "tweetLengthPolicy": tweet_length_policy_doc,
        "createdAt": _dt.datetime.now(_dt.timezone.utc),
        "updatedAt": _dt.datetime.now(_dt.timezone.utc),
    }

    saved_master_prompt_id = None

    # Persist master prompt via repository adapter first; fallback to direct DB upsert if adapter missing or fails
    if repo_master_prompt_available:
        try:
            # Build TweetLengthPolicy entity if available
            tlp_entity = None
            if TweetLengthPolicy is not None and isinstance(master_prompt_doc.get("tweetLengthPolicy"), dict):
                tlp = master_prompt_doc["tweetLengthPolicy"]
                try:
                    mode_enum = TweetLengthMode(tlp.get("mode")) if tlp.get("mode") else TweetLengthMode.RANGE
                except Exception:
                    mode_enum = TweetLengthMode.RANGE
                try:
                    unit_enum = TweetLengthUnit(tlp.get("unit")) if tlp.get("unit") else TweetLengthUnit.CHARS
                except Exception:
                    unit_enum = TweetLengthUnit.CHARS

                tlp_entity = TweetLengthPolicy(
                    mode=mode_enum,
                    min_length=tlp.get("minLength"),
                    max_length=tlp.get("maxLength"),
                    target_length=tlp.get("targetLength"),
                    tolerance_percent=tlp.get("tolerancePercent", 10),
                    unit=unit_enum,
                )

            master_prompt_entity = MasterPrompt(
                id=str(master_prompt_doc["_id"]),
                category=master_prompt_doc["category"],
                subcategory=master_prompt_doc["subcategory"],
                prompt_content=PromptContent(
                    system_message=master_prompt_doc["promptContent"]["systemMessage"],
                    user_message=master_prompt_doc["promptContent"]["userMessage"],
                ),
                language_of_the_prompt=master_prompt_doc.get("languageOfThePrompt", ""),
                language_to_generate_tweets=master_prompt_doc.get("languageToGenerateTweets", ""),
                max_tweets_to_generate_per_video=master_prompt_doc.get("maxTweetsToGeneratePerVideo", 0),
                tweet_length_policy=tlp_entity,
                created_at=master_prompt_doc.get("createdAt"),
                updated_at=master_prompt_doc.get("updatedAt"),
            )

            saved_master_prompt_id = await master_prompt_repo.insert_one(master_prompt_entity)  # type: ignore
            # If repo returns entity or id, normalize to string id
            if isinstance(saved_master_prompt_id, MasterPrompt):
                saved_master_prompt_id = saved_master_prompt_id.id
            logger.info(f"[ok] master_prompt saved via repo, id={saved_master_prompt_id}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
        except Exception:
            await db.get_collection("master_prompts").replace_one(
                {"category": master_prompt_doc["category"], "subcategory": master_prompt_doc["subcategory"]},
                master_prompt_doc,
                upsert=True
            )
            saved_master_prompt_id = str(master_prompt_doc["_id"])
            logger.info(f"[ok] master_prompt upserted via direct DB fallback, id={saved_master_prompt_id}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    else:
        await db.get_collection("master_prompts").replace_one(
            {"category": master_prompt_doc["category"], "subcategory": master_prompt_doc["subcategory"]},
            master_prompt_doc,
            upsert=True
        )
        saved_master_prompt_id = str(master_prompt_doc["_id"])
        logger.info(f"[ok] master_prompt upserted via direct DB (adapter missing), id={saved_master_prompt_id}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

    # Now update all seeded channels to reference the same master prompt
    for channel_id_str in saved_channel_ids:
        try:
            channel_ref = ObjectId(channel_id_str)
        except Exception:
            channel_ref = channel_id_str

        await db.get_collection("channels").update_one(
            {"_id": channel_ref},
            {"$set": {"selectedMasterPromptId": ObjectId(saved_master_prompt_id), "updatedAt": _dt.datetime.now(_dt.timezone.utc)}}
        )
        logger.info(f"[ok] channel {channel_ref} updated with selectedMasterPromptId={saved_master_prompt_id}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

    # If still needed to keep an array of affected channel ids, saved_channel_ids can be reused.
    # saved_master_prompt_id contains the master prompt id (string).


    """
    # ------------------------------
    # 3) PROMPT
    # ------------------------------
    # saved_channel_ids is expected to be a list of channel IDs (strings) produced by the CHANNEL step
    # Example: saved_channel_ids = ["645a1f2b...", "645a1f2c...", ...]

    SYSTEM_MESSAGE = (
    === WHO YOU ARE ===
    You are a witty, insightful financial educator who writes engaging, human-sounding tweets that spark curiosity and conversation.

    === MANDATORY CONTENT RULES ===
    1. Each tweet must reference at least one specific detail from the transcript (e.g., names, events, strategies, dates, figures, or quotes).
    2. Avoid generic advice — every tweet must clearly tie back to the video's narrative.
    3. Each tweet must deliver the maximum possible value to the reader — no empty promotion, channel mentions, or filler.
    4. That value can be in the form of a learning, a practical tip, an educational takeaway, or a thought-provoking reflection that leaves the reader thinking about the topic.
    5. Model your tweets closely on the style, tone, and structure of the examples provided below (STYLE EXAMPLES GOOD).
    6. Each tweet must stand alone and provide immediate value to the reader.
    7. Do not invite the reader to watch the video or to 'learn more later'.
    8. Avoid vague calls like 'profundicemos juntos' or 'descubre más' (see below: STYLE EXAMPLES BAD).
    9. Instead, include a concrete insight, fact, or reflection directly in the tweet.

    === STYLE & TONE ===
    - Speak like a friend interested in personal finance, using clear, approachable language.
    - Conversational and engaging.
    - Keep each tweet in a human voice: use contractions and colloquial expressions common in Spain.
    - Voice: conversational, close, no unnecessary technicalities (Example voice: "Sounds odd? Check this out…")
    - Intelligent sense of humor where appropriate.
    - Occasional emojis and relevant hashtags.
    - Use "you" instead of "sir/ma'am" to keep the tone direct and familiar.
    - Vary the structure: some tweets as questions, others as impactful statements, others as quotes.
    - Avoid offensive or vulgar words that sound bad in Spanish (e.g., "vejestorio", etc.).
    - You may use common financial terms if the tweet requires them (e.g., long position, short position, etc.).
    - Use simple metaphors (e.g., "it's like saving in a jar") to explain complex ideas.

    === OUTPUT FORMAT ===
    - Do NOT number the tweets.
    - Each tweet on its own line.
    - No introductions or explanations — only the tweets.

    === STYLE EXAMPLES GOOD (Spanish) ===
    - "Las correcciones bursátiles pueden ser oportunidades de oro. Como dice Buffett: cuando llueve oro, mejor coge una bañera, no una cucharita. 🌧️💵 #CorrecciónDeMercado"
    - "Warren Buffett acumula efectivo, no para adivinar el mercado, sino para aprovechar oportunidades únicas cuando los precios caen. La paciencia tiene recompensa. 💰📉 #SabiduríaInversora #InversiónEnValor"
    - "Las correcciones de mercado suelen venir provocadas por factores externos, no solo por sobrevaloración. Estar preparado supera al 'market timing'. 🧠📊 #MercadoDeValores #InversiónALargoPlazo"
    - "Diversificar y pensar a largo plazo es clave para surfear la volatilidad. Cabalga las olas, no persigas la marea. 🌊📈 #LibertadFinanciera #InvierteInteligente"
    - "En las caídas del mercado, el efectivo es el rey 👑. Las inversiones de Buffett en 2008 en Goldman Sachs y GE demostraron que la oportunidad llega a los que están preparados. 🔑💼 #EfectivoEnMano #SabiduríaBuffett"
    - "¿Y si la próxima gran oportunidad llega en plena crisis? Los inversores pacientes ya saben la respuesta. ⏳📉 #InversiónInteligente"
    - "Los CDOs (Collateralized Debt Obligation) empaquetaban hipotecas basura como si fueran oro. En 2008 aprendimos que el envoltorio no cambia la realidad. 🎭💣 #CrisisFinanciera #RiesgoEstructural"
    - "Si una inversión es tan compleja que nadie puede explicártela en 2 frases, cuidado: puede esconder un riesgo enorme. Ahí están los CDOs en la crisis 2008. ⚠️📉 #InversiónInteligente #Lección2008"
    
    === STYLE EXAMPLES BAD (Spanish) ===
    - "Compra esto ahora, es la mejor inversión del año, enlace aquí."
    - "Gran vídeo, suscríbete y comparte con todos tus amigos!!!"
    - "Invertir es fácil, solo sigue estos pasos y serás rico en 30 días."
    - "Este mercado va a subir seguro, confía en mí y pon todo tu dinero."
    - "Resumen: cosas importantes, mira el vídeo para más info."
    - "Opinión personal: yo creo que esto es lo mejor, no lo dudes."
    - "Tweet genérico sin detalle: 'La diversificación es buena, invierte hoy'."
    - "Demasiado técnico y largo: explicación de 3 párrafos con jerga y sin gancho."
    )

    USER_MESSAGE = (
    You are given a transcript of a video. 
    Your task is to generate independent sentences, or texts, suitable for posting on Twitter (X). 
    Each sentence or text must be educational, meaningful, and targeted to a financial investing audience. 
    You may use a touch of humor if it helps boost engagement. 
    Include relevant hashtags and emojis when they enhance clarity or engagement. 
    Take into account everything described in the SYSTEM_MESSAGE.
    )
    # Do not include any introduction or explanation — output only the tweets, one per line.

    # Result array: will contain the saved prompt IDs (strings) created for each channel
    saved_prompt_ids = []

    # Try to import prompt repo and domain entity once
    try:
        from adapters.outbound.mongodb.prompt_repository import MongoPromptRepository  # type: ignore
        from domain.entities.prompt import Prompt, PromptContent, TweetLengthPolicy, TweetLengthMode, TweetLengthUnit  # type: ignore
        prompt_repo = MongoPromptRepository(db)
        repo_prompt_available = True
    except Exception:
        prompt_repo = None
        Prompt = None
        PromptContent = None
        TweetLengthPolicy = None
        TweetLengthMode = None
        TweetLengthUnit = None
        repo_prompt_available = False

    for channel_id_str in saved_channel_ids:
        # Try to convert channel id string to ObjectId for storing in the document; if fails, keep string
        try:
            channel_ref = ObjectId(channel_id_str)
        except Exception:
            channel_ref = channel_id_str

        # Default tweet length policy for seeded prompts (adjust as you prefer)
        tweet_length_policy_doc = {
            "mode": "range",               # "fixed" | "range"
            "minLength": 120,
            "maxLength": 220,
            "targetLength": 110,           # optional preference
            "tolerancePercent": 10,
            "unit": "chars"                # "chars" | "tokens"
        }

        prompt_doc = {
            "_id": ObjectId(),
            "userId": MASTER_USER_ID,
            "channelId": channel_ref,
            "promptContent": {
                "systemMessage": SYSTEM_MESSAGE,
                "userMessage": USER_MESSAGE
            },
            "languageOfThePrompt": "English",
            "languageToGenerateTweets": "Spanish (ESPAÑOL)",
            "maxTweetsToGeneratePerVideo": 2,
            "tweetLengthPolicy": tweet_length_policy_doc,
            "createdAt": _dt.datetime.now(_dt.timezone.utc),
            "updatedAt": _dt.datetime.now(_dt.timezone.utc)
        }

        saved_prompt_id = None

        # Persist prompt via repository adapter first; fallback to direct DB upsert if adapter missing or fails
        if repo_prompt_available:
            try:
                # Build TweetLengthPolicy entity if available
                tlp_entity = None
                if TweetLengthPolicy is not None and isinstance(prompt_doc.get("tweetLengthPolicy"), dict):
                    tlp = prompt_doc["tweetLengthPolicy"]
                    # Safe enum conversion with fallbacks
                    try:
                        mode_enum = TweetLengthMode(tlp.get("mode")) if tlp.get("mode") else TweetLengthMode.RANGE
                    except Exception:
                        mode_enum = TweetLengthMode.RANGE
                    try:
                        unit_enum = TweetLengthUnit(tlp.get("unit")) if tlp.get("unit") else TweetLengthUnit.CHARS
                    except Exception:
                        unit_enum = TweetLengthUnit.CHARS

                    tlp_entity = TweetLengthPolicy(
                        mode=mode_enum,
                        min_length=tlp.get("minLength"),
                        max_length=tlp.get("maxLength"),
                        target_length=tlp.get("targetLength"),
                        tolerance_percent=tlp.get("tolerancePercent", 10),
                        unit=unit_enum,
                    )

                prompt_entity = Prompt(
                    id=str(prompt_doc["_id"]),
                    user_id=str(prompt_doc["userId"]),
                    channel_id=str(prompt_doc["channelId"]) if not isinstance(prompt_doc["channelId"], ObjectId) else str(prompt_doc["channelId"]),
                    prompt_content=PromptContent(
                        system_message=prompt_doc["promptContent"]["systemMessage"],
                        user_message=prompt_doc["promptContent"]["userMessage"]
                    ),
                    language_of_the_prompt=prompt_doc.get("languageOfThePrompt", ""),
                    language_to_generate_tweets=prompt_doc.get("languageToGenerateTweets", ""),
                    max_tweets_to_generate_per_video=prompt_doc.get("maxTweetsToGeneratePerVideo", 0),
                    tweet_length_policy=tlp_entity,
                    created_at=prompt_doc.get("createdAt"),
                    updated_at=prompt_doc.get("updatedAt")
                )
                saved_prompt_id = await prompt_repo.save(prompt_entity)  # type: ignore
                logger.info(f"[ok] prompt saved via repo, id={saved_prompt_id}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
            except Exception:
                await db.get_collection("prompts").replace_one(
                    {"userId": prompt_doc["userId"], "channelId": prompt_doc["channelId"]},
                    prompt_doc,
                    upsert=True
                )
                saved_prompt_id = str(prompt_doc["_id"])
                logger.info(f"[ok] prompt upserted referencing userId={str(MASTER_USER_ID)} and channelId={prompt_doc['channelId']} via direct DB fallback", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
        else:
            await db.get_collection("prompts").replace_one(
                {"userId": prompt_doc["userId"], "channelId": prompt_doc["channelId"]},
                prompt_doc,
                upsert=True
            )
            saved_prompt_id = str(prompt_doc["_id"])
            logger.info(f"[ok] prompt upserted referencing userId={str(MASTER_USER_ID)} and channelId={prompt_doc['channelId']} via direct DB (adapter missing)", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

        # Update the channel to set this prompt as the selected one
        await db.get_collection("channels").update_one( {"_id": channel_ref}, {"$set": {"selectedPromptId": ObjectId(saved_prompt_id)}} )
        logger.info( f"[ok] channel {channel_ref} updated with selectedPromptId={saved_prompt_id}", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name} )

        # array with all the saved prompt IDs (strings) created for each channel
        saved_prompt_ids.append(saved_prompt_id)
    """

    # -----------------------
    # 4) APP CONFIG
    # -----------------------
    scheduler_config = SchedulerConfig(
        ingestion_pipeline_frequency_minutes=1,
        publishing_pipeline_frequency_minutes=1,
        is_ingestion_pipeline_enabled=True,
        is_publishing_pipeline_enabled=True,
    )
    app_config = AppConfig(scheduler_config=scheduler_config)
    app_config_repo = MongoAppConfigRepository(db)
    try:
        await app_config_repo.update_config(app_config)
        logger.info("[ok] app config updated via repo", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    except AttributeError:
        # fallback direct write to the app_config collection (collection name is app_config)
        await db.get_collection("app_config").replace_one(
            {"_id": "global"},
            {
                "_id": "global",
                "schedulerConfig": {
                    "ingestionPipelineFrequencyMinutes": scheduler_config.ingestion_pipeline_frequency_minutes,
                    "publishingPipelineFrequencyMinutes": scheduler_config.publishing_pipeline_frequency_minutes,
                    "isIngestionPipelineEnabled": scheduler_config.is_ingestion_pipeline_enabled,
                    "isPublishingPipelineEnabled": scheduler_config.is_publishing_pipeline_enabled
                }
            },
            upsert=True
        )
        logger.info("[ok] app config upserted directly", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})


    # -----------------------
    # 5) USER SCHEDULER RUNTIME STATUS
    # -----------------------
    # Minimal, idempotent seeding for the runtime status entity.
    try:
        now = _dt.datetime.now(timezone.utc)
        usr_status_coll = db.get_collection("user_scheduler_runtime_status")

        # Ensure unique index on userId to guarantee one status doc per user (safe to call repeatedly)
        try:
            await usr_status_coll.create_index("userId", unique=True)
        except Exception:
            # index creation non-fatal if it already exists or if permissions differ
            logger.debug("Could not create index userId on user_scheduler_runtime_status (may already exist)", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})

        # Document shape aligned with the design
        status_doc = {
            "userId": MASTER_USER_ID,
            "isIngestionPipelineRunning": False,
            "isPublishingPipelineRunning": False,
            "lastIngestionPipelineStartedAt": None,
            "lastIngestionPipelineFinishedAt": None,
            "lastPublishingPipelineStartedAt": None,
            "lastPublishingPipelineFinishedAt": None,
            "nextScheduledIngestionPipelineStartingAt": None,
            "nextScheduledPublishingPipelineStartingAt": None,
            "consecutiveFailuresIngestionPipeline": 0,
            "consecutiveFailuresPublishingPipeline": 0,
            "createdAt": datetime.now(_dt.timezone.utc),
        }

        # Upsert: create if missing, otherwise leave existing runtime values intact but ensure updatedAt exists
        res = await usr_status_coll.update_one(
            {"userId": MASTER_USER_ID},
            {
                "$setOnInsert": status_doc,
                "$set": {"updatedAt": now}
            },
            upsert=True
        )
        if res.upserted_id:
            logger.info("[ok] user_scheduler_runtime_status created for user=%s", str(MASTER_USER_ID), extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
        else:
            logger.info("[ok] user_scheduler_runtime_status ensured for user=%s (already existed)", str(MASTER_USER_ID), extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})
    except Exception as exc:
        logger.exception("Failed to seed user_scheduler_runtime_status: %s", exc, extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})


    logger.info("Script - Seeding data to MongoDB finished.", extra={"module_name": __name__, "function_name": inspect.currentframe().f_code.co_name})


if __name__ == "__main__":
    asyncio.run(seed())
