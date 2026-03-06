import re
import asyncio
import urllib.request
from typing import Dict
from .models import ObservationDay, AirPoint, Wind

WIND_DIR_MAP = {
    "Север": "С",
    "Северо-Восток": "СВ",
    "Восток": "В",
    "Юго-Восток": "ЮВ",
    "Юг": "Ю",
    "Юго-Запад": "ЮЗ",
    "Запад": "З",
    "Северо-Запад": "СЗ",
}


def _map_cloudiness(desc: str) -> str:
    d = desc.lower()
    if "ясно" in d:
        return "ясная"
    if re.search(r"местами|переменная", d):
        return "переменная"
    if re.search(r"\bдождь\b|сплошная|пасмурно|снег|гроза|туман", d):
        return "сплошная"
    return "переменная"


def _date_to_url(date: str) -> str:
    y, m, d = date.split("-")
    return f"https://goodmeteo.ru/pogoda-sochi/{int(d)}-{int(m)}/"


def _fetch_html(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def _parse(html: str, date: str) -> ObservationDay:
    # --- Облачность ---
    desc_m = re.search(r'class="dt-bl-weather-desc">([^<]+)', html)
    cloudiness_raw = desc_m.group(1).strip() if desc_m else ""
    cloudiness = _map_cloudiness(cloudiness_raw)

    # --- Блок с осадками и ветром ---
    info_m = re.search(
        r'class="dt-bl-weather-info">(.*?)</div>', html, re.DOTALL
    )
    precip_mm = None
    wind = None

    if info_m:
        info = info_m.group(1)

        # Осадки: <b>Дождь:</b> 4,0 мм  (только если есть "мм")
        prec_m = re.search(r"<b>[^<]+</b>\s*([\d,]+)\s*мм", info)
        if prec_m:
            precip_mm = float(prec_m.group(1).replace(",", "."))

        # Ветер: <b>Ветер:</b> 3,1 м/с, Юго-Восток
        wind_m = re.search(r"<b>Ветер:</b>\s*([\d,]+)\s*м/с,?\s*([^<]+)", info)
        if wind_m:
            speed = float(wind_m.group(1).replace(",", "."))
            dir_raw = wind_m.group(2).strip()
            dir_abbr = WIND_DIR_MAP.get(dir_raw)
            if dir_abbr:
                wind = Wind(speed_mps=speed, dir=dir_abbr)

    # --- Почасовая таблица: 07:00, 13:00, 20:00 ---
    HOURS = {"07:00", "13:00", "20:00"}
    row_re = re.compile(
        r'<td class="h-time-cell">(\d{2}:\d{2})</td>'
        r'<td class="h-temp-cell">([+-]?\d+[.,]\d+)°</td>'
        r".*?"
        r'<td class="h-humidity-cell"><span class="h-bold">(\d+)</span>%</td>',
        re.DOTALL,
    )

    air_map: Dict[str, AirPoint] = {}
    for m in row_re.finditer(html):
        t = m.group(1)
        if t in HOURS:
            temp = float(m.group(2).replace(",", "."))
            rh = float(m.group(3))
            air_map[t] = AirPoint(time=t, temp_c=temp, rh_pct=rh)

    air = [
        air_map.get(t, AirPoint(time=t, temp_c=None, rh_pct=None))
        for t in ["07:00", "13:00", "20:00"]
    ]

    return ObservationDay(
        date=date,
        cloudiness=cloudiness,
        precip_mm=precip_mm,
        wind=wind,
        air=air,
    )


async def fetch_day(date: str) -> ObservationDay:
    url = _date_to_url(date)
    loop = asyncio.get_event_loop()
    html = await loop.run_in_executor(None, _fetch_html, url)
    return _parse(html, date)
