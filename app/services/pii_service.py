"""PII/PHI protection service using Microsoft Presidio."""
from typing import List, Dict, Any
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from app.config import settings
from app.utils.logger import logger


class PIIService:
    """Service for detecting and anonymizing PII/PHI data."""

    def __init__(self):
        """Initialize Presidio analyzer and anonymizer."""
        # Setup NLP engine with spaCy
        nlp_configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_lg"}]
        }

        provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
        nlp_engine = provider.create_engine()

        # Create analyzer
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=["en"]
        )

        # Create anonymizer
        self.anonymizer = AnonymizerEngine()

        # Entities to detect (financial + medical)
        self.entities = [
            "PERSON",              # Person names
            "EMAIL_ADDRESS",       # Email addresses
            "PHONE_NUMBER",        # Phone numbers
            "LOCATION",            # Addresses, cities, states
            "DATE_TIME",           # Dates and times
            "CREDIT_CARD",         # Credit card numbers
            "IBAN_CODE",           # Bank account numbers (IBAN)
            "US_SSN",              # Social Security Numbers
            "US_BANK_NUMBER",      # US Bank account numbers
            "US_DRIVER_LICENSE",   # Driver's license numbers
            "US_PASSPORT",         # Passport numbers
            "MEDICAL_LICENSE",     # Medical license numbers
            "IP_ADDRESS",          # IP addresses
            "CRYPTO",              # Cryptocurrency addresses
            "URL",                 # URLs (may contain sensitive info)
        ]

        logger.info("PII Service initialized with Presidio")

    def analyze_text(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Analyze text for PII/PHI entities.

        Args:
            text: Text to analyze
            language: Language code

        Returns:
            List of detected PII entities
        """
        try:
            results = self.analyzer.analyze(
                text=text,
                entities=self.entities,
                language=language,
                score_threshold=settings.PRESIDIO_ANALYZER_SCORE_THRESHOLD
            )

            # Convert results to dictionaries
            pii_results = []
            for result in results:
                pii_results.append({
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                })

            if pii_results:
                logger.info(f"Detected {len(pii_results)} PII entities in text")

            return pii_results

        except Exception as e:
            logger.error(f"Error analyzing text for PII: {str(e)}")
            return []

    def anonymize_text(
        self,
        text: str,
        language: str = "en",
        anonymization_method: str = "replace"
    ) -> str:
        """
        Anonymize PII/PHI in text.

        Args:
            text: Text to anonymize
            language: Language code
            anonymization_method: Method to use (replace, mask, redact, hash, encrypt)

        Returns:
            Anonymized text
        """
        try:
            # Analyze text first
            analyzer_results = self.analyzer.analyze(
                text=text,
                entities=self.entities,
                language=language,
                score_threshold=settings.PRESIDIO_ANALYZER_SCORE_THRESHOLD
            )

            if not analyzer_results:
                return text

            # Define anonymization operators
            operators = {}

            if anonymization_method == "replace":
                # Replace with entity type placeholder
                for entity_type in self.entities:
                    operators[entity_type] = OperatorConfig("replace", {"new_value": f"<{entity_type}>"})

            elif anonymization_method == "mask":
                # Mask with asterisks
                for entity_type in self.entities:
                    operators[entity_type] = OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 100})

            elif anonymization_method == "redact":
                # Completely remove
                for entity_type in self.entities:
                    operators[entity_type] = OperatorConfig("redact", {})

            elif anonymization_method == "hash":
                # Hash the value
                for entity_type in self.entities:
                    operators[entity_type] = OperatorConfig("hash", {})

            else:
                # Default to replace
                for entity_type in self.entities:
                    operators[entity_type] = OperatorConfig("replace", {"new_value": f"<{entity_type}>"})

            # Anonymize
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results,
                operators=operators
            )

            logger.info(f"Anonymized {len(analyzer_results)} PII entities from text")

            return anonymized_result.text

        except Exception as e:
            logger.error(f"Error anonymizing text: {str(e)}")
            # Return original text if anonymization fails (safer than losing data)
            return text

    def detect_and_anonymize(
        self,
        text: str,
        language: str = "en",
        anonymization_method: str = "replace"
    ) -> Dict[str, Any]:
        """
        Detect PII and return both analysis and anonymized text.

        Args:
            text: Text to process
            language: Language code
            anonymization_method: Anonymization method

        Returns:
            Dictionary with detected entities and anonymized text
        """
        # Analyze
        detected_entities = self.analyze_text(text, language)

        # Anonymize
        anonymized_text = self.anonymize_text(text, language, anonymization_method)

        return {
            "original_text": text,
            "anonymized_text": anonymized_text,
            "detected_entities": detected_entities,
            "entity_count": len(detected_entities)
        }

    def is_sensitive_content(self, text: str, threshold: int = 3) -> bool:
        """
        Check if text contains sensitive PII/PHI content.

        Args:
            text: Text to check
            threshold: Minimum number of entities to consider sensitive

        Returns:
            True if sensitive content detected
        """
        detected = self.analyze_text(text)
        return len(detected) >= threshold


# Global PII service instance
pii_service = PIIService()
