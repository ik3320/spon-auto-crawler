import time
import random
import requests

# 구글 앱스 스크립트 웹 앱 URL
GAS_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxeGQeWAo1DFLmXiFDe00ERYM54mxKTJTeV6jUtAAqlz391Scyg1exmAHgY1L9UQcIbzg/exec"

print(">> 구글 시트로부터 스폰 API 대상 목록을 조회하는 중...")

try:
    # [수정/추가 포인트 1] doGet을 호출하여 시트의 스폰 API 목록 주소를 가져옵니다.
    # 만약 "스타대학2" 시트를 업데이트하고 싶다면 action 파라미터 끝에 2를 붙여 "getSponTargetList2"로 변경하세요.
    get_url = f"{GAS_WEBAPP_URL}?action=getSponTargetList"
    response = requests.get(get_url)
    target_streamers = response.json()  # 이 단계에서 target_streamers 변수가 정상 정의됩니다!
    
    if isinstance(target_streamers, dict) and "error" in target_streamers:
        print(f"구글 시트 에러: {target_streamers['error']}")
        exit()
        
    print(f">> 성공적으로 {len(target_streamers)}명의 대상 목록을 가져왔습니다.\n")

except Exception as e:
    print(f"구글 시트 목록 조회 중 에러 발생: {e}")
    exit()


# 씨나인 공홈 스폰 API 통신을 위한 세션 설정
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
})

payload = []

# [수정/추가 포인트 2] 가져온 실제 스트리머 목록을 순회하며 크롤링을 시작합니다.
for item in target_streamers:
    row_num = item["rowNum"]
    streamer_name = item["streamerName"]
    api_url = item["apiUrl"]
    
    print(f"[{streamer_name}] ({row_num}행) 씨나인 공홈 API 조회 중...")
    
    try:
        res = session.get(api_url, timeout=10)
        if res.status_code != 200:
            print(f" -> 실패 (HTTP 상태코드: {res.status_code})")
            continue
            
        json_data = res.json()
        data_array = json_data.get("data", [])
        
        if not isinstance(data_array, list):
            print(" -> 실패 (유효한 데이터 형식이 아닙니다.)")
            continue
            
        # 종족별 매칭 데이터 검색 (A: 전체, P: 프로토스, T: 테란, Z: 저그)
        data_A = next((x for x in data_array if x.get("opponentRace") == "A"), None)
        data_P = next((x for x in data_array if x.get("opponentRace") == "P"), None)
        data_T = next((x for x in data_array if x.get("opponentRace") == "T"), None)
        data_Z = next((x for x in data_array if x.get("opponentRace") == "Z"), None)
        
        stats_data = {
            "count": data_A.get("totalCount", 0) if data_A else 0,
            "win": data_A.get("wins", 0) if data_A else 0,
            "lose": data_A.get("losses", 0) if data_A else 0,
            "rate": data_A.get("winRate", 0) if data_A else 0,
            
            "pCount": data_P.get("totalCount", 0) if data_P else 0,
            "pRate": data_P.get("winRate", 0) if data_P else 0,
            
            "tCount": data_T.get("totalCount", 0) if data_T else 0,
            "tRate": data_T.get("winRate", 0) if data_T else 0,
            
            "zCount": data_Z.get("totalCount", 0) if data_Z else 0,
            "zRate": data_Z.get("winRate", 0) if data_Z else 0,
        }
        
        payload.append({
            "rowNum": row_num,  # GAS 단으로 보낼 고유 행 번호
            "stats": stats_data
        })
        print(f" -> 완료 (총 스폰수: {stats_data['count']}전)")
        
    except Exception as e:
        print(f" -> 크롤링 중 에러 발생: {e}")
        
    # IP 차단 및 과부하 방지를 위한 랜덤 딜레이 (1.5초 ~ 3.0초)
    time.sleep(random.uniform(1.5, 3.0))

if not payload:
    print("\n>> 업데이트할 스폰 데이터가 없습니다. 프로그램을 종료합니다.")
    exit()

# 최종 GAS 전송부 패킷 구조 정의
# "스타대학2" 시트에 반영하고 싶다면 action을 "updateSponStats2"로 주시면 됩니다.
final_data = {
    "action": "updateSponStats", 
    "payload": payload
}

print("\n>> 구글 시트 서버(doPost)로 데이터를 일괄 전송하여 반영하는 중...")
# 전송 실행
response = requests.post(GAS_WEBAPP_URL, json=final_data)
print(f"서버 결과 메시지: {response.text}")