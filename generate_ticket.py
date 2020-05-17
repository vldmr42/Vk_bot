from io import BytesIO

import requests
from PIL import Image, ImageFont, ImageDraw

TEMPLATE_PATH = 'files/ticket_template.png'
FONT_PATH = 'files/Roboto-Regular.ttf'
FONT_SIZE = 20
BLACK = (0, 0, 0, 255)
NAME_OFFSET = (230, 325)
EMAIL_OFFSET = (230, 355)
AVATAR_SIZE = 95
AVATAR_OFFSET = (70, 315)

def generate_ticket(name, email):
    base = Image.open(TEMPLATE_PATH).convert('RGBA')
    fnt = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    draw = ImageDraw.ImageDraw(base)
    draw.text(NAME_OFFSET, name, font=fnt, fill=BLACK)
    draw.text(EMAIL_OFFSET, email, font=fnt, fill=BLACK)

    response = requests.get(f'https://api.adorable.io/avatars/{AVATAR_SIZE}/{email}.png')
    avatar_file_like = BytesIO(response.content)
    avatar = Image.open(avatar_file_like)
    base.paste(avatar, AVATAR_OFFSET)

    temp_file = BytesIO()
    base.save(temp_file, 'PNG')
    # base.save('files/my1.png', 'PNG')
    temp_file.seek(0)

    return temp_file


# generate_ticket('NAME', 'EMAIL')
