import httpx
import json
import time
import requests
import asyncio
import random
from src.utils import disk
from tqdm import tqdm
from nba_api.live.nba.endpoints import boxscore
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import traceback

def timestamp():
    return datetime.now(timezone.utc).isoformat()

gids = disk.read_json('data/unique_game_ids.json')
gids = gids[-1]['data']
gids = [_['game_id'] for _ in gids]

header_content = """
accept
*/*
accept-encoding
gzip, deflate, br, zstd
accept-language
nb-NO,nb;q=0.9,no;q=0.8,nn;q=0.7,en-US;q=0.6,en;q=0.5
cache-control
no-cache
cookie
nbatag_main_v_id=019d71a08e8c0021001940bbf3e60506f0019067019c0; OptanonAlertBoxClosed=2026-04-09T11:13:49.151Z; eupubconsent-v2=CQiZB7AQiZB7AAcABBENCZFsAP_gAAAAACiQMSgB4CIEQSFBACJwAIoAAAAEQAAAAEAAAAABAAAAAAAABAQAECAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAEgAAAABIAAAAAAAAAAAARKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAATyff7Pn__rl_e7X_ve_n3zv8oXH77r____f_-7___2b_-___b-__7JoAAACQkAYACoAIIAZABoAEwAQgC8wgAIBR4DFh0AcABYAFQAQQAyADQAJgBFgF5jgAQBCAGLEIAIACyUAMABYATAF5kgAIDFikAcABYAFQAQQAyADQAJgBFgF5lAAIDFgAAA.f_wAAAAAAAAA.IMSwRYAFAAaABUADIAIAASAAqABaADIAGgAOgAigBJgCYAJwAWwAvgBhAD8AIAAQgApABlAEAAIQARYAjoBOwEagKPAXgAvMBiwDGQGfANmAbUA20Bt4DcwJwQTjBOYCdME7ATwgnkCfME-wUXgoyCjkFHgUmgpQClcFLQUvgpiCmQFNIKbAqJBUYFSYKlgqxBVoFXoKwAraBW8CuIFcwK7QV4BXoCvkFfgWJgsWCx8FkQXagu4DDMGGwYcgw8DEEGIgYjAxKAAA; s_ecid=MCMID%7C81492290038141589478614812525550188763; canPersist=true; AMCV_248F210755B762187F000101%40AdobeOrg=179643557%7CMCMID%7C81492290038141589478614812525550188763%7CMCAID%7CNONE%7CMCOPTOUT-1775762150s%7CNONE%7CvVersion%7C5.5.0%7CMCIDTS%7C20553%7CMCAAMLH-1776359750%7C6%7CMCAAMB-1776359750%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI; _gid=GA1.2.470863044.1775754997; _ga_XQNG16PXVR=GS2.1.s1775754943$o1$g1$t1775755005$j60$l0$h0; _ga=GA1.2.2059718217.1775754944; _hjSessionUser_2837354=eyJpZCI6ImI1Yzg4MmFhLTc2OGYtNWQwZC04ZGRmLTM0ZTBjMjJiZTRkOSIsImNyZWF0ZWQiOjE3NzU3NTQ5NDg2ODIsImV4aXN0aW5nIjp0cnVlfQ==; bm_mi=CF07E3618B6A993993AB2F8A7CC2019F~YAAQXnchF/O4k2KdAQAABI5ldR/drkmM/Rjj/2IcNYZbVoU7bc9WSKReANtdK32kCaZzPaTR7s4xEpn0yx4icbh/+tUw30vcbkgw1Bd+a5ITz8tBmNfAOU28DAoWF68U9dcTLPhi4LSD17BAOYCqqmBL15pw9zw/OyWYCFMtAqwXypN/FGOMbvxbHPN5ZuWbsdkx4mYHXfXVt6yrWBJGoIEAlWMbVCyESS+FZjHJ0CDxKpBd8FQGDvZIePNP7afLOh0az6/wX36hGLNcb/WORvCvR3JRJu85ytOWBGshzgG+IKp5fqHM8JndHPPplR4=~1; nbatag_main__sn=7; nbatag_main_ses_id=1775791084179%3Bexp-session; nbatag_main_dc_visit=6; nbatag_main__ss=0%3Bexp-session; nbatag_main_dc_region=eu-central-1%3Bexp-session; ab.storage.deviceId.cf150dab-3153-49b0-b48c-66a7c18688ea=%7B%22g%22%3A%22a14abc75-c221-e8a4-aff0-92da6118005a%22%2C%22c%22%3A1775733229794%2C%22l%22%3A1775791084766%7D; AMP_MKTG_2442d50754=JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE; bm_ss=ab8e18ef4e; _abck=F7C1C43FA6297958E1CF4325D30CA083~0~YAAQlwtlX+Eq92OdAQAA76midQ/DwJVzGhNUSAJJpCSrI2spmMMDs+m8kbh09uVBfPC7F9SuHuJ8JfCPiO0TGQoLlYwc++eU8LhMPphg3MsOUyzCDsRm8o0s8shhpZ7toQVjvBZUgh5uPmuz7pDj8wEQ4aFPtXb6gfJNR6mwTCKi6JOxFezllpeQrhSda0ucgDBNH1IVec3VWEA9aIAGJ36Anftn0uri0zMq3ID0a/otONHhACfcLZQPLk98ask3MR0uNOzP5YiqlWGJMGcav4dGU70qfmOVm6rdTqEEw3ywAYWVi6CDmybRF7V0YaHncaNirdQ1vUDcuQ7qpkwsoVel0+zh5iTR2ePo2u/o/ek/QME1gIDWkCfYWPwzxH79TqddIoVg27rSFmCBOrHT4Ct8V/dAqB7l56qGES7ubxNyu/UZbITsq19tE0dtTxAqgg+LIB+/RCUCCqYlizTHNoyJIlqqZYyy9LbJQKKi9QvnNIrWNpwzlXUlLvdToZPP1ofSrElRD5g5gEOU2dFrM8jDQmvvyrAWG1ybISKy00jyFkVYWf9w5kjRlv7zg8dNM38SfOoscKali9e/M8QseOI1cSWHbVxJvldwDH/XX/DI2mquCMAGgqOw7/Y5gh6hCA4ujZr5X7v+mkBCAgiQqTwWqfesZSrxUOGCE60MfecKi1NSpC/Lv4yelDOwkFcK4ktLox3YpjyuwqD3pJ8QEo0ypKJEPpAQy2YIeTt65Dtbo0NX3t42c/RWZfTPm/lx8D9qWanmnoY=~-1~-1~1775798284~AAQAAAAF%2f%2f%2f%2f%2f7FItcB8sJjtplnbmJmst0mVI2jSOaTzlPEySMSVtRTJsySwSRSHSEN2B68QkKDnWrOtW2H4FIBZwbSAeTvEo66lWnGgToxOLJ+aESo41HdUpXUm3VuNTYYRKrkpUuJbnuY2gFdWNkwVW+%2fzSKTJfsFvXwKBQu1w%2fJiJWSrYeboSA5WmWi%2fSynknB9o8wzYydRAd%2ftEu%2fJG%2fPObF9%2fFR2S1VhD0FtJFXCyaYefg5a%2f7VXrk%3d~-1; _cs_mk_aa=0.3907873886704897_1775795089743; bm_so=B1B518F26FAD9C893E7FF6582DA1AC64C153ADB86BBF38569E5BFBA4C85C1310~YAAQlwtlX4wv92OdAQAAaaendQfAtO5xtEkniyZRXd/VmTD238Sr7Mq3XP5ltfiEuQd0WS9ge3IdO0PGRwDWN6BHPs10uNI7Obee9Mmlt9qk+GrGenX+fK/XsiiEmeUjCxU/DgL3Rbn9R2LTQQfi8AmKBKh2WcLm7HZ5vklwNLsGcdRVC2GsL1B0R6Ks/914/7rPq4wgiZlJEzQ+cJcqC7BxlWEBA1BS9FgPJc+gGxJScn8P9B/0MAo1rGJ3yQwajFhUUqTJQfeePvoWpq1pwNYQJAgrHSSRM0MPORDNef40ZiTmjRMdbUbo6by/ENN/LyYQYaeBhPc0DKy+DLtHb92zcNCDsUEhD/4gKgyCq8b+TxAVq4PuZzKR59lcKCfj67tN13kNTGUNdO2J80R2w2J1+wr35F3LBgtqhQzVKS9S4XFBA9jc4Svtg0ILrxLKMVvOmOVwvzqbdhW621+tDxLOFhR26wWVywjqj6dFAlCL+9XJFe6x; iframeRef=www.nba.com/game/mem-vs-bkn-0021300908/box-score; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Apr+10+2026+06%3A30%3A17+GMT%2B0200+(Central+European+Summer+Time)&version=202511.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=f5564860-72ae-4a15-8ab6-602e8a51a37d&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=dsa%3A1%2Ccad%3A1%2CNBAad%3A1%2Cmcp%3A1%2CNBAmt%3A1%2Cpad%3A1%2Cpap%3A1%2Cgld%3A1%2Cpcd%3A1%2Cpcp%3A1%2Cmap%3A1%2Cmra%3A1%2Cpdd%3A1%2Csid%3A1%2Csec%3A1%2Ctdc%3A1%2Ccos%3A1%2Cdlk%3A1%2Cdid%3A1%2Cdsh%3A1%2Cdsl%3A1%2Cven%3A1%2Creq%3A1&AwaitingReconsent=false&intType=1&geolocation=NO%3B03; nbatag_main__pn=12%3Bexp-session; nbatag_main__se=28%3Bexp-session; nbatag_main__st=1775797217191%3Bexp-session; at_check=true; s_gpv_pageModal=nba%3Agames%3Agame-details%3Abox-score; aaCustPrevPage=nba:games:game-details:box-score; s_cc=true; s_ips=2245; __gads=ID=9d31533db7910237:T=1775733229:RT=1775795417:S=ALNI_MbqHDWjDYMzIk1F-NyEdcVAxuMRkA; __gpi=UID=0000139a73d9ab7f:T=1775733229:RT=1775795417:S=ALNI_MbUBVKh9VfIsZqhwnOtLD4sZqN7xQ; __eoi=ID=1c65af6dd079bd46:T=1775733229:RT=1775795417:S=AA-AfjYaQbbstDhV2gY1e295P99o; nbatag_main_dc_event=28%3Bexp-session; nbaOrigin=Page%20View%3A%20Game%20Details%20Box%20Score%7C%7CGames; ab.storage.sessionId.cf150dab-3153-49b0-b48c-66a7c18688ea=%7B%22g%22%3A%22a038162f-24a6-e827-720e-1163acb0f539%22%2C%22e%22%3A1775797218273%2C%22c%22%3A1775791084763%2C%22l%22%3A1775795418273%7D; AMP_2442d50754=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjIwMTlkNzFhMDhlOGMwMDIxMDAxOTQwYmJmM2U2MDUwNmYwMDE5MDY3MDE5YzAlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjIlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzc1NzkxMDg1OTYwJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTc3NTc5NTQxOTQ5OCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMTU4JTJDJTIycGFnZUNvdW50ZXIlMjIlM0EwJTdE; s_tp=3566; s_ppv=nba%253Agames%253Agame-details%253Abox-score%2C66%2C63%2C2339%2C1%2C2; ak_bmsc=F546E8FB3D7C296C1B5869941D308F90~000000000000000000000000000000~YAAQXnchF/ErlGKdAQAAnM6ndR9xjWEkm5OyJKvdTBSJhlmXqKfJgQUy2q1b36lLR5cgK0B++c+WCU1Oad5uJHdjErrSH/68pFyQaxZ/t3U9jovWkAq5OtKTpTRkQxKp4Csg4/bFV0NHqyjUGHPgDQ4ehPBa0MzAkjzw6nFiSwdjXn4OOUU2lSCmMVrGyotx624FmvvJF8SoLSngl3UH2/CHq/HM88eYtcSwq8+BBvIbGHXpFXMN+mF2eAV/XyBtIcsw43Xcr/dddXWkV0mBSzrySubQIzyYDuJnULre9Tz/A6cirymHeclPHpfO+9yOEokWAlZiyzbNCTC6Yhn+lQrklM1nXF/CxsezAUOhq5ZtSwrCT+o4rb7vfQKAsqCqsnWA56blZ9HwDunnWyjg5tK3UFI92hoLca7ew9uCXGSGkio7zT8a6ot1lHgy9y6TNNRMamMqXKb7wtdnX2ryG7AQ589COwHRXTJ9vKvJPcFvu0BgmrQ7AE+L7LMp+a0V9xscpH/9NYRN6w==; bm_s=YAAQXnchF/IrlGKdAQAAnM6ndQX0wraz8tPSocqmkr4w/XfwVNyvFTFetQZW/SZG1ASAdFB2TEVrf99AwvpPal0hOMyh3ooxFCqbyCPwsa8PJ/NRX7WkQd7THC1weczWstXQ85TuAqGqtLCMD6P80Xa0W+CEFy005bdCgqnAvolHVFBP9xJi/QsP9fs+Frw48NtecJaSx9i/2JA49aoyuf8FweRaWnwu4EW+hOX67fIu+rwhZm93649lG+bxkBoVPfYxLjT+cWAqS1MPNHthLoOPnrS3Hxsj1s/HwEqIqn+2PN71nyJ2o9fuJlxbBhg+Ljnqls5A9294B7tBJ9S7PVxvSb/BTX2dV+iS6RW6RLYbS77oS6MZ6IdGEv9aUD2ZTWBTFS1Cj4/oTR7fQVQL3rsO1DQ6KeXuNn6ezpNVdj38CAEnSSm8F7mVxfnv7bz6ynaLksAVHb0qvVTpECMfkFsOe8wBO+OOuKu71YZQFLeI6G+gLjWkTD47tpIx0/XRyxFxQbmcl8tWve9/pu/wnlnfMqHO8hRGnLsXbo8Dk/1fqjBSrP3UADffsYes4IVzMif6QFa6y55sc+nmag9yxnt11W4ZeqZm9/rj5pMYn8olqCTqH3PkMpYz9t/WgofS9FlBVQMhvH7OUTHOKNcK+IcpQCOCgulQaLArZgJMZmCub46fCBNs2P1FCRD1rpOzPoBcNxzCxTBzoQQ0v+ZsKNhaimD+RdJAnGwNToIgP/x/ILyeYi8DwdK9XyI1U2jMsJIl/5+tTeFFwitcC0WJY4FSwdPQcZ6qWZxwy6UldRtkuUHB2m1xKVBrijtIzngilIbXdJ8PG+QJTWe1yMpMZt3miLPYnyCa1cXIDY8f4+rGBGLzegU54/kIbFurMAoeudItMXyRizNyK6NV3btR02ornqey5TeyhgnjgVognybi6ke0BYVUjMErtgIWA6GCS0Py9hqWQFwOCXjP7sF9BI5lFgzX2INhJq63F8VtMD0BUfbq+JG8OABmnmI=; bm_sv=A234BD4DCCCBF7F480613BC4F4B4D628~YAAQXnchF/MrlGKdAQAAnM6ndR/X+eIzLV8Zy+1TOClWlD5sL+yR79C7yfcQOYq9IJyF3lSL+WevJGMAbW60W35v9ZXSN0yo1X9nyRwcGDh2wS1BrHft9j/mLrsizr51VzumSQvg8vxjjl4bmG9qShYeqKhfMAF78hyVm2+9ueMpCLEItVW+cav0sH04qIlc6i0+sGSFIzJLmuNXjLRYVV12zCcacjufvCBU/6RysAmAx2AewA73Rv/MirKXgA==~1; bm_sz=B50DBEF5E27D8777BCA40535DD907D51~YAAQXnchF/QrlGKdAQAAnM6ndR+leCUSTUDtGLzru47hJE+ioNvZZ2D5zxGFpwGGaRf+Uk8Dak/xGbTGnLwX+o0VzztJdcQlfT6ak2W9VRYmQ0QwGJJNMH9Lpteg3ZSOb/lCBkMi8upADXmxiMLuYnP1T+W8FCbNiukuqo1vYLgaT5enGYp+tW1W9PmIew2ctqnu5pwHKJIpe3pfu2UPb03vvWFQGD0M2Jx5qHn3Li5gPvH+HFWPgLQQKac32O+WSIFdyYRfC+Us+tGX2rSgL1/CsIKTdeXOazL8IR2j87UxmizUi7DVjDykyZwH4LmIoVLqddtGkh/Z+NRxm0c4vbSWmQrO5c9EedHxmEzvvtgF0Rp/PWYooVqMpFNb7pu5QxtX11zQPkDAczf0rnyRx2sdOrRi45ry3ZDEhbkH/neLN0+AHk0CLXf7uqJ1STwdmdOwzkqVYi17wLQns8XzWoKIQ79dPWDkzBEpn2JMq7p81oMbAVIA2H4BVqU+oDqrNMR7qbnRH5UaD8Q0EoVEG9termlOJw==~4277301~3552825
pragma
no-cache
referer
https://www.nba.com/
sec-ch-ua
"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"
sec-ch-ua-mobile
?0
sec-ch-ua-platform
"Windows"
sec-fetch-dest
script
sec-fetch-mode
no-cors
sec-fetch-site
same-site
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36
""".strip()


