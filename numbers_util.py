import re

def number_parts(number):
    if number == 0:
        return "ноль"
    if number == 1:
        return "бер"
    if number == 2:
        return "ике"
    if number == 3:
        return "өс"
    if number == 4:
        return "дүрт"
    if number == 5:
        return "биш"
    if number == 6:
        return "алты"
    if number == 7:
        return "ете"
    if number == 8:
        return "һигеҙ"
    if number == 9:
        return "туғыҙ"
    if number == 10:
        return "ун"
    if number == 20:
        return "егерме"
    if number == 30:
        return "утыҙ"
    if number == 40:
        return "ҡырҡ"
    if number == 50:
        return "илле"
    if number == 60:
        return "алтмыш"
    if number == 70:
        return "етмеш"
    if number == 80:
        return "һикһән"
    if number == 90:
        return "туҡһан"
    if number == 100:
        return "йөҙ"

    if number > 10 and number < 100:
        suffix=number_parts(number % 10)
        if suffix=="ноль":
            suffix=""
        return number_parts(number // 10 * 10) + " " + suffix
    if number > 100 and number < 1000:
        suffix=number_parts(number % 100)
        if suffix=="ноль":
            suffix=""
        return number_parts(number // 100) + " йөҙ " + suffix

    return None


def int2text(number):
    tmp = number
    parts = []
    while tmp > 0:
        parts.append(number_parts(tmp % 1000))
        tmp = tmp // 1000

    if len(parts)==0:
        parts.append(number_parts(0))

    result = ''
    if len(parts) >= 5 and parts[4] != 'ноль':
        result += parts[4] + " триллион "
    if len(parts) >= 4 and parts[3] != 'ноль':
        result += parts[3] + " миллиард "
    if len(parts) >= 3 and parts[2] != 'ноль':
        result += parts[2] + " миллион "
    if len(parts) >= 2 and parts[1] != 'ноль':
        result += parts[1] + " мең "

    if len(result) == 0 or parts[0] != 'ноль':
        result += parts[0]
    return result

def real2text(number):
    match = re.match(r'^(\d+)[\.,](\d+)$', str(number))
    if match:
        integer_part = int(match.group(1))
        decimal_part = match.group(2)
        # print(integer_part)
        # print(decimal_part)
        decimal_part=decimal_part.rstrip('0')
        if len(decimal_part)>3:
            decimal_part=decimal_part[0:3]
        decimal_prefix=''
        if len(decimal_part)==1:
            decimal_prefix="ундан"
        elif len(decimal_part)==2:
            decimal_prefix="йөҙҙән"
        elif len(decimal_part)==3:
            decimal_prefix="меңдән"
        decimal_part=decimal_part.lstrip('0')
        decimal_part_as_int=int(decimal_part)
        if decimal_part_as_int==0:
            return int2text(integer_part)

        return f'{int2text(integer_part)} бөтөн {decimal_prefix} {int2text(decimal_part_as_int)}'

    return number

def unit2text(txt):
    units_simple=[
           ('кВт','кило ват'),
           ('МВт','мега ват'),
           ('мВт','милли ват'),
           ('ГВт','гига ват'),
           ('мкм','микрометр'),
           ('м²','квадрат метр'),
           ('см²','квадрат сантиметр'),
           ('км²','квадрат километр'),
           ('мм²','квадрат миллиметр'),
           ('мкг','микрограмм'),
           ('кбит/с','килобит секундына'),
           ('Мбит/с','мегабит секундына'),
           ('Гбит/с','гигабит секундына'),
           ('Кбайт','килобайт'),
           ('Мбайт','мегабайт'),
           ('Гбайт','гигабайт'),
           ('Тбайт','терабайт'),
           ('Пбайт','петабайт'),
           ('км/с','километр секундына'),
           ('км/сәғ','километр сәғәтенә'),
           ('м/с','метр секундына'),
           ('%','процент'),
           ('°C','градус'),
           ('°','градус'),
           ]
    units_regex=[('Вт','ват'),
           ('дм','дециметр'),
           ('см','сантиметр'),
           ('км','километр'),
           ('мм','миллиметр'),
           ('л','литр'),
           ('т','тонна'),
           ('га','гектар'),
           ('кг','килограмм'),
           ('мг','миллиграмм'),
           ('мс','миллисекунда'),
           ('мкс','микросекунда'),
           ('нс','наносекунда'),
           ('млн','миллион'),
           ('млрд','миллиард'),
           ]

    for short_name,long_name in units_simple:
        txt=txt.replace(short_name,long_name)
    for short_name,long_name in units_regex:
        r1=(f'(\\d+)\\s*({short_name})(\.|\s)')
        r2=(f'\\1 {long_name} ')
        txt = re.sub(r1, r2, txt)

    return txt

def correct_suffix(number_as_text,hard_suffix="ынсы",soft_suffix="енсе",soft2_suffix="өнсө"):
    hard_vowels=['а', 'ы', 'о', 'я', 'ю','у']
    last_word=number_as_text.lower().split(' ')[-1]
    is_hard=False
    for ch in hard_vowels:
        if ch in last_word:
            is_hard=True
            break
    if number_as_text[-1]=='ы':
        number_as_text=number_as_text[:-1]
    if number_as_text[-1]=='е':
        number_as_text=number_as_text[:-1]

    return number_as_text+(hard_suffix if is_hard else soft2_suffix if 'ө' in last_word else soft_suffix)

def day2text(txt):
    pattern=(f'(\\d+)\\sһәм\\s(\\d+)\\s*(ғинуар\\w*|январ\\w*|феврал\\w*|март\\w*|апрел\\w*|май\\w*|июн\\w*|июл\\w*|авгус\\w*|сентябр\\w*|октябр\\w*|ноябр\\w*|декабр\\w*)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer1_part = int(match.group(1))
            integer2_part = int(match.group(2))
            integer1_txt=int2text(integer1_part)
            integer2_txt=int2text(integer2_part)

            suffix = match.group(3)
            txt=txt[0:match.start()]+correct_suffix(integer1_txt)+" һәм "+correct_suffix(integer2_txt)+" "+suffix+txt[match.end():]
        else:
            break

    pattern=(f'(\\d+)\\s*(ғинуар\\w*|январ\\w*|феврал\\w*|март\\w*|апрел\\w*|май\\w*|июн\\w*|июл\\w*|авгус\\w*|сентябр\\w*|октябр\\w*|ноябр\\w*|декабр\\w*)')
    while True:
        match = re.search(pattern, txt, re.IGNORECASE)
        if match:
            integer_part = int(match.group(1))
            integer_txt=int2text(integer_part)
            suffix = match.group(2)
            txt=txt[0:match.start()]+correct_suffix(integer_txt)+" "+suffix+txt[match.end():]
        else:
            break


    return txt

def rome2number(rome):
    if rome=="I":
        return 1
    if rome=="II":
        return 2
    if rome=="III":
        return 3
    if rome=="IV":
        return 4
    if rome=="V":
        return 5
    if rome=="VI":
        return 6
    if rome=="VII":
        return 7
    if rome=="VIII":
        return 8
    if rome=="IX":
        return 9
    if rome=="X" or rome=="Х":
        return 10
    if rome=="XI":
        return 11
    if rome=="XII":
        return 12
    if rome=="XIII":
        return 13
    if rome=="XIV":
        return 14
    if rome=="XV":
        return 15
    if rome=="XVI":
        return 16
    if rome=="XVII":
        return 17
    if rome=="XVIII":
        return 18
    if rome=="XIX":
        return 19
    if rome=="XX" or rome=="ХХ":
        return 20
    if rome=="XXI":
        return 21

def rome2text(txt):
    pattern=(f'(I|II|III|IV|V|VI|VII|VIII|IX|Х|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|ХХ|XX|XXI)-(I|II|III|IV|V|VI|VII|VIII|IX|Х|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|ХХ|XXI)\\s*(быу\\w*)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer1_part = rome2number(match.group(1))
            integer2_part = rome2number(match.group(2))
            integer1_txt=int2text(integer1_part)
            integer2_txt=int2text(integer2_part)
            suffix = match.group(3)
            txt=txt[0:match.start()]+correct_suffix(integer1_txt)+" "+correct_suffix(integer2_txt)+" "+suffix+txt[match.end():]
        else:
            break

    pattern=(f'(I|II|III|IV|V|VI|VII|VIII|IX|X|Х|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX|ХХ|XXI)\\s*(быу\\w*|дәрәж\\w*)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer_part = rome2number(match.group(1))
            integer_txt=int2text(integer_part)
            suffix = match.group(2)
            txt=txt[0:match.start()]+correct_suffix(integer_txt)+" "+suffix+txt[match.end():]
        else:
            break


    return txt

def when_suffix(number):
    txt=int2text(number)
    if number==10:
        # txt+="да"
        return txt
    if number==20:
        # txt+="лә"
        return txt

    number=int(str(number)[-1])
    if number==1:
        # txt+="ҙә"
        return txt
    if number==2:
        # txt+="лә"
        return txt
    if number==3:
        # txt+="тә"
        return txt
    if number==4:
        # txt+="тә"
        return txt
    if number==5:
        # txt+="тә"
        return txt
    if number==6:
        # txt+="ла"
        return txt
    if number==7:
        # txt+="лә"
        return txt
    if number==8:
        # txt+="ҙә"
        return txt
    if number==9:
        # txt+="ҙа"
        return txt
    return txt

def mont_name_by_number(number):
    if number==1:
        return "ғинуары"
    if number==2:
        return "феврале"
    if number==3:
        return "марты"
    if number==4:
        return "апреле"
    if number==5:
        return "майы"
    if number==6:
        return "июне"
    if number==7:
        return "июле"
    if number==8:
        return "авгусы"
    if number==9:
        return "сентябере"
    if number==10:
        return "октябере"
    if number==11:
        return "ноябере"
    if number==12:
        return "декабере"
def fulldate2text(txt):
    pattern=('(\\d{1,2})[-\\.](\\d{1,2})[-\\.](\\d{4})')
    while True:
        match = re.search(pattern, txt, re.IGNORECASE)
        if match:
            day_part = match.group(1)
            day_txt=int2text(int(day_part))
            month_part = int(match.group(2))
            month_name=mont_name_by_number(month_part)
            year_part = match.group(3)
            txt=txt[0:match.start()]+year_part+" йылдың "+correct_suffix(day_txt)+" "+month_name+" "+txt[match.end():]
        else:
            break
    return txt

def prepare_number_text(txt):
    txt=txt.replace('—','-')
    return txt


def transcript_number_from_raw_text(txt):
    txt=prepare_number_text(txt)
    txt=unit2text(txt)
    # print('unit2text:', txt)
    txt=fulldate2text(txt)
    # print('fulldate2text:', txt)
    txt=day2text(txt)
    # print('day2text:',txt)
    txt=rome2text(txt)
    # print('rome2text:',txt)

    # 2020-2023 йыл
    pattern=(f'(\\d\\d\\d\\d)\-(\\d\\d\\d\\d)\\s(йыл\\w*)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer1_part = int(match.group(1))
            integer1_txt=int2text(integer1_part)
            integer2_part = int(match.group(2))
            integer2_txt=int2text(integer2_part)
            suffix = match.group(3)
            txt=txt[0:match.start()]+correct_suffix(integer1_txt)+" "+correct_suffix(integer2_txt)+" "+suffix+txt[match.end():]
        else:
            break
    # print('2020-2023 йыл:',txt)
    #У084НУ 702
    pattern=('([a-z])(\\d{1})(\\d{1})(\\d{1})([a-z])([a-z])\\s{0,1}(\\d{1,3})')
    while True:
        match = re.search(pattern, txt, re.IGNORECASE)
        if match:
            char1=match.group(1)
            integer1_part = int(match.group(2))
            integer1_txt=int2text(integer1_part)
            integer2_part = int(match.group(3))
            integer2_txt=int2text(integer2_part)
            integer3_part = int(match.group(4))
            integer3_txt=int2text(integer3_part)
            char2=match.group(5)
            char3=match.group(6)
            suffix = match.group(7)
            txt=txt[0:match.start()]+char1+" "+integer1_txt+" "+integer2_txt+" "+integer3_txt+" "+char2+" "+char3+" "+suffix+txt[match.end():]
        else:
            break
    # print('У084НУ 702:',txt)

    # 16-17
    pattern=(f'(\\d+)\-(\\d+)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer1_part = int(match.group(1))
            integer1_txt=int2text(integer1_part)
            integer2_part = int(match.group(2))
            integer2_txt=int2text(integer2_part)
            txt=txt[0:match.start()]+integer1_txt+" "+integer2_txt+" "+txt[match.end():]
        else:
            break
    # print('2020-2023 йыл:',txt)



    #10-сы,10-да
    pattern=(f'(\\d+)-(с[ыеө])')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer_part = int(match.group(1))
            integer_txt=int2text(integer_part)
            suffix = match.group(2)
            txt=txt[0:match.start()]+correct_suffix(integer_txt.strip(),"ын","ен","өн")+suffix+txt[match.end():]
        else:
            break
    # print('10-сы:',txt)
    #10-лаған
    pattern=(f'(\\d+)-(\\w+)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer_part = int(match.group(1))
            integer_txt=int2text(integer_part).strip()
            suffix = match.group(2)
            txt=txt[0:match.start()]+integer_txt+suffix+txt[match.end():]
        else:
            break

    # print('10-лаған:',txt)
    # 1000 йыллыҡ
    pattern=('(?<!\d)(\\d{4})\\s(йыллы\\w*)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer_part = int(match.group(1))
            integer_txt=int2text(integer_part)
            suffix = match.group(2)
            txt=txt[0:match.start()]+integer_txt+" "+suffix+txt[match.end():]
        else:
            break

    # print('1000 йыллыҡ:',txt)
    # 2023 йыл
    pattern=('(?<!\d)(\\d{4})\\s(йыл\\w*)')
    while True:
        match = re.search(pattern, txt)
        if match:
            integer_part = int(match.group(1))
            integer_txt=int2text(integer_part)
            suffix = match.group(2)
            txt=txt[0:match.start()]+correct_suffix(integer_txt)+" "+suffix+txt[match.end():]
        else:
            break

    # print('2023 йыл:',txt)
    # 10:00
    pattern=('(\\d{1,2}):(\\d\\d)\\s*(сәғ\\w*){0,1}')
    while True:
        match = re.search(pattern, txt)
        if match:
            hour_part = int(match.group(1))
            minute_part = int(match.group(2))
            if minute_part==0:
                txt=txt[0:match.start()]+ " сәғәт "+when_suffix(hour_part)+" "+txt[match.end():]
            else:
                hour_txt=int2text(hour_part)
                minute_txt=int2text(minute_part)
                txt=txt[0:match.start()]+hour_txt+ " сәғәт "+minute_txt+" минут "+txt[match.end():]

        else:
            break

    # print('10:00:',txt)
    # -5.1
    pattern=('\\-\\d+[,\\.]\\d+')
    while True:
        match = re.search(pattern, txt)
        if match:
            number = float(match.group(0).replace(",",".")[1:])
            number_txt=real2text(number)
            # print(number_txt)
            txt=txt[0:match.start()]+"минус "+number_txt+ " "+txt[match.end():]

        else:
            break

    # print('-5.1:',txt)

    # -5
    pattern=('\\-\\d+')
    while True:
        match = re.search(pattern, txt)
        if match:
            number = float(match.group(0)[1:])
            number_txt=int2text(number)
            # print(number_txt)
            txt=txt[0:match.start()]+"минус "+number_txt+ " "+txt[match.end():]

        else:
            break

    # print('-5:',txt)

    # 10.4
    pattern=('\\d+[,\\.]\\d+')
    while True:
        match = re.search(pattern, txt)
        if match:
            number = float(match.group(0).replace(",","."))
            number_txt=real2text(number)
            txt=txt[0:match.start()]+number_txt+ " "+txt[match.end():]

        else:
            break

    # print('10.4:',txt)
    # 10
    pattern=('\\d+')
    while True:
        match = re.search(pattern, txt)
        if match:
            number = int(match.group(0))
            number_txt=int2text(number)
            txt=txt[0:match.start()]+number_txt+ " "+txt[match.end():]

        else:
            break

    txt=" ".join(list(filter(None, txt.split(' '))))
    return txt

def test():
    numbers = [1, 12, 23, 55, 60, 100, 101, 245, 1000, 1001, 2034, 3478, 10000,
               20030, 100000, 234567, 1000000, 10000000, 2000000000]
    # numbers = [1000000]
    for n in numbers:
        print(f'{n}={transcript_number_from_raw_text(str(n))}')
