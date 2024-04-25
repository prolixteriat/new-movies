import json
from ask_sdk_model import ui
from utils import create_presigned_url


# ----------------------------------------------------------------------
# APL Document file paths for use in handlers
APL_DOC = {}
APL_DOC['launch'] = 'launch_doc.json'
APL_DOC['movie_list'] = 'movie_list_doc.json'
APL_DOC['movie_detail'] = 'movie_detail_doc.json'

# ----------------------------------------------------------------------
# Tokens used when sending the APL directives
MOVIES_TOKEN = "new_movies_token"


# ----------------------------------------------------------------------
def create_url(key):
    img_url_raw = str(ui.Image(large_image_url=create_presigned_url(key)))
    length = len(img_url_raw)
    return img_url_raw[21:length-28]


# ----------------------------------------------------------------------
def _load_apl_document(file_path):
    """ Load the apl json document at the path into a dict object. """
    with open(file_path) as f:
        return json.load(f)
