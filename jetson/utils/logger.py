# jetson/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(config: dict) -> logging.Logger:
    """Configurer logger avec rotation de fichiers"""
    
    # Créer dossier logs
    log_file = Path(config['file'])
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Logger
    logger = logging.getLogger()
    logger.setLevel(config['level'])
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler fichier avec rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config['max_size_mb'] * 1024 * 1024,
        backupCount=config['backup_count']
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger