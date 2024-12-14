# translation_pipeline.py

import os
import requests
import time

class TranslationPipeline:
    def __init__(self, deepl_api_key, nllb_api_key, aya_api_key):
        self.translators = [
            DeepLTranslator(deepl_api_key),
            NLLBTranslator(nllb_api_key),
            AyaTranslator(aya_api_key)
        ]

    def translate(self, chunks, source_lang="EN", target_lang="CS"):
        translated_chunks = []
        for chunk in chunks:
            translated = self._translate_chunk(chunk, source_lang, target_lang)
            translated_chunks.append(translated)
        return translated_chunks

    def _translate_chunk(self, text, source_lang, target_lang):
        for translator in self.translators:
            try:
                return translator.translate(text, source_lang, target_lang)
            except Exception as e:
                print(f"Translation failed with {translator.__class__.__name__}. Error: {e}")
                time.sleep(1)  # Wait before trying the next translator
        raise Exception("All translators failed")


class DeepLTranslator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api-free.deepl.com/v2/translate"

    def translate(self, text, source_lang, target_lang):
        data = {
            "auth_key": self.api_key,
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        response = requests.post(self.base_url, data=data)
        response.raise_for_status()
        return response.json()["translations"][0]["text"]


class NLLBTranslator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.nlpcloud.io/v1/nllb-200-3-3b/translation"

    def translate(self, text, source_lang, target_lang):
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "source": source_lang,
            "target": target_lang
        }
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["translation_text"]


class AyaTranslator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.aya.xyz/v1/translate"

    def translate(self, text, source_lang, target_lang):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["translation"]