headers = {}

for idx, line in enumerate(header_content.split('\n')):
    if idx % 2 == 0:
        key = line.strip()
    else:
        value = line.strip()
        headers[key] = value

def download_boxscore(game_ids: list[str], output_dir: str = 'data/boxscores', batch_size: int = 10, limit=None, headers: dict = {}, timeout: int = 10, sleep_range: tuple[float, float] = (1, 5)):
    url_ = lambda game_id: f'https://www.nba.com/game/{game_id}/game-charts'
    out_ = lambda game_id: disk.joinpath(output_dir, 'data', f'{game_id}.json')
    error_log = disk.joinpath(output_dir, 'errors.jsonl')


    def download_boxscore(game_id: str):
        url = url_(game_id)
        out = out_(game_id)

        if disk.isfile(out):
            print(f'{out} already exists, skipping...')
            return 1, True, 0

        rsp = None

        try:    
            rsp = requests.get(url, headers=headers, timeout=timeout)
        except Exception as e:
            disk.write_jsonl(error_log, {
                'timestamp': timestamp(),
                'type': 'request_error',
                'game_id': game_id,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'url': url,
            })
            return 0, False, 10


        if rsp.status_code != 200:
            disk.write_jsonl(error_log, {
                'timestamp': timestamp(),
                'type': 'response_error',
                'game_id': game_id,
                'status_code': rsp.status_code,
                'text': rsp.text,
                'headers': dict(rsp.headers),
                'url': url,
            })

            return 0, False, 10

        soup = BeautifulSoup(rsp.text, 'html.parser')
        contents = soup.find_all(attrs={'type': 'application/json'})

        body = []

        for content in contents:    
            try:
                body.append({
                    'type': 'json',
                    'data': json.loads(content.text),
                    'error': None
                })
            except Exception as e:
                body.append({
                    'type': 'text',
                    'data': content.text,
                    'error': str(e)
                })


        log = dict(
            timestamp=timestamp(),
            url=url,
            game_id=game_id,
            headers=dict(rsp.headers),
            status_code=rsp.status_code,
            body=body,
            text=rsp.text,
        )

        disk.write_json(out, log)

        return 1, False, 0
    
    N = 0
    C = 0
    batches = [game_ids[i:i+batch_size] for i in range(0, len(game_ids), batch_size)]

    disk.makedirs(disk.joinpath(output_dir, 'data'), exist_ok=True)

    with tqdm(total=len(game_ids)) as pbar:
        
        for batch in batches:
            flags = [download_boxscore(game_id) for game_id in batch]
            counts, skip_wait, extra_wait = zip(*flags)
            N += sum(counts)
            C += len(counts)
            extra_wait = sum(extra_wait)

            duration = random.uniform(*sleep_range) + extra_wait
            pbar.set_description_str(f'({N}/{C}) - Sleep: {duration:.2f}s')
            pbar.update(len(counts))
                
            if not all(skip_wait) or extra_wait > 0:
                time.sleep(duration)

            if isinstance(limit, int) and N >= limit:
                print(f'Limit of {limit} reached, stopping download.')
                return


if __name__ == '__main__':
    download_boxscore(
        gids, 
        batch_size=1, 
        output_dir='data/boxscores',
        limit=None,
        headers=headers,
        timeout=60,
        sleep_range=(5, 20)

    )