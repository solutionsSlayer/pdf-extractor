"""
Configuration pour l'extracteur LangChain
"""

import os
from typing import Dict, Any

# Configuration Ollama
OLLAMA_CONFIG = {
    "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    "model_name": os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
    "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
    "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "4096")),
    "timeout": int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 5 minutes
}

# Configuration de l'extraction
EXTRACTION_CONFIG = {
    "max_retries": int(os.getenv("MAX_RETRIES", "3")),
    "retry_delay": float(os.getenv("RETRY_DELAY", "1.0")),
    "batch_size": int(os.getenv("BATCH_SIZE", "5")),
    "enable_confidence_scoring": os.getenv("ENABLE_CONFIDENCE_SCORING", "true").lower() == "true"
}

# Configuration des chemins
PATHS_CONFIG = {
    "extracted_data_dir": os.getenv("EXTRACTED_DATA_DIR", "extracted_data"),
    "output_dir": os.getenv("OUTPUT_DIR", "structured_output"),
    "logs_dir": os.getenv("LOGS_DIR", "logs")
}

# Configuration du logging
LOGGING_CONFIG = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_enabled": os.getenv("LOG_TO_FILE", "true").lower() == "true",
    "console_enabled": os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"
}

# Prompts personnalisés (optionnel)
CUSTOM_PROMPTS = {
    "system_prompt_prefix": os.getenv("SYSTEM_PROMPT_PREFIX", ""),
    "system_prompt_suffix": os.getenv("SYSTEM_PROMPT_SUFFIX", ""),
    "few_shot_examples": os.getenv("ENABLE_FEW_SHOT", "false").lower() == "true"
}

def get_config() -> Dict[str, Any]:
    """Retourne la configuration complète"""
    return {
        "ollama": OLLAMA_CONFIG,
        "extraction": EXTRACTION_CONFIG,
        "paths": PATHS_CONFIG,
        "logging": LOGGING_CONFIG,
        "prompts": CUSTOM_PROMPTS
    }

def validate_config() -> bool:
    """Valide la configuration"""
    try:
        # Vérification des types
        assert isinstance(OLLAMA_CONFIG["temperature"], float)
        assert 0.0 <= OLLAMA_CONFIG["temperature"] <= 2.0
        assert isinstance(OLLAMA_CONFIG["num_predict"], int)
        assert OLLAMA_CONFIG["num_predict"] > 0
        
        # Vérification des chemins
        import pathlib
        for path_key, path_value in PATHS_CONFIG.items():
            if path_value:
                pathlib.Path(path_value).mkdir(parents=True, exist_ok=True)
        
        return True
    except Exception as e:
        print(f"Erreur de validation de la configuration : {e}")
        return False 