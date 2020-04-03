import os
import re
import io
import sys
import requests
import urllib.parse
import json

path = "metadata"

source_lang = "de-DE"
deepl_langs = ["en", "fr", "es", "it", "nl", "pl", "ru"]
deepl_api_key = ""
google_api_key = ""
path_to_i18n_languages = "" #/Users/.../App/I18n/languages/
deepl_base_uri = 'https://api.deepl.com/v2/translate?auth_key=' + deepl_api_key
google_base_uri = 'https://translation.googleapis.com/language/translate/v2?key=' + google_api_key
max_texts_in_one_request = 50
force_translation = False

def check_translation_exists(target_file, target_dir):
  for root, dirs, files in os.walk("./metadata/" + target_dir):
    for file in files:
      if file == target_file:
        txt_content = io.open("./" + path + "/" +target_dir+ "/"+ file, mode="r", encoding="utf-8").read()
        if txt_content != "" or txt_content == "%0A":
          return True
        else:
          print(target_dir)
          return False

def gen_app_store_texts_to_translate(target_dir):
  texts_to_translate = []
  for root, dirs, files in os.walk("./metadata/de-DE"):
    for file in files:
      if len(files) <= max_texts_in_one_request:
       if not check_translation_exists(file, target_dir) or force_translation:

          source_txt = io.open("./" + path + "/" +source_lang+ "/" + file, mode="r", encoding="utf-8").read()
          source_txt_encoded = urllib.parse.quote(source_txt.encode('utf8'))
          texts_to_translate.append({file: source_txt_encoded})
          #texts_to_translate = texts_to_be_translated + "&text=" + master_txt_encoded
      else:
        print("Max 50 texts in one request allowed")
  return texts_to_translate


#Only Folders with a name like en-US, fr-FR, it, nl are matched
reg_compile = re.compile("^[a-z]{2}(?:-[A-Z]{2})?$")

def translate_app_store_entry():
  for root, dirs, files in os.walk("./" + path):
    for dir in dirs:
      if reg_compile.match(dir) and dir != source_lang:
        target_lang = dir.split("-")[0]
        print(target_lang)
        texts_to_translate = gen_app_store_texts_to_translate(dir)
        print(texts_to_translate)
        if (len(texts_to_translate) > 0):
          translate_app_string(target_lang)
          if target_lang in deepl_langs:
            to_be_translated = ""
            print(texts_to_translate)
            for index, text in enumerate(texts_to_translate):
              print(" - " + list(text.keys())[0])
              to_be_translated = to_be_translated + "&text=" + list(text.values())[0]
            req = requests.get(deepl_base_uri + to_be_translated + '&source_lang='+source_lang.split("-")[0]+'&target_lang='+target_lang.split("-")[0])
            translations = req.json()["translations"]
            for index, translation in enumerate(translations):
              fileName = list(texts_to_translate[index].keys())[0]
              slaveFile = io.open(path + "/" + dir + "/" + fileName, "w", encoding="utf8")
              slaveFile.write(translation["text"])
          else:
            to_be_translated = ""
            for index, text in enumerate(texts_to_translate):
              print(" - " + list(text.keys())[0])
              to_be_translated = to_be_translated + "&q=" + list(text.values())[0]
            req = requests.get(google_base_uri + to_be_translated + '&source='+source_lang.split("-")[0]+'&target='+target_lang.split("-")[0])
            translations = req.json()["data"]["translations"]
            for index, translation in enumerate(translations):
              fileName = list(texts_to_translate[index].keys())[0]
              targetFile = io.open(path + "/" + dir + "/" + fileName, "w", encoding="utf8")
              targetFile.write(translation["translatedText"])


def gen_app_texts_to_translate(data):
  texts_to_translate = ""
  for dataElement in data:
    text = data[dataElement]
    txt_encoded = urllib.parse.quote(text.encode('utf8'))
    texts_to_translate = texts_to_translate + "&q=" + txt_encoded
  return texts_to_translate


def translate_app_string(target_lang):
  translate_to = target_lang
  data = ""
  with io.open(path_to_i18n_languages + "de.json", 'r', encoding='utf8') as f:
    data = json.load(f)
    translation_keys = []
    for key in data.keys():
      translation_keys.append(key)
    #print(translation_keys[0])
    texts_to_translate = gen_app_texts_to_translate(data)
    req = requests.get(google_base_uri + texts_to_translate +"&source=de&target="+translate_to)
    response = req.json()
    translatedStrings = {}
    translations = response["data"]["translations"]
    #print(data)
    for index, translation in enumerate(translations):
      translatedStrings.update({translation_keys[index]:translation["translatedText"]})
    print(translatedStrings)


  with io.open(path_to_i18n_languages + translate_to+".json", 'w', encoding='utf8') as f:
    newData = json.dumps(translatedStrings, ensure_ascii=False, indent=4)
    f.write(newData)
