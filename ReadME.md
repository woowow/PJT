docker-compose up --build 실행 시, 자동으로 현재 저장되어있는 json 파일로 DB 생성

### 기존에 이미 DB를 사용하고 있다면 "반드시" export_to_json.py 파일을 사용해서 json 파일로 만들고나서 새로 build해야함, 안그러면 data 날아감

<hr>

### 새로이 build 할거라면 아래 실행

docker-compose down -v
docker-compose up --build

<hr>

### 만약 새로운 json 파일을 받아서 현재 내 DB를 update하고 싶다면?

현재 내 db 데이터들을 export_to_json.py로 json형태로 만들고, 새로운 json 파일의 내용을 붙여넣기 한다.

이미 docker가 실행 중이라면?

merge_and_insert.py를 실행해서 적재한다.

