import re
import traceback
import pytz
from datetime import datetime
from unidecode import unidecode
MINUS_SIGN = '[-~]'
NUMBER = r'\d+[.,]\s*\d{2}'


def get_item_name(item_name):
    item_alphas = len([c for c in item_name if c.isalpha() and c not in ['B', 'E']])
    # don't count pcs (pieces) as item name
    if 'ks' in item_name[:3] or ' ks' in item_name:
        item_alphas -= 2
    # don't count weight units as item name
    if 'kg' in item_name:
        item_alphas -= 2
    if item_alphas > 1:
        return item_name


def fix_item_name(name):
    name = ' '.join(name.split())
    name = f"{name[:-1]}g" if name[-1] == '9' else name

    typos = [(' .', '.'), (' ,', '.'), (' ml', ' ml'), (' m1', ' ml'), (' m}', ' ml')]
    name = name.replace(' .', '.').replace(' ,', ',').replace(' m|', ' ml').replace(' m1', ' ml')

    # Extra manual fixes
    name = name.replace('najmeng', 'najmens')
    name = re.sub(r'( \d+)\*', lambda pat: f"{pat.group(1)}%", name)
    name = re.sub(r'( \d+[94])', lambda pat: f"{pat.group(1)[:-1]}g", name)  # g sometimes read as 9 or 4
    return name


def get_sub_price(price):
    print(f"EXTRACTING SUBPRICE FROM {price=}")
    if price_amount := re.search(r'\d+,\d+', price):
        return round(float_sk(price_amount.group(0)), 2)

    if price_str := re.search(r'[^,.]+(\d+)\s+[.,]?(\d{2})\s*[BCE]', price):
        return int(price_str.group(1)) + int(price_str.group(2)) / 100

    if cents := re.search(r'\d{2}', price):
        # Assume it was .cents
        return round(int(cents.group(0)) / 100, 2)


def is_discount(raw_text):
    raw_text = unidecode(raw_text.lower().replace(' "', ' -').replace(' ~', ' -'))
    if re.search(r'z.ava', raw_text) or re.search(r'zaloh.?a', raw_text) or re.search(r'-\d', raw_text):
        return True


def get_discount_from_item(item):
    # TODO: Replace CHANGING "8 to -0 with a fix
    try:
        # raw_text = ' '.join([i[1] for i in item]).lower().replace(' "8', ' -0').replace(' "', ' -').replace(' ~', ' -')
        # raw_text = unidecode(raw_text)

        # Note: 'zaloha' should not be deducted from the item's price in the future
        raw_text = ' '.join([i[1] for i in item]).lower().replace(' "8', ' -0')
        raw_text = re.sub(r' "(\d)', lambda pat: f" -{pat.group(1)}", raw_text)
        if not is_discount(raw_text):
            return 0
        # if not re.search(r'z.ava', raw_text) and not re.search(r'zaloh.?a', raw_text) and '-' not in raw_text:
        #     return 0
        try:
            amount = int(re.search(r' (\d+) ', raw_text).group(1))
        except:
            print(f"CAN'T GET AMOUNT FROM {raw_text} defaulting to 1")
            amount = 1
        discount_price = re.search(rf'{MINUS_SIGN}({NUMBER})', raw_text).group(1)
        discount_price = round(float_sk(''.join(discount_price.split())), 2)
        print(f"GOT DISCOUNT FROM {raw_text} {amount=} {discount_price=}")
        return round(amount * discount_price, 2)
    except Exception as e:
        print(f"MAY HAVE SKIPPED A DISCOUNT: {' '.join([i[1] for i in item])}, e={e}")
        return 0


def get_shop(receipt):
    shops = {
        'yeme': ('yeme', '2024133650', '47793155'),
        'kaufland': ('kaufland', '2020234216', '35790164'),
        'lidl': ('lidl', 'lsdl', '2020279415', '35793783')}
    receipt_shop = ''
    for shop, shop_aliases in shops.items():
        for shop_alias in shop_aliases:
            receipt_shop = shop if shop_alias in receipt else receipt_shop
            if receipt_shop:
                break
        if receipt_shop:
            break

    # Try regex as well (experimental)
    receipt_shop = 'lidl' if re.search(r'lid[}]', receipt) else receipt_shop
    return receipt_shop


def float_sk(num_str):
    return float(num_str.replace(',', '.'))


def get_shopping_date(receipt):
    if dt := re.search(r'(\d{2}-\d{2}-\d{4})\s*(\d{2})[.:;](\d{2})[.:;](\d{2})', receipt):  # Yeme, Lidl
        date = dt.group(1)
        hour, minute, second = dt.group(2), dt.group(3), dt.group(4)
        return f"{date} {':'.join([hour, minute, second])}"


def fix_amount_int(amount):
    return int(amount.replace('i', '1').replace('{', '1'))


def get_iso_from_slovak_dt_str(slovak_dt):
    input_format = "%d-%m-%Y %H:%M:%S"
    source_timezone = pytz.timezone("Europe/Bratislava")

    # Parse the input string as a datetime object in the source timezone
    source_datetime = datetime.strptime(slovak_dt, input_format)
    source_datetime = source_timezone.localize(source_datetime)

    # Convert the datetime to UTC
    return source_datetime.astimezone(pytz.utc).isoformat()


def get_phone_input():
    while True:
        phone = input("Please input last 3 digits of your phone number: ")
        if phone.isdecimal():
            return phone
        print("Use only digits, try again.")
