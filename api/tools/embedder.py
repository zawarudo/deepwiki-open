import adalflow as adal

from api.config import configs


def get_embedder() -> adal.Embedder:
    import logging
    logger = logging.getLogger(__name__)
    
    embedder_config = configs["embedder"]
    
    # Debug: Log embedder configuration
    logger.debug(f"Initializing embedder with config: model_client={embedder_config.get('model_client', 'Unknown')}")
    logger.debug(f"Model kwargs: {embedder_config.get('model_kwargs', {})}")
    
    # --- Initialize Embedder ---
    model_client_class = embedder_config["model_client"]
    
    # Debug: Log model client initialization
    if "initialize_kwargs" in embedder_config:
        logger.debug(f"Initializing {model_client_class.__name__} with kwargs: {embedder_config['initialize_kwargs']}")
        model_client = model_client_class(**embedder_config["initialize_kwargs"])
    else:
        logger.debug(f"Initializing {model_client_class.__name__} with default kwargs")
        model_client = model_client_class()
    
    # Debug: Log embedder creation
    logger.debug(f"Creating embedder with model_client={model_client.__class__.__name__}")
    
    embedder = adal.Embedder(
        model_client=model_client,
        model_kwargs=embedder_config["model_kwargs"],
    )
    
    logger.info(f"Embedder initialized: {embedder.__class__.__name__} with {model_client.__class__.__name__}")
    return embedder
